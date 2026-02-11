---
description: Terraform code generation, Critic review cycle, and deployment workflow for the DevOps agent.
---

# Terraform Workflow

## Step 0: Load Required References
Before generating Terraform, identify and load reference documentation from .github/skills/devops/references/:
- IF Image Builder needed → Load: image-builder.md
- IF ALB + ASG → Load: aws-services.md
- IF Lambda → Load: aws-services.md
- ALWAYS load: terraform-aws.md
- IF issues expected → Load: troubleshooting.md

## Step 1: Verify Prerequisites
```bash
source .github/skills/devops/.aws_credentials  # or configured credential source
aws sts get-caller-identity          # verify AWS access
echo $AWS_DEFAULT_REGION             # verify region
terraform version                    # verify Terraform v1.0+
```
If ANY prerequisite fails → STOP → report error to user.

## Step 2: Read Input
1. Read Solution_Design_Document.md from generated_docs_[TIMESTAMP]/
2. Extract: VPC, compute, load balancing, serverless, monitoring, security, Image Builder requirements
3. Read user deployment prompt for: overrides, environment values, testing requirements

## Step 3: Generate Terraform
Create production-ready IaC in: generated_docs_[TIMESTAMP]/terraform/

Required files:
- main.tf (or modular: modules/alb/, modules/asg/, etc.)
- variables.tf
- outputs.tf
- terraform.tfvars
- backend.tf (S3 backend commented out by default)

Best practices:
- Variables for all configurable values
- Tag all resources (project, environment, managed-by)
- Enable EBS encryption
- IAM roles instead of access keys
- Security groups with minimal ports
- Health checks with appropriate grace periods
- Proper depends_on where needed
- Target: 15-25 resources for typical deployments

## Step 4: Iterative Review with Critic (max 3 iterations)

### Critic Validation Scope
1. Security (CRITICAL): No hardcoded secrets, least-privilege IAM, minimal ports, encryption
2. Correctness (CRITICAL): All Solution Design components included, dependencies correct
3. Best Practices (MAJOR): Proper tags, variables, outputs, module structure
4. Production Readiness (MAJOR): Grace periods, cooldowns, timeouts configured

### Iteration Loop
- Submit terraform files to Critic → receive verdict
- If APPROVED → proceed to Step 5
- If NOT APPROVED → fix issues, create REVISION_LOG.md, resubmit
- If iteration >= 3 and not approved → report to user for manual review

CRITICAL: ONLY proceed to deployment after Critic APPROVED verdict.

## Step 5: Initialize and Plan
```bash
cd generated_docs_[TIMESTAMP]/terraform
terraform init
terraform plan -out=tfplan
```
Present plan summary to user.

## Step 6: Deploy (requires user confirmation)
```bash
terraform apply tfplan
```
DO NOT execute without explicit user confirmation.

## Step 7: Post-Deployment
After successful apply:
1. Extract terraform outputs
2. Run verification procedures (see [verification-procedures](verification-procedures.instructions.md))
3. Generate deployment report
4. Download AWS resource inventory
5. Execute user-specified tests if any
