# AWS Services Reference

## Application Load Balancer (ALB)

### Create ALB with Target Groups

```bash
# Get VPC and subnets
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text)
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text)

# Create security group
SG_ID=$(aws ec2 create-security-group \
  --group-name my-alb-sg \
  --description "Security group for ALB" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

# Allow HTTP
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Create ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name my-alb \
  --subnets $SUBNET_IDS \
  --security-groups $SG_ID \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

# Create target group
TG_ARN=$(aws elbv2 create-target-group \
  --name my-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id $VPC_ID \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

### Weighted Routing (Multiple Target Groups)

```bash
# Create second target group (cloud proxy)
TG_CLOUD_ARN=$(aws elbv2 create-target-group \
  --name my-cloud-targets \
  --protocol HTTP \
  --port 8080 \
  --vpc-id $VPC_ID \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# Create listener with weighted routing
LISTENER_ARN=$(aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,ForwardConfig="{
    \"TargetGroups\": [
      {\"TargetGroupArn\": \"$TG_ARN\", \"Weight\": 100},
      {\"TargetGroupArn\": \"$TG_CLOUD_ARN\", \"Weight\": 0}
    ]
  }" \
  --query 'Listeners[0].ListenerArn' \
  --output text)

# Update weights dynamically
aws elbv2 modify-listener \
  --listener-arn $LISTENER_ARN \
  --default-actions Type=forward,ForwardConfig="{
    \"TargetGroups\": [
      {\"TargetGroupArn\": \"$TG_ARN\", \"Weight\": 70},
      {\"TargetGroupArn\": \"$TG_CLOUD_ARN\", \"Weight\": 30}
    ]
  }"
```

### Check Target Health

```bash
# Describe target health
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State,TargetHealth.Reason]' \
  --output table
```

## Auto Scaling Group (ASG)

### Create Launch Template

```bash
# Create launch template
LT_ID=$(aws ec2 create-launch-template \
  --launch-template-name my-template \
  --version-description v1 \
  --launch-template-data "{
    \"ImageId\": \"ami-0665b842451e64959\",
    \"InstanceType\": \"g5.xlarge\",
    \"KeyName\": \"my-key\",
    \"SecurityGroupIds\": [\"$SG_INSTANCES_ID\"],
    \"IamInstanceProfile\": {\"Name\": \"my-instance-profile\"},
    \"TagSpecifications\": [{
      \"ResourceType\": \"instance\",
      \"Tags\": [{\"Key\": \"Name\", \"Value\": \"my-instance\"}]
    }]
  }" \
  --query 'LaunchTemplate.LaunchTemplateId' \
  --output text)

# Create ASG
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name my-asg \
  --launch-template LaunchTemplateId=$LT_ID,Version='$Latest' \
  --min-size 1 \
  --max-size 10 \
  --desired-capacity 1 \
  --vpc-zone-identifier "$PRIVATE_SUBNET_IDS" \
  --target-group-arns $TG_ARN \
  --health-check-type ELB \
  --health-check-grace-period 300 \
  --tags "Key=Name,Value=my-asg,PropagateAtLaunch=true"
```

### Scaling Policies

```bash
# Target tracking policy (based on latency)
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name my-asg \
  --policy-name target-tracking-latency \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration "{
    \"PredefinedMetricSpecification\": {
      \"PredefinedMetricType\": \"ALBRequestCountPerTarget\",
      \"ResourceLabel\": \"$ALB_RESOURCE_LABEL\"
    },
    \"TargetValue\": 1000.0
  }"

