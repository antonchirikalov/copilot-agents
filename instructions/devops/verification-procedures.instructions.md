---
description: Post-deployment verification procedures, health checks, and deployment report generation for the DevOps agent.
---

# Verification Procedures

## Service Health Checks
Run these after terraform apply completes:

### 1. Application Load Balancer
```bash
ALB_DNS=$(terraform output -raw alb_dns_name)
curl -I http://$ALB_DNS/health
```
Expected: HTTP 200. If fails: wait 60s, retry up to 3 times.

### 2. Target Group
```bash
TG_ARN=$(terraform output -raw target_group_arn)
aws elbv2 describe-target-health --target-group-arn $TG_ARN --region $AWS_DEFAULT_REGION
```
Expected: All targets "healthy". If unhealthy: wait for health check grace period.

### 3. Auto Scaling Group
```bash
ASG_NAME=$(terraform output -raw asg_name)
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names $ASG_NAME --region $AWS_DEFAULT_REGION
```
Expected: DesiredCapacity = InService instances.

### 4. Lambda Function (if applicable)
```bash
LAMBDA_NAME=$(terraform output -raw lambda_function_name)
aws lambda invoke --function-name $LAMBDA_NAME --region $AWS_DEFAULT_REGION response.json
cat response.json
```
Expected: StatusCode 200, no errors.

### 5. CloudWatch Alarms
```bash
aws cloudwatch describe-alarms --region $AWS_DEFAULT_REGION
```
Expected: All alarms in OK state.

### 6. Endpoint Test
```bash
curl -X POST http://$ALB_DNS/[endpoint] -d '[test-data]'
```
Verify response time and content.

## If ANY Verification Fails
- Document the failure in deployment report
- Provide troubleshooting guidance from .github/skills/devops/references/troubleshooting.md
- Offer rollback: `terraform destroy`

## Deployment Report
Create: generated_docs_[TIMESTAMP]/Deployment_Report.md

Required sections:
1. Infrastructure Summary (resource counts by type)
2. Service Endpoints (ALB DNS, ARNs)
3. Verification Results table (Check | Status | Details)
4. Access Instructions (curl commands, monitoring commands)
5. Configuration Files locations
6. Next Steps (monitoring recommendations)

## AWS Resource Inventory
```bash
terraform output -json > generated_docs_[TIMESTAMP]/terraform_outputs.json
terraform state list > generated_docs_[TIMESTAMP]/terraform_resources.txt
```
