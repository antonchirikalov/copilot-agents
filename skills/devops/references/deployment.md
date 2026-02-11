# AWS Deployment Workflows

## Standard Deployment Process

### Step-by-Step Deployment

```bash
# 1. Configure environment
source .github/skills/devops/.aws_credentials

# Verify credentials and region
aws sts get-caller-identity
echo "Region: $AWS_DEFAULT_REGION"

# 2. Review project design
cat Solution_Design_Document.md

# 3. Navigate to terraform directory
cd terraform/

# 4. Initialize Terraform (first time or after adding modules)
terraform init

# 5. Format and validate
terraform fmt -recursive
terraform validate

# 6. Review configuration
cat terraform.tfvars

# 7. Generate plan
terraform plan -out=tfplan

# 8. Review plan output carefully
terraform show tfplan | less

# 9. Apply infrastructure (requires user confirmation)
terraform apply tfplan

# 10. Capture outputs
terraform output > ../deployment_outputs.txt
terraform output -json > ../deployment_outputs.json

# 11. Test endpoints
ALB_DNS=$(terraform output -raw alb_dns_name)
curl -v http://$ALB_DNS/health
```

### Post-Deployment Verification

```bash
# 1. Check ALB status
aws elbv2 describe-load-balancers \
  --names $(terraform output -raw alb_name) \
  --region $AWS_DEFAULT_REGION \
  --query 'LoadBalancers[0].State'

# 2. Check target health
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw target_group_arn) \
  --region $AWS_DEFAULT_REGION \
  --output table

# 3. Check ASG status
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names $(terraform output -raw asg_name) \
  --region $AWS_DEFAULT_REGION \
  --query 'AutoScalingGroups[0].[DesiredCapacity,MinSize,MaxSize,Instances[*].[InstanceId,HealthStatus]]' \
  --output table

# 4. Check Lambda function
aws lambda get-function \
  --function-name $(terraform output -raw lambda_function_name) \
  --region $AWS_DEFAULT_REGION

# 5. Test Lambda invocation
aws lambda invoke \
  --function-name $(terraform output -raw lambda_function_name) \
  --region $AWS_DEFAULT_REGION \
  response.json && cat response.json

# 6. Monitor logs
aws logs tail /aws/lambda/$(terraform output -raw lambda_function_name) \
  --follow \
  --region $AWS_DEFAULT_REGION
```

## Monitoring Deployment Progress

### Real-time Monitoring

```bash
# Terminal 1: Watch ASG
watch -n 10 '
echo "=== ASG Status ==="
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names $(terraform output -raw asg_name) \
  --region $AWS_DEFAULT_REGION \
  --query "AutoScalingGroups[0].[DesiredCapacity,Instances[*].[InstanceId,HealthStatus,LifecycleState]]" \
  --output table

echo -e "\n=== Target Health ==="
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw target_group_arn) \
  --region $AWS_DEFAULT_REGION \
  --output table
'

# Terminal 2: Watch Lambda logs
aws logs tail /aws/lambda/$(terraform output -raw lambda_function_name) \
  --follow \
  --region $AWS_DEFAULT_REGION

# Terminal 3: Watch scaling activities
watch -n 30 '
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name $(terraform output -raw asg_name) \
  --max-records 10 \
  --region $AWS_DEFAULT_REGION \
  --output table
'
```

## Update Deployment

### Infrastructure Updates

```bash
# 1. Pull latest changes
git pull origin main

# 2. Review changes
cd terraform/
terraform plan

# 3. Apply targeted update (specific module)
terraform apply -target=module.lambda

# 4. Apply all changes
terraform apply

# 5. Verify no drift
terraform plan
# Expected: "No changes. Your infrastructure matches the configuration."
```

### AMI Updates (Rolling Update)

