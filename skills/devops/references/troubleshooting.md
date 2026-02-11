# AWS Troubleshooting Guide

## Common Terraform Errors

### Error: Error acquiring the state lock

**Cause**: Another terraform process is running or previous run didn't release lock

**Solution**:
```bash
# Check DynamoDB lock table
aws dynamodb scan --table-name curious-terraform-locks

# Force unlock (use with caution)
terraform force-unlock <lock-id>

# If lock is stale, delete from DynamoDB
aws dynamodb delete-item \
  --table-name curious-terraform-locks \
  --key '{"LockID":{"S":"<lock-id>"}}'
```

### Error: ValidationError: Minimum capacity of 1 required

**Cause**: ASG min_size cannot be less than 1

**Solution**:
```hcl
# In terraform
variable "asg_min_size" {
  default = 1
  validation {
    condition     = var.asg_min_size >= 1
    error_message = "Min size must be at least 1"
  }
}
```

### Error: InvalidAMIID.NotFound

**Cause**: AMI doesn't exist in target region or not accessible

**Solution**:
```bash
# Verify AMI exists
aws ec2 describe-images \
  --region $AWS_DEFAULT_REGION \
  --image-ids ami-0665b842451e64959

# If AMI is in different region, copy it
aws ec2 copy-image \
  --source-region us-east-1 \
  --source-image-id ami-0665b842451e64959 \
  --region eu-north-1 \
  --name "copied-ami"
```

## EC2 and ASG Issues

### InsufficientInstanceCapacity

**Symptom**: Instances not launching, ASG stuck at desired capacity

**Cause**: No available GPU instances (g5.xlarge, g4dn.xlarge) in AZ

**Solutions**:
```bash
# 1. Check current capacity
aws ec2 describe-instance-type-offerings \
  --location-type availability-zone \
  --filters Name=instance-type,Values=g5.xlarge \
  --region $AWS_DEFAULT_REGION

# 2. Try different AZ
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name my-asg \
  --vpc-zone-identifier subnet-xxx,subnet-yyy

# 3. Request capacity reservation
aws ec2 create-capacity-reservation \
  --instance-type g5.xlarge \
  --instance-platform Linux/UNIX \
  --availability-zone us-east-1a \
  --instance-count 5

# 4. Use different instance type temporarily
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name my-asg \
  --launch-template LaunchTemplateId=lt-xxx,Version=2  # version with g4dn.xlarge
```

### VcpuLimitExceeded

**Symptom**: Cannot launch instances, "You have requested more vCPU capacity than your current limit"

**Cause**: Account vCPU limit reached (g5.xlarge = 4 vCPUs, g4dn.xlarge = 4 vCPUs)

**Solution**:
```bash
# 1. Check current limits
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-1216C47A  # Running On-Demand G instances

# 2. Request limit increase
aws service-quotas request-service-quota-increase \
  --service-code ec2 \
  --quota-code L-1216C47A \
  --desired-value 64  # Request 64 vCPUs (16 g5.xlarge instances)

# 3. Check request status
aws service-quotas list-requested-service-quota-change-history-by-quota \
  --service-code ec2 \
  --quota-code L-1216C47A
```

### Instances Launching but Immediately Terminating

**Symptom**: ASG launches instances that terminate within 2-3 minutes

**Cause**: User data script failure or health check failure

**Debug**:
```bash
# 1. Get terminated instance ID
INSTANCE_ID=$(aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name my-asg \
  --max-records 5 \
  --query 'Activities[?StatusCode==`Failed`].Description' \
  --output text | grep -oP 'i-\w+')

# 2. Check CloudWatch Logs (if configured)
aws logs tail /var/log/cloud-init-output.log --follow

# 3. Check instance system log
aws ec2 get-console-output --instance-id $INSTANCE_ID

# 4. Launch instance manually with same launch template to debug
aws ec2 run-instances \
  --launch-template LaunchTemplateId=lt-xxx,Version='$Latest' \
  --subnet-id subnet-xxx

# SSH to instance and check
ssh -i my-key.pem ec2-user@<instance-ip>
sudo journalctl -u cloud-final -f
```