# Step scaling policy
POLICY_ARN=$(aws autoscaling put-scaling-policy \
  --auto-scaling-group-name my-asg \
  --policy-name step-scale-up \
  --policy-type StepScaling \
  --adjustment-type ChangeInCapacity \
  --metric-aggregation-type Average \
  --step-adjustments "[
    {\"MetricIntervalLowerBound\": 0, \"MetricIntervalUpperBound\": 10, \"ScalingAdjustment\": 1},
    {\"MetricIntervalLowerBound\": 10, \"ScalingAdjustment\": 2}
  ]" \
  --query 'PolicyARN' \
  --output text)
```

### Manual Scaling

```bash
# Set desired capacity
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name my-asg \
  --desired-capacity 5

# Update min/max capacity
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name my-asg \
  --min-size 2 \
  --max-size 15

# Suspend/resume processes
aws autoscaling suspend-processes \
  --auto-scaling-group-name my-asg \
  --scaling-processes Launch Terminate

aws autoscaling resume-processes \
  --auto-scaling-group-name my-asg
```

### Monitor ASG

```bash
# Describe ASG
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names my-asg \
  --query 'AutoScalingGroups[0].[DesiredCapacity,MinSize,MaxSize,Instances[*].[InstanceId,HealthStatus,LifecycleState]]' \
  --output table

# View scaling activities
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name my-asg \
  --max-records 20 \
  --query 'Activities[*].[StartTime,StatusCode,Description]' \
  --output table
```

## Lambda Functions

### Create Lambda with EventBridge Trigger

```bash
# Create IAM role
ROLE_ARN=$(aws iam create-role \
  --role-name my-lambda-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --query 'Role.Arn' \
  --output text)

# Attach policies
aws iam attach-role-policy \
  --role-name my-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create Lambda function
LAMBDA_ARN=$(aws lambda create-function \
  --function-name my-function \
  --runtime python3.11 \
  --role $ROLE_ARN \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment "Variables={KEY1=value1,KEY2=value2}" \
  --query 'FunctionArn' \
  --output text)

# Create EventBridge rule
RULE_ARN=$(aws events put-rule \
  --name my-schedule \
  --schedule-expression "rate(1 minute)" \
  --state ENABLED \
  --query 'RuleArn' \
  --output text)

# Add Lambda as target
aws events put-targets \
  --rule my-schedule \
  --targets "Id=1,Arn=$LAMBDA_ARN"

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission \
  --function-name my-function \
  --statement-id AllowEventBridge \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn $RULE_ARN
```

### Invoke and Monitor Lambda

```bash
# Invoke function
aws lambda invoke \
  --function-name my-function \
  --payload '{"key":"value"}' \
  response.json

cat response.json

# View logs
aws logs tail /aws/lambda/my-function --follow

# Get metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=my-function \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## CloudWatch Monitoring

### Create Alarms

```bash
# ALB latency alarm
aws cloudwatch put-metric-alarm \
  --alarm-name high-latency \
  --alarm-description "Trigger when latency > 3s" \
  --metric-name TargetResponseTime \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 60 \
  --evaluation-periods 2 \
  --threshold 3.0 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=LoadBalancer,Value=$ALB_RESOURCE_LABEL \
  --alarm-actions $POLICY_ARN

# ASG unhealthy instances alarm
aws cloudwatch put-metric-alarm \
  --alarm-name unhealthy-targets \
  --metric-name UnHealthyHostCount \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 60 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=TargetGroup,Value=$TG_RESOURCE_LABEL
```

### Query Metrics

```bash
# Get ALB latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=$ALB_RESOURCE_LABEL \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --output table

# Get ASG metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=my-asg \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

## Secrets Manager

### Store and Retrieve Secrets

```bash
# Create secret
aws secretsmanager create-secret \
  --name my-api-key \
  --description "API key for external service" \
  --secret-string "72eec40c2f7c489c8d621f6dc1bfa039" \
  --region $AWS_DEFAULT_REGION

# Retrieve secret
aws secretsmanager get-secret-value \
  --secret-id my-api-key \
  --query SecretString \
  --output text

# Update secret
aws secretsmanager update-secret \
  --secret-id my-api-key \
  --secret-string "new-api-key-value"

# Delete secret (with recovery window)
aws secretsmanager delete-secret \
  --secret-id my-api-key \
  --recovery-window-in-days 30
```

## IAM Roles and Policies

### Create Instance Profile for EC2

```bash
# Create role
aws iam create-role \
  --role-name my-instance-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Create inline policy for CloudWatch
aws iam put-role-policy \
  --role-name my-instance-role \
  --policy-name cloudwatch-metrics \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["cloudwatch:PutMetricData"],
      "Resource": "*"
    }]
  }'

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name my-instance-profile

# Add role to instance profile
aws iam add-role-to-instance-profile \
  --instance-profile-name my-instance-profile \
  --role-name my-instance-role
```

## VPC and Security Groups

### Create Security Group

```bash
# Create security group for instances
SG_INSTANCES_ID=$(aws ec2 create-security-group \
  --group-name my-instances-sg \
  --description "Security group for instances" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

# Allow traffic from ALB only
aws ec2 authorize-security-group-ingress \
  --group-id $SG_INSTANCES_ID \
  --protocol tcp \
  --port 8000 \
  --source-group $SG_ALB_ID

# Allow outbound HTTPS (for Secrets Manager, etc.)
aws ec2 authorize-security-group-egress \
  --group-id $SG_INSTANCES_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

## Common AWS CLI Patterns

### Query and Filter

```bash
# Find default VPC
aws ec2 describe-vpcs \
  --filters "Name=is-default,Values=true" \
  --query "Vpcs[0].VpcId" \
  --output text

# List running instances
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query "Reservations[*].Instances[*].[InstanceId,InstanceType,PrivateIpAddress]" \
  --output table

# Get latest AMI
aws ec2 describe-images \
  --owners self \
  --filters "Name=name,Values=my-ami-*" \
  --query "sort_by(Images, &CreationDate)[-1].ImageId" \
  --output text
```

### Resource Tagging

```bash
# Tag resources
aws ec2 create-tags \
  --resources i-1234567890abcdef0 \
  --tags Key=Environment,Value=production Key=Project,Value=curious

# Find resources by tag
aws ec2 describe-instances \
  --filters "Name=tag:Environment,Values=production" \
  --query "Reservations[*].Instances[*].InstanceId"
```
