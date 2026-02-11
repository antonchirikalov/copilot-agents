# DevOps Agent - Quick Reference Guide

## When to Use Each Reference Document

### 1. Terraform AWS Reference
Use when:
- Setting up Terraform backend (S3 + DynamoDB)
- Creating modular Terraform structure
- Working with Terraform state management
- Need Terraform best practices

Key sections: Module structure, backend config, provider setup

### 2. AWS Services Reference
Use when:
- Deploying ALB (Application Load Balancer)
- Configuring Auto Scaling Groups
- Setting up Lambda functions
- Creating CloudWatch alarms
- Configuring target groups and health checks

Key sections: Service-specific AWS CLI commands and Terraform resources

### 3. AWS Image Builder Reference
Use when:
- Creating AMI for STT (Speech-to-Text) workload
- Creating AMI for TTS (Text-to-Speech) workload
- Creating AMI for LLM inference workload
- Need to install NVIDIA drivers and CUDA
- Pre-downloading ML models into AMI
- Setting up systemd auto-start for ML services
- Configuring Python virtual environments in AMI

Key sections:
- Image Builder pipeline configuration
- 8 component definitions (drivers, CUDA, reboot, venv, dependencies, models, systemd, verification)
- Manual AMI creation script
- Integration with Auto Scaling

### 4. Troubleshooting Guide
Use when:
- Deployment fails
- Service health checks failing
- NVIDIA driver issues
- Model loading problems
- Terraform errors
- AWS service limits exceeded

Key sections: Error patterns, diagnostic commands, resolution steps

### 5. Deployment Guide
Use when:
- Executing full deployment workflow
- Running verification commands
- Performing rollback procedures
- Post-deployment validation

Key sections: Step-by-step deployment, verification commands, rollback options

## Common Workflows

### Workflow 1: Deploy Infrastructure with Pre-built AMI
1. Read: Deployment Guide (overall process)
2. Read: Terraform AWS Reference (state setup)
3. Read: AWS Services Reference (specific services)
4. Execute: Terraform deployment
5. Reference: Troubleshooting Guide (if issues)

### Workflow 2: Create Custom AMI for ML Workload
1. Read: Image Builder Reference (full guide)
2. Choose: Terraform Image Builder OR Manual script approach
3. Configure: Components based on workload type (STT/TTS/LLM)
4. Execute: Pipeline or manual creation
5. Verify: AMI validation report
6. Reference: Troubleshooting Guide (for driver/CUDA issues)

### Workflow 3: Deploy Auto-Scaling ML Service
1. Read: Image Builder Reference (create AMI first)
2. Read: AWS Services Reference (ASG + ALB setup)
3. Read: Deployment Guide (deployment process)
4. Execute: Full deployment with custom AMI
5. Monitor: CloudWatch dashboards
6. Reference: Troubleshooting Guide (for scaling issues)

## Quick Commands Reference

### Check Current AMIs
```bash
# List all ML workload AMIs
aws ec2 describe-images \
  --owners self \
  --filters "Name=tag:WorkloadType,Values=stt,tts,llm" \
  --query 'Images[*].[ImageId,Name,CreationDate,Tags[?Key==`WorkloadType`].Value|[0]]' \
  --output table
```

### Verify AMI Components
```bash
# Launch instance from AMI and check
INSTANCE_ID=$(aws ec2 run-instances --image-id ami-XXXXXXXX --instance-type g4dn.xlarge --query 'Instances[0].InstanceId' --output text)
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# SSH and verify
ssh ubuntu@<ip> "nvidia-smi && systemctl list-unit-files | grep -E '(stt|tts|llm)'"
```

### Manual AMI Creation (Quick)
```bash
# From running instance with all setup complete
aws ec2 create-image \
  --instance-id i-XXXXXXXXX \
  --name "stt-whisper-$(date +%Y%m%d)" \
  --description "Whisper STT with NVIDIA drivers" \
  --tag-specifications 'ResourceType=image,Tags=[{Key=WorkloadType,Value=stt}]'
```

