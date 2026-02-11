# Terraform for AWS Infrastructure

## Module Structure

Best practice: Separate modules for each AWS service category.

```
terraform/
├── main.tf              # Root module orchestration
├── variables.tf         # Global variables
├── outputs.tf          # Deployment outputs
├── terraform.tfvars    # Environment-specific values
├── backend.tf          # S3 state management
└── modules/
    ├── alb/            # Application Load Balancer
    ├── asg/            # Auto Scaling Group
    ├── lambda/         # Lambda functions
    └── monitoring/     # CloudWatch resources
```

## S3 Backend Configuration

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "curious-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "curious-terraform-locks"
    encrypt        = true
  }
}
```

**Setup backend resources:**
```bash
# Create S3 bucket
aws s3 mb s3://curious-terraform-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket curious-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB lock table
aws dynamodb create-table \
  --table-name curious-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## ALB Module Example

```hcl
# modules/alb/main.tf
resource "aws_lb" "main" {
  name               = "${var.project}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.enable_deletion_protection

  tags = {
    Name        = "${var.project}-alb"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "main" {
  name     = "${var.project}-tg"
  port     = var.target_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = var.health_check_path
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name = "${var.project}-tg"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

# modules/alb/outputs.tf
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.main.arn
}
```

## ASG Module Example

```hcl
# modules/asg/main.tf
resource "aws_launch_template" "main" {
  name_prefix   = "${var.project}-lt-"
  image_id      = var.ami_id
  instance_type = var.instance_type
  key_name      = var.key_name

  iam_instance_profile {
    name = aws_iam_instance_profile.main.name
  }

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.instances.id]
    delete_on_termination       = true
  }

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = var.root_volume_size
      volume_type           = "gp3"
      delete_on_termination = true
      encrypted             = true
    }
  }

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    region = var.aws_region
  }))

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "${var.project}-instance"
      Environment = var.environment
    }
  }
}

resource "aws_autoscaling_group" "main" {
  name                = "${var.project}-asg"
  vpc_zone_identifier = var.private_subnet_ids
  target_group_arns   = [var.target_group_arn]
  health_check_type   = "ELB"
  health_check_grace_period = var.health_check_grace_period

  min_size         = var.min_size
  max_size         = var.max_size
  desired_capacity = var.desired_capacity

  launch_template {
    id      = aws_launch_template.main.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.project}-asg"
    propagate_at_launch = true
  }
}

resource "aws_autoscaling_policy" "scale_up" {
  name                   = "${var.project}-scale-up"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = var.scale_up_cooldown
  autoscaling_group_name = aws_autoscaling_group.main.name
}

resource "aws_autoscaling_policy" "scale_down" {
  name                   = "${var.project}-scale-down"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = var.scale_down_cooldown
  autoscaling_group_name = aws_autoscaling_group.main.name
}
```

## Lambda Module Example

```hcl
# modules/lambda/main.tf
data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_lambda_function" "main" {
  filename         = data.archive_file.lambda.output_path
  function_name    = var.function_name
  role             = aws_iam_role.lambda.arn
  handler          = var.handler
  source_code_hash = data.archive_file.lambda.output_base64sha256
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory_size

  environment {
    variables = var.environment_variables
  }

  tags = {
    Name        = var.function_name
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "${var.function_name}-schedule"
  description         = "Trigger ${var.function_name} on schedule"
  schedule_expression = var.schedule_expression

  tags = {
    Name = "${var.function_name}-schedule"
  }
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "lambda"
  arn       = aws_lambda_function.main.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.function_name}-logs"
  }
}
```

## Variables Pattern

```hcl
# variables.tf
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project" {
  description = "Project name for resource naming"
  type        = string
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
```

## Outputs Pattern

```hcl
# outputs.tf
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "asg_name" {
  description = "Name of the Auto Scaling Group"
  value       = module.asg.asg_name
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.lambda.function_name
}

output "endpoint" {
  description = "Full service endpoint"
  value       = "http://${module.alb.alb_dns_name}"
}
```

## Terraform Workflow

```bash
# Initialize (first time or after adding modules)
terraform init

# Format code
terraform fmt -recursive

# Validate configuration
terraform validate

# Plan changes
terraform plan -out=tfplan

# Review plan output before applying
terraform show tfplan

# Apply changes
terraform apply tfplan

# View outputs
terraform output

# Destroy infrastructure
terraform destroy
```

## State Management

```bash
# List resources in state
terraform state list

# Show specific resource
terraform state show aws_lb.main

# Remove resource from state (if manually deleted)
terraform state rm aws_lb.main

# Import existing resource
terraform import aws_lb.main <alb-arn>

# Refresh state
terraform refresh
```

## Best Practices

1. **Use modules** for reusable components
2. **Store state remotely** in S3 with locking
3. **Use variables** for all environment-specific values
4. **Tag all resources** for cost tracking
5. **Enable versioning** on state bucket
6. **Use workspaces** for multiple environments
7. **Validate before apply** with terraform plan
8. **Document outputs** for downstream usage
9. **Use data sources** for existing resources
10. **Implement lifecycle rules** for critical resources

## Common Patterns

### Data Source for Existing VPC
```hcl
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}
```

### Conditional Resources
```hcl
resource "aws_lb_listener" "https" {
  count = var.enable_https ? 1 : 0
  
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  certificate_arn   = var.certificate_arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}
```

### Dynamic Blocks
```hcl
resource "aws_security_group" "alb" {
  name   = "${var.project}-alb-sg"
  vpc_id = var.vpc_id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
```