```bash
# 1. Update AMI in terraform.tfvars
vim terraform.tfvars
# Change: ami_id = "ami-new-version"

# 2. Apply to create new launch template version
terraform apply -target=module.asg.aws_launch_template.main

# 3. Trigger instance refresh for gradual rollout
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name $(terraform output -raw asg_name) \
  --region $AWS_DEFAULT_REGION \
  --preferences '{
    "MinHealthyPercentage": 50,
    "InstanceWarmup": 300,
    "CheckpointPercentages": [50, 100]
  }'

# 4. Monitor refresh progress
watch -n 30 '
aws autoscaling describe-instance-refreshes \
  --auto-scaling-group-name $(terraform output -raw asg_name) \
  --region $AWS_DEFAULT_REGION \
  --query "InstanceRefreshes[0].[Status,PercentageComplete,InstancesToUpdate]" \
  --output table
'

# 5. Cancel refresh if needed
aws autoscaling cancel-instance-refresh \
  --auto-scaling-group-name $(terraform output -raw asg_name) \
  --region $AWS_DEFAULT_REGION
```

### Configuration Changes

```bash
# 1. Update terraform.tfvars
vim terraform.tfvars
# Example: asg_max_size = 15 (was 10)

# 2. Plan changes
terraform plan

# 3. Apply
terraform apply

# 4. Verify ASG updated
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names $(terraform output -raw asg_name) \
  --region $AWS_DEFAULT_REGION \
  --query 'AutoScalingGroups[0].[MinSize,MaxSize,DesiredCapacity]'
```

## Rollback Procedures

### Emergency Rollback (Complete Destruction)

```bash
# 1. Backup current state
cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)

# 2. Destroy all resources
terraform destroy

# 3. Confirm destruction
# Type: yes

# 4. Verify cleanup
aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=curious" \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name]'

# 5. Manual cleanup if needed
# - Delete stuck security groups
# - Delete detached EBS volumes
# - Delete orphaned ENIs
```

### Partial Rollback (Preserve Infrastructure)

```bash
# 1. Suspend auto-scaling processes
aws autoscaling suspend-processes \
  --auto-scaling-group-name $(terraform output -raw asg_name) \
  --scaling-processes Launch Terminate HealthCheck ReplaceUnhealthy AlarmNotification ScheduledActions \
  --region $AWS_DEFAULT_REGION

# 2. Disable EventBridge rule (stop Lambda triggers)
RULE_NAME=$(terraform output -raw eventbridge_rule_name)
aws events disable-rule \
  --name $RULE_NAME \
  --region $AWS_DEFAULT_REGION

# 3. Disable CloudWatch alarms
aws cloudwatch disable-alarm-actions \
  --alarm-names curious-high-latency \
  --region $AWS_DEFAULT_REGION

# 4. Scale down to minimum
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name $(terraform output -raw asg_name) \
  --desired-capacity 1 \
  --region $AWS_DEFAULT_REGION

# To resume:
aws autoscaling resume-processes \
  --auto-scaling-group-name $(terraform output -raw asg_name) \
  --region $AWS_DEFAULT_REGION

aws events enable-rule --name $RULE_NAME --region $AWS_DEFAULT_REGION
aws cloudwatch enable-alarm-actions --alarm-names curious-high-latency --region $AWS_DEFAULT_REGION
```

### Rollback to Previous AMI

```bash
# 1. Identify previous AMI version
aws ec2 describe-images \
  --owners self \
  --filters "Name=name,Values=curious-*" \
  --query 'sort_by(Images, &CreationDate)[*].[ImageId,Name,CreationDate]' \
  --output table

# 2. Update terraform.tfvars with previous AMI
vim terraform.tfvars
# Change: ami_id = "ami-previous-version"

# 3. Apply changes
terraform apply -target=module.asg.aws_launch_template.main

# 4. Trigger instance refresh
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name $(terraform output -raw asg_name) \
  --region $AWS_DEFAULT_REGION
```

## Testing Workflows

### Functional Testing

```bash
# 1. Health check test
ALB_DNS=$(terraform output -raw alb_dns_name)
curl -f http://$ALB_DNS/health || echo "Health check failed!"

# 2. Service endpoint test
curl -X POST http://$ALB_DNS/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Test synthesis", "voice": "default"}' \
  --output test_output.wav

# Verify output
file test_output.wav
# Expected: RIFF (little-endian) data, WAVE audio

# 3. Latency test
time curl -X POST http://$ALB_DNS/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Latency test", "voice": "default"}' \
  --output /dev/null -s

# Expected: real time < 2.0s
```

