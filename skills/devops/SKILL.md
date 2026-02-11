---
name: devops
description: AWS infrastructure reference knowledge for Terraform deployment, AWS services configuration, AMI building with GPU/NVIDIA drivers, and deployment troubleshooting. Provides production-ready reference docs for ALB, ASG, Lambda, CloudWatch, Image Builder, and Terraform IaC patterns.
---

# AWS DevOps Reference Knowledge

Reference documentation for AWS infrastructure deployment tasks. Use these when generating Terraform code, configuring AWS services, or troubleshooting deployments.

## Available References

Located in `references/` directory relative to this skill:

| # | File | Use When | Content |
|---|------|----------|---------|
| 1 | terraform-aws.md | ALWAYS for Terraform tasks | IaC provisioning, modules, resource syntax, backend config |
| 2 | aws-services.md | ALB, ASG, Lambda, CloudWatch | Service-specific configuration, CLI commands, Terraform resources |
| 3 | image-builder.md | Custom AMI with GPU/NVIDIA | Full AMI creation guide for ML workloads, CUDA, model pre-loading |
| 4 | troubleshooting.md | Errors during deployment | Common AWS errors, diagnosis steps, resolution patterns |
| 5 | deployment.md | Deployment and rollback | Deployment workflows, verification procedures, health checks |
| 6 | README.md | Quick orientation | When-to-use guide, cross-reference map, decision trees |

## AWS Credentials

Credential file: `.aws_credentials` in this skill directory.

```bash
source .github/skills/devops/.aws_credentials
```

## Loading Strategy

1. ALWAYS load `terraform-aws.md` before generating any Terraform
2. Load service-specific docs based on Solution Design requirements
3. Load `troubleshooting.md` reactively when errors occur
4. Load `deployment.md` before executing terraform apply