## ALB and Target Group Issues

### Target.FailedHealthChecks

**Symptom**: Instances registered but marked unhealthy, ALB returns 503

**Cause**: Service not responding on health check port or wrong health check path

**Debug**:
```bash
# 1. Check target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State,TargetHealth.Reason]' \
  --output table

# 2. SSH to instance and test locally
ssh -i my-key.pem ec2-user@<instance-ip>
curl -v http://localhost:8000/health

# 3. Check security group allows ALB -> instance
aws ec2 describe-security-groups --group-ids sg-xxx

# 4. Check service is running
systemctl status my-service

# 5. Update health check settings
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:... \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 10 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3
```

### Target.ResponseCodeMismatch

**Symptom**: Health check path returns non-200 status code

**Solution**:
```bash
# 1. Check what status code is returned
ssh -i my-key.pem ec2-user@<instance-ip>
curl -I http://localhost:8000/health

# 2. Update matcher to accept 200-299
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:... \
  --matcher HttpCode=200-299

# 3. Fix application to return 200
# Check application logs for errors
```

### Target.Timeout

**Symptom**: Health checks timing out after 5-10 seconds

**Cause**: Application slow to respond or model loading not complete

**Solution**:
```bash
# 1. Increase health check timeout
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:... \
  --health-check-timeout-seconds 15

# 2. Increase health check grace period
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name my-asg \
  --health-check-grace-period 600  # 10 minutes

# 3. Optimize application startup
# - Preload models during AMI baking
# - Use lazy loading for large models
# - Add warmup endpoint
```

### ResourceInUse: Target group is currently in use by a listener

**Symptom**: Cannot modify target group port, protocol, or delete target group

**Cause**: Target group attached to ALB listener

**Solution**:
```bash
# 1. Find listener using target group
aws elbv2 describe-listeners \
  --load-balancer-arn arn:aws:... \
  --query 'Listeners[?DefaultActions[?TargetGroupArn==`arn:aws:...`]]'

# 2. Delete listener rule or modify listener
aws elbv2 delete-listener --listener-arn arn:aws:...

# 3. Recreate target group with correct settings
# 4. Reattach to listener
```

## Lambda Issues

### ThrottlingException: Rate exceeded

**Symptom**: Lambda function throttled, EventBridge invocations failing

**Cause**: Too many concurrent invocations or API rate limits

**Solution**:
```bash
# 1. Check Lambda concurrency
aws lambda get-function-concurrency \
  --function-name my-function

# 2. Increase reserved concurrency
aws lambda put-function-concurrency \
  --function-name my-function \
  --reserved-concurrent-executions 10

# 3. Reduce EventBridge frequency
aws events put-rule \
  --name my-schedule \
  --schedule-expression "rate(2 minutes)"  # Was 1 minute

# 4. Implement exponential backoff in Lambda code
import time
import random

def lambda_handler(event, context):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # AWS API call
            response = client.describe_auto_scaling_groups(...)
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'Throttling':
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
                else:
                    raise
```

### AccessDeniedException

**Symptom**: Lambda cannot access AWS resources (CloudWatch, ALB, ASG)

**Cause**: IAM role missing permissions

**Solution**:
```bash
# 1. Check Lambda role
ROLE_NAME=$(aws lambda get-function \
  --function-name my-function \
  --query 'Configuration.Role' \
  --output text | cut -d'/' -f2)

# 2. List attached policies
aws iam list-attached-role-policies --role-name $ROLE_NAME

# 3. Add required policy
aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess

# 4. Or create inline policy
aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name alb-modify \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:ModifyListener",
        "elasticloadbalancing:ModifyRule"
      ],
      "Resource": "*"
    }]
  }'
```

## Region Issues

### Resource Not Found

**Symptom**: AWS CLI commands return "not found" but resource exists in console

**Cause**: Wrong region - resource in different region than CLI default