### Load Testing

```bash
# Simulate concurrent requests
for i in {1..20}; do
  curl -X POST http://$ALB_DNS/v1/tts \
    -H "Content-Type: application/json" \
    -d '{"text": "Load test request '$i'", "voice": "default"}' \
    --output /dev/null -s &
done
wait

# Monitor scaling response
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name $(terraform output -raw asg_name) \
  --max-records 20 \
  --region $AWS_DEFAULT_REGION \
  --output table

# Check if new instances launched
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names $(terraform output -raw asg_name) \
  --region $AWS_DEFAULT_REGION \
  --query 'AutoScalingGroups[0].DesiredCapacity'
```

### Scaling Policy Testing

```bash
# 1. Manually trigger scale-up alarm
aws cloudwatch set-alarm-state \
  --alarm-name curious-high-latency \
  --state-value ALARM \
  --state-reason "Manual test" \
  --region $AWS_DEFAULT_REGION

# 2. Wait and verify scale-up
sleep 60
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names $(terraform output -raw asg_name) \
  --region $AWS_DEFAULT_REGION \
  --query 'AutoScalingGroups[0].DesiredCapacity'

# 3. Reset alarm
aws cloudwatch set-alarm-state \
  --alarm-name curious-high-latency \
  --state-value OK \
  --state-reason "Test complete" \
  --region $AWS_DEFAULT_REGION
```

## Multi-Environment Deployment

### Using Terraform Workspaces

```bash
# 1. Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# 2. List workspaces
terraform workspace list

# 3. Switch workspace
terraform workspace select dev

# 4. Deploy to dev
terraform apply -var-file="environments/dev.tfvars"

# 5. Deploy to prod
terraform workspace select prod
terraform apply -var-file="environments/prod.tfvars"
```

### Environment-Specific Variables

```hcl
# environments/dev.tfvars
environment = "dev"
asg_min_size = 1
asg_max_size = 3
instance_type = "g4dn.xlarge"
enable_deletion_protection = false

# environments/prod.tfvars
environment = "prod"
asg_min_size = 2
asg_max_size = 10
instance_type = "g5.xlarge"
enable_deletion_protection = true
```

## Operational Runbooks

### Daily Health Check

```bash
#!/bin/bash
# daily_health_check.sh

source .github/skills/devops/.aws_credentials
cd terraform/

echo "=== $(date) ===" | tee -a health_check.log

# Check ALB
ALB_DNS=$(terraform output -raw alb_dns_name)
if curl -sf http://$ALB_DNS/health > /dev/null; then
  echo "✓ ALB health check passed" | tee -a health_check.log
else
  echo "✗ ALB health check FAILED" | tee -a health_check.log
fi

# Check ASG capacity
ASG_CAPACITY=$(aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names $(terraform output -raw asg_name) \
  --region $AWS_DEFAULT_REGION \
  --query 'AutoScalingGroups[0].DesiredCapacity' \
  --output text)
echo "ASG Desired Capacity: $ASG_CAPACITY" | tee -a health_check.log

# Check target health
HEALTHY_TARGETS=$(aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw target_group_arn) \
  --region $AWS_DEFAULT_REGION \
  --query 'length(TargetHealthDescriptions[?TargetHealth.State==`healthy`])' \
  --output text)
echo "Healthy Targets: $HEALTHY_TARGETS" | tee -a health_check.log

echo "==========================================\n" | tee -a health_check.log
```

### Weekly Cost Report

```bash
#!/bin/bash
# weekly_cost_report.sh

echo "=== Weekly Cost Report $(date) ==="

# Running instances
echo -e "\n### Running Instances ###"
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,LaunchTime]' \
  --region $AWS_DEFAULT_REGION \
  --output table

# Load balancers
echo -e "\n### Load Balancers ###"
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[*].[LoadBalancerName,CreatedTime]' \
  --region $AWS_DEFAULT_REGION \
  --output table

# Lambda invocations (last 7 days)
echo -e "\n### Lambda Invocations ###"
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=$(terraform output -raw lambda_function_name) \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 604800 \
  --statistics Sum \
  --region $AWS_DEFAULT_REGION
```