### Check Image Builder Pipeline Status
```bash
# List pipelines
aws imagebuilder list-image-pipelines

# Get pipeline executions
aws imagebuilder list-image-pipeline-images \
  --image-pipeline-arn arn:aws:imagebuilder:REGION:ACCOUNT:image-pipeline/NAME

# Get build logs from S3
aws s3 ls s3://your-imagebuilder-logs-bucket/image-builder-logs/
```

## Decision Tree: Which AMI Creation Method?

```
Need to create AMI for ML workload?
├─ One-time / Testing?
│  └─ Use: Manual AMI Creation Script (image-builder.md section "AWS CLI Manual AMI Creation")
│     - Faster setup
│     - Full control
│     - Good for prototyping
│
└─ Production / Recurring updates?
   └─ Use: AWS Image Builder Pipeline (image-builder.md section "Terraform Image Builder Configuration")
      - Automated rebuilds
      - Version tracking
      - Scheduled updates
      - Multi-region distribution
```

## Workload Type Specific Guidance

### STT (Speech-to-Text)
- Reference: image-builder.md
- Model: faster-whisper (large-v3-turbo, medium, etc.)
- Key dependencies: faster-whisper, fastapi, uvicorn, python-multipart
- GPU requirement: g4dn.xlarge minimum (16GB VRAM)
- Startup time: 15-30 seconds (model loading)
- Health check: GET /health
- Endpoint: POST /v1/audio/transcriptions

### TTS (Text-to-Speech)
- Reference: image-builder.md
- Model: Coqui TTS (vits, tacotron2, etc.)
- Key dependencies: TTS, fastapi, uvicorn, librosa
- GPU requirement: g4dn.xlarge or g5.xlarge
- Startup time: 10-20 seconds (model loading)
- Health check: GET /health
- Endpoint: POST /v1/audio/speech

### LLM (Large Language Model)
- Reference: image-builder.md
- Model: Llama, Mistral, Phi, etc.
- Key dependencies: vllm, transformers, fastapi, torch
- GPU requirement: g5.xlarge+ (depends on model size)
- Startup time: 30-120 seconds (model loading, longer for larger models)
- Health check: GET /health
- Endpoint: POST /v1/completions or /v1/chat/completions

## Integration Points

### From AMI to Auto Scaling
1. Create AMI using Image Builder reference
2. Note AMI ID
3. Use AMI in Launch Template (aws-services.md)
4. Configure ASG with Launch Template
5. Set health check grace period (account for model loading time)
6. Deploy using Deployment Guide

### From Design Document to Deployment
1. Orchestrator creates Solution Design Document
2. DevOps reads Solution Design from generated_docs_[TIMESTAMP]/
3. If custom AMI needed: Follow Image Builder reference
4. If using pre-built AMI: Proceed with Deployment Guide
5. Apply Terraform configuration
6. Verify using AWS Services reference commands

## File Locations

All reference documents located in:
```
.github/skills/devops/references/
├── README.md                 (Quick reference guide - START HERE)
├── terraform-aws.md          (438 lines - Terraform IaC)
├── aws-services.md           (486 lines - AWS services config)
├── image-builder.md          (1093 lines - Full AMI creation guide)
├── troubleshooting.md        (Error diagnosis and fixes)
└── deployment.md             (481 lines - Deployment workflows)
```

Output from Orchestrator workflow:
```
generated_docs_[TIMESTAMP]/
├── Solution_Design_Document.md
├── workflow_log.md
├── workflow_state.json
└── research/
    └── *.md
```

## Next Steps After Reading This Guide

1. Identify your task (deployment, AMI creation, troubleshooting)
2. Select appropriate reference document(s)
3. Follow step-by-step procedures
4. Use quick commands for verification
5. Reference troubleshooting if issues arise

Remember: DevOps agent activates only on explicit command (deploy, apply infrastructure, execute deployment). Always review Solution_Design_Document.md from orchestrator workflow before executing.