**Solution**:
```bash
# 1. Check current region
aws configure get region

# 2. List resources in all regions
for region in us-east-1 eu-north-1 eu-west-1; do
  echo "Checking $region..."
  aws autoscaling describe-auto-scaling-groups \
    --region $region \
    --query 'AutoScalingGroups[*].AutoScalingGroupName'
done

# 3. Set correct region
export AWS_DEFAULT_REGION=us-east-1

# 4. Always specify --region flag
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names my-asg \
  --region us-east-1
```

## Terraform Destroy Issues

### Timeout waiting for ASG to drain

**Symptom**: `terraform destroy` hangs for 10+ minutes waiting for ASG

**Cause**: Instances continuously recreated due to health check failures

**Solution**:
```bash
# 1. Force delete ASG via AWS CLI
aws autoscaling delete-auto-scaling-group \
  --auto-scaling-group-name my-asg \
  --force-delete \
  --region $AWS_DEFAULT_REGION

# 2. Remove from Terraform state
terraform state rm module.asg.aws_autoscaling_group.main

# 3. Continue destroy
terraform destroy
```

### DependencyViolation: resource has dependent objects

**Symptom**: Cannot delete VPC, security group, or target group

**Solution**:
```bash
# 1. Identify dependencies
aws ec2 describe-network-interfaces \
  --filters "Name=group-id,Values=sg-xxx"

# 2. Delete dependent resources first
aws ec2 terminate-instances --instance-ids i-xxx
aws elbv2 delete-load-balancer --load-balancer-arn arn:aws:...

# 3. Wait for resources to delete
aws ec2 wait instance-terminated --instance-ids i-xxx

# 4. Retry deletion
terraform destroy -target=aws_security_group.main
```

## Cost Issues

### Unexpected High Costs

**Symptom**: AWS bill higher than expected

**Debug**:
```bash
# 1. Check running instances
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,LaunchTime]' \
  --output table

# 2. Check ASG desired capacity
aws autoscaling describe-auto-scaling-groups \
  --query 'AutoScalingGroups[*].[AutoScalingGroupName,DesiredCapacity]'

# 3. Check scaling activities (if stuck at high capacity)
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name my-asg \
  --max-records 50

# 4. Force scale down
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name my-asg \
  --desired-capacity 1

# 5. Check for zombie resources
# - Load balancers without target groups
# - Detached EBS volumes
# - Elastic IPs
aws ec2 describe-addresses --filters "Name=association-id,Values=''"
aws ec2 describe-volumes --filters "Name=status,Values=available"
```

## Monitoring and Debugging

### Enable Detailed Logging

```bash
# CloudWatch Logs for Lambda
aws logs create-log-group --log-group-name /aws/lambda/my-function
aws logs put-retention-policy \
  --log-group-name /aws/lambda/my-function \
  --retention-in-days 14

# CloudWatch Agent on EC2 (via user data)
yum install -y amazon-cloudwatch-agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json <<EOF
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [{
          "file_path": "/var/log/myapp.log",
          "log_group_name": "/aws/ec2/myapp",
          "log_stream_name": "{instance_id}"
        }]
      }
    }
  }
}
EOF
systemctl start amazon-cloudwatch-agent

# ALB Access Logs
aws elbv2 modify-load-balancer-attributes \
  --load-balancer-arn arn:aws:... \
  --attributes Key=access_logs.s3.enabled,Value=true \
              Key=access_logs.s3.bucket,Value=my-alb-logs-bucket
```

### Quick Health Check Script

```bash
#!/bin/bash
# health_check.sh - Quick infrastructure health check

set -euo pipefail

ASG_NAME="my-asg"
ALB_ARN="arn:aws:elasticloadbalancing:..."
TG_ARN="arn:aws:elasticloadbalancing:..."

echo "=== ASG Status ==="
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names $ASG_NAME \
  --query 'AutoScalingGroups[0].[DesiredCapacity,Instances[*].[InstanceId,HealthStatus]]' \
  --output table

echo -e "\n=== Target Health ==="
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' \
  --output table

echo -e "\n=== ALB Status ==="
aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].State.Code' \
  --output text

echo -e "\n=== Recent Scaling Activities ==="
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name $ASG_NAME \
  --max-records 5 \
  --query 'Activities[*].[StartTime,StatusCode,Description]' \
  --output table
```
