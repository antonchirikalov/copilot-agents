# AWS Image Builder for ML Workloads

## Overview

AWS Image Builder automates creation of golden AMIs for STT (Speech-to-Text), TTS (Text-to-Speech), and LLM inference workloads. This guide covers automated AMI creation with NVIDIA drivers, CUDA toolkit, Python environments, and ML model pre-loading.

## Architecture

```
Image Pipeline Flow:
1. Base AMI (Ubuntu 22.04 Deep Learning AMI)
2. Component: Install/Update NVIDIA Drivers
3. Component: Install CUDA Toolkit
4. Component: Reboot Instance
5. Component: Setup Python Virtual Environment
6. Component: Install ML Dependencies
7. Component: Pre-download Models
8. Component: Configure systemd Auto-start
9. Component: Final Verification
10. Create Golden AMI
```

## Terraform Image Builder Configuration

### Main Image Pipeline

```hcl
# modules/image-builder/main.tf

resource "aws_imagebuilder_image_pipeline" "ml_workload" {
  name                             = "${var.project_name}-${var.workload_type}-pipeline"
  description                      = "Automated AMI creation for ${var.workload_type} workload"
  image_recipe_arn                 = aws_imagebuilder_image_recipe.ml_recipe.arn
  infrastructure_configuration_arn = aws_imagebuilder_infrastructure_configuration.ml_infra.arn
  distribution_configuration_arn   = aws_imagebuilder_distribution_configuration.ml_dist.arn
  
  schedule {
    schedule_expression                = "cron(0 0 * * SUN)"  # Weekly on Sunday
    pipeline_execution_start_condition = "EXPRESSION_MATCH_AND_DEPENDENCY_UPDATES_AVAILABLE"
  }

  tags = {
    Name        = "${var.project_name}-${var.workload_type}-pipeline"
    WorkloadType = var.workload_type
  }
}
```

### Infrastructure Configuration

```hcl
resource "aws_imagebuilder_infrastructure_configuration" "ml_infra" {
  name                          = "${var.project_name}-ml-infra"
  description                   = "Infrastructure for ML AMI builds"
  instance_profile_name         = aws_iam_instance_profile.imagebuilder.name
  instance_types                = [var.instance_type]  # g4dn.xlarge or g5.xlarge
  security_group_ids            = [aws_security_group.imagebuilder.id]
  subnet_id                     = var.subnet_id
  terminate_instance_on_failure = true
  
  logging {
    s3_logs {
      s3_bucket_name = aws_s3_bucket.imagebuilder_logs.id
      s3_key_prefix  = "image-builder-logs"
    }
  }

  tags = {
    Name = "${var.project_name}-imagebuilder-infra"
  }
}
```

### Image Recipe

```hcl
resource "aws_imagebuilder_image_recipe" "ml_recipe" {
  name         = "${var.project_name}-${var.workload_type}-recipe"
  parent_image = data.aws_ami.ubuntu_dl_ami.id
  version      = "1.0.0"
  
  block_device_mapping {
    device_name = "/dev/sda1"
    
    ebs {
      delete_on_termination = true
      volume_size           = var.volume_size  # 100GB for models
      volume_type           = "gp3"
      iops                  = 3000
      throughput            = 125
      encrypted             = true
    }
  }

  component {
    component_arn = aws_imagebuilder_component.nvidia_drivers.arn
  }

  component {
    component_arn = aws_imagebuilder_component.cuda_toolkit.arn
  }

  component {
    component_arn = aws_imagebuilder_component.reboot.arn
  }

  component {
    component_arn = aws_imagebuilder_component.python_venv.arn
    
    parameter {
      name  = "WorkloadType"
      value = var.workload_type  # stt, tts, or llm
    }
  }

  component {
    component_arn = aws_imagebuilder_component.ml_dependencies.arn
    
    parameter {
      name  = "WorkloadType"
      value = var.workload_type
    }
  }

  component {
    component_arn = aws_imagebuilder_component.model_download.arn
    
    parameter {
      name  = "WorkloadType"
      value = var.workload_type
    }
    
    parameter {
      name  = "ModelName"
      value = var.model_name  # e.g., "large-v3-turbo", "vits-tts", "llama-3-8b"
    }
  }

  component {
    component_arn = aws_imagebuilder_component.systemd_service.arn
    
    parameter {
      name  = "WorkloadType"
      value = var.workload_type
    }
    
    parameter {
      name  = "ServicePort"
      value = tostring(var.service_port)
    }
  }

  component {
    component_arn = aws_imagebuilder_component.verification.arn
  }

  tags = {
    Name         = "${var.project_name}-${var.workload_type}-recipe"
    WorkloadType = var.workload_type
  }
}
```

## Component Definitions

### Component 1: NVIDIA Drivers Installation

```hcl
resource "aws_imagebuilder_component" "nvidia_drivers" {
  name     = "${var.project_name}-nvidia-drivers"
  platform = "Linux"
  version  = "1.0.0"

  data = yamlencode({
    schemaVersion = 1.0
    phases = [
      {
        name = "build"
        steps = [
          {
            name   = "UpdateSystem"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "apt-get update",
                "apt-get upgrade -y"
              ]
            }
          },
          {
            name   = "InstallNvidiaDrivers"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# Check if NVIDIA drivers already installed",
                "if ! command -v nvidia-smi &> /dev/null; then",
                "  echo 'Installing NVIDIA drivers...'",
                "  apt-get install -y ubuntu-drivers-common",
                "  ubuntu-drivers autoinstall",
                "  # Or install specific version for g4dn (Tesla T4)",
                "  # apt-get install -y nvidia-driver-525",
                "else",
                "  echo 'NVIDIA drivers already installed'",
                "  nvidia-smi",
                "fi"
              ]
            }
          },
          {
            name   = "VerifyNvidiaInstallation"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# Verify driver files exist",
                "ls -la /usr/bin/nvidia-smi || echo 'WARNING: nvidia-smi not found'",
                "ls -la /usr/lib/x86_64-linux-gnu/libcuda.so* || echo 'WARNING: CUDA libraries not found'"
              ]
            }
          }
        ]
      }
    ]
  })
}
```

### Component 2: CUDA Toolkit

```hcl
resource "aws_imagebuilder_component" "cuda_toolkit" {
  name     = "${var.project_name}-cuda-toolkit"
  platform = "Linux"
  version  = "1.0.0"

  data = yamlencode({
    schemaVersion = 1.0
    phases = [
      {
        name = "build"
        steps = [
          {
            name   = "InstallCUDA"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# Install CUDA 12.1 (compatible with faster-whisper, TTS, most LLMs)",
                "if ! command -v nvcc &> /dev/null; then",
                "  wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb",
                "  dpkg -i cuda-keyring_1.0-1_all.deb",
                "  apt-get update",
                "  apt-get install -y cuda-toolkit-12-1",
                "  echo 'export PATH=/usr/local/cuda-12.1/bin:$PATH' >> /etc/environment",
                "  echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH' >> /etc/environment",
                "else",
                "  echo 'CUDA already installed'",
                "  nvcc --version",
                "fi"
              ]
            }
          },
          {
            name   = "InstallCuDNN"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# Install cuDNN for deep learning optimizations",
                "apt-get install -y libcudnn8 libcudnn8-dev"
              ]
            }
          }
        ]
      }
    ]
  })
}
```

### Component 3: Reboot Instance

```hcl
resource "aws_imagebuilder_component" "reboot" {
  name     = "${var.project_name}-reboot"
  platform = "Linux"
  version  = "1.0.0"

  data = yamlencode({
    schemaVersion = 1.0
    phases = [
      {
        name = "build"
        steps = [
          {
            name   = "Reboot"
            action = "Reboot"
            inputs = {
              delaySeconds = 10
            }
          }
        ]
      }
    ]
  })
}
```

### Component 4: Python Virtual Environment

```hcl
resource "aws_imagebuilder_component" "python_venv" {
  name     = "${var.project_name}-python-venv"
  platform = "Linux"
  version  = "1.0.0"

  data = yamlencode({
    schemaVersion = 1.0
    parameters = [
      {
        WorkloadType = {
          type        = "string"
          description = "Type of ML workload: stt, tts, or llm"
        }
      }
    ]
    phases = [
      {
        name = "build"
        steps = [
          {
            name   = "InstallPython"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# Install Python 3.10 and development tools",
                "apt-get install -y python3.10 python3.10-venv python3.10-dev",
                "apt-get install -y python3-pip build-essential",
                "# Install additional libraries for audio/video processing",
                "apt-get install -y ffmpeg libsm6 libxext6 libxrender-dev",
                "# Update pip",
                "python3.10 -m pip install --upgrade pip setuptools wheel"
              ]
            }
          },
          {
            name   = "CreateVirtualEnvironment"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# Create application directory structure",
                "mkdir -p /opt/{{ WorkloadType }}",
                "mkdir -p /opt/{{ WorkloadType }}/models",
                "mkdir -p /opt/{{ WorkloadType }}/logs",
                "# Create virtual environment",
                "python3.10 -m venv /opt/{{ WorkloadType }}/venv",
                "# Activate and upgrade pip in venv",
                "source /opt/{{ WorkloadType }}/venv/bin/activate",
                "pip install --upgrade pip setuptools wheel"
              ]
            }
          },
          {
            name   = "CreateServiceUser"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# Create dedicated user for service",
                "useradd -r -s /bin/bash -d /opt/{{ WorkloadType }} {{ WorkloadType }}",
                "# Add user to video group for GPU access",
                "usermod -aG video {{ WorkloadType }}",
                "# Set permissions",
                "chown -R {{ WorkloadType }}:{{ WorkloadType }} /opt/{{ WorkloadType }}"
              ]
            }
          }
        ]
      }
    ]
  })
}
```

### Component 5: ML Dependencies Installation

```hcl
resource "aws_imagebuilder_component" "ml_dependencies" {
  name     = "${var.project_name}-ml-dependencies"
  platform = "Linux"
  version  = "1.0.0"

  data = yamlencode({
    schemaVersion = 1.0
    parameters = [
      {
        WorkloadType = {
          type        = "string"
          description = "Type of ML workload: stt, tts, or llm"
        }
      }
    ]
    phases = [
      {
        name = "build"
        steps = [
          {
            name   = "CreateRequirementsFile"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# Create requirements.txt based on workload type",
                "cat > /opt/{{ WorkloadType }}/requirements.txt << 'EOF'",
                "{% if WorkloadType == 'stt' %}",
                "faster-whisper==1.0.0",
                "fastapi==0.109.0",
                "uvicorn[standard]==0.27.0",
                "python-multipart==0.0.9",
                "torch==2.1.2",
                "{% elif WorkloadType == 'tts' %}",
                "TTS==0.22.0",
                "fastapi==0.109.0",
                "uvicorn[standard]==0.27.0",
                "python-multipart==0.0.9",
                "torch==2.1.2",
                "numpy==1.24.3",
                "librosa==0.10.1",
                "{% elif WorkloadType == 'llm' %}",
                "vllm==0.3.1",
                "fastapi==0.109.0",
                "uvicorn[standard]==0.27.0",
                "torch==2.1.2",
                "transformers==4.37.0",
                "{% endif %}",
                "EOF"
              ]
            }
          },
          {
            name   = "InstallDependencies"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# Install dependencies in virtual environment",
                "source /opt/{{ WorkloadType }}/venv/bin/activate",
                "pip install -r /opt/{{ WorkloadType }}/requirements.txt",
                "# Verify installation",
                "pip list > /opt/{{ WorkloadType }}/installed_packages.txt"
              ]
            }
          }
        ]
      }
    ]
  })
}
```

### Component 6: Model Pre-download

```hcl
resource "aws_imagebuilder_component" "model_download" {
  name     = "${var.project_name}-model-download"
  platform = "Linux"
  version  = "1.0.0"

  data = yamlencode({
    schemaVersion = 1.0
    parameters = [
      {
        WorkloadType = {
          type        = "string"
          description = "Type of ML workload"
        }
      },
      {
        ModelName = {
          type        = "string"
          description = "Specific model to download"
        }
      }
    ]
    phases = [
      {
        name = "build"
        steps = [
          {
            name   = "SetEnvironmentVariables"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# Set Hugging Face cache location",
                "export HF_HOME=/opt/{{ WorkloadType }}/models",
                "echo 'export HF_HOME=/opt/{{ WorkloadType }}/models' >> /etc/environment"
              ]
            }
          },
          {
            name   = "DownloadModel"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "source /opt/{{ WorkloadType }}/venv/bin/activate",
                "export HF_HOME=/opt/{{ WorkloadType }}/models",
                "{% if WorkloadType == 'stt' %}",
                "# Download faster-whisper model",
                "python3 << 'PYEOF'",
                "from faster_whisper import WhisperModel",
                "import os",
                "os.environ['HF_HOME'] = '/opt/{{ WorkloadType }}/models'",
                "model = WhisperModel('{{ ModelName }}', device='cpu', compute_type='int8')",
                "print(f'Model {{ ModelName }} downloaded successfully to {os.environ[\"HF_HOME\"]}')",
                "PYEOF",
                "{% elif WorkloadType == 'tts' %}",
                "# Download TTS model",
                "python3 << 'PYEOF'",
                "from TTS.api import TTS",
                "import os",
                "os.environ['HF_HOME'] = '/opt/{{ WorkloadType }}/models'",
                "tts = TTS(model_name='{{ ModelName }}')",
                "print(f'TTS model {{ ModelName }} downloaded successfully')",
                "PYEOF",
                "{% elif WorkloadType == 'llm' %}",
                "# Download LLM model from Hugging Face",
                "python3 << 'PYEOF'",
                "from transformers import AutoTokenizer, AutoModelForCausalLM",
                "import os",
                "os.environ['HF_HOME'] = '/opt/{{ WorkloadType }}/models'",
                "tokenizer = AutoTokenizer.from_pretrained('{{ ModelName }}')",
                "model = AutoModelForCausalLM.from_pretrained('{{ ModelName }}')",
                "print(f'LLM model {{ ModelName }} downloaded successfully')",
                "PYEOF",
                "{% endif %}"
              ]
            }
          },
          {
            name   = "SetModelPermissions"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "chown -R {{ WorkloadType }}:{{ WorkloadType }} /opt/{{ WorkloadType }}/models",
                "chmod -R 755 /opt/{{ WorkloadType }}/models",
                "# Log model cache size",
                "du -sh /opt/{{ WorkloadType }}/models"
              ]
            }
          }
        ]
      }
    ]
  })
}
```

### Component 7: systemd Service Configuration

```hcl
resource "aws_imagebuilder_component" "systemd_service" {
  name     = "${var.project_name}-systemd-service"
  platform = "Linux"
  version  = "1.0.0"

  data = yamlencode({
    schemaVersion = 1.0
    parameters = [
      {
        WorkloadType = {
          type        = "string"
          description = "Type of ML workload"
        }
      },
      {
        ServicePort = {
          type        = "string"
          description = "Port for the service"
          default     = "8000"
        }
      }
    ]
    phases = [
      {
        name = "build"
        steps = [
          {
            name   = "CreateServiceScript"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# This will be replaced by actual service script via S3 or user data",
                "# Placeholder service script",
                "cat > /opt/{{ WorkloadType }}/service.py << 'EOF'",
                "# Service script placeholder",
                "# Actual script uploaded during deployment",
                "print('Service placeholder - replace with actual implementation')",
                "EOF",
                "chmod +x /opt/{{ WorkloadType }}/service.py",
                "chown {{ WorkloadType }}:{{ WorkloadType }} /opt/{{ WorkloadType }}/service.py"
              ]
            }
          },
          {
            name   = "CreateSystemdUnit"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "cat > /etc/systemd/system/{{ WorkloadType }}.service << 'EOF'",
                "[Unit]",
                "Description={{ WorkloadType | upper }} ML Service",
                "After=network.target",
                "",
                "[Service]",
                "Type=simple",
                "User={{ WorkloadType }}",
                "Group=video",
                "WorkingDirectory=/opt/{{ WorkloadType }}",
                "Environment=\"HF_HOME=/opt/{{ WorkloadType }}/models\"",
                "Environment=\"CUDA_VISIBLE_DEVICES=0\"",
                "ExecStart=/opt/{{ WorkloadType }}/venv/bin/python /opt/{{ WorkloadType }}/service.py",
                "Restart=always",
                "RestartSec=10",
                "StandardOutput=append:/opt/{{ WorkloadType }}/logs/service.log",
                "StandardError=append:/opt/{{ WorkloadType }}/logs/error.log",
                "",
                "[Install]",
                "WantedBy=multi-user.target",
                "EOF"
              ]
            }
          },
          {
            name   = "EnableService"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# Reload systemd",
                "systemctl daemon-reload",
                "# Enable service to start on boot",
                "systemctl enable {{ WorkloadType }}.service",
                "# Don't start now - will start on instance launch",
                "echo 'Service configured and enabled for auto-start'"
              ]
            }
          }
        ]
      }
    ]
  })
}
```

### Component 8: Final Verification

```hcl
resource "aws_imagebuilder_component" "verification" {
  name     = "${var.project_name}-verification"
  platform = "Linux"
  version  = "1.0.0"

  data = yamlencode({
    schemaVersion = 1.0
    phases = [
      {
        name = "build"
        steps = [
          {
            name   = "VerifyNvidiaDriver"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "nvidia-smi || (echo 'ERROR: nvidia-smi failed' && exit 1)",
                "nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv"
              ]
            }
          },
          {
            name   = "VerifyCUDA"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "nvcc --version || (echo 'ERROR: CUDA not found' && exit 1)"
              ]
            }
          },
          {
            name   = "VerifyPythonEnvironment"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "# Check virtual environments exist",
                "ls -la /opt/stt/venv/bin/python || echo 'STT venv not found'",
                "ls -la /opt/tts/venv/bin/python || echo 'TTS venv not found'",
                "ls -la /opt/llm/venv/bin/python || echo 'LLM venv not found'"
              ]
            }
          },
          {
            name   = "VerifySystemdServices"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "systemctl list-unit-files | grep -E '(stt|tts|llm).service' || echo 'No ML services configured'"
              ]
            }
          },
          {
            name   = "GenerateValidationReport"
            action = "ExecuteBash"
            inputs = {
              commands = [
                "cat > /opt/ami-validation-report.txt << 'EOF'",
                "=== AMI Validation Report ===",
                "Build Date: $(date)",
                "",
                "NVIDIA Driver:",
                "$(nvidia-smi --query-gpu=driver_version --format=csv,noheader)",
                "",
                "CUDA Version:",
                "$(nvcc --version | grep release)",
                "",
                "GPU Information:",
                "$(nvidia-smi --query-gpu=name,memory.total --format=csv)",
                "",
                "Installed Services:",
                "$(systemctl list-unit-files | grep -E '(stt|tts|llm).service')",
                "",
                "Model Cache Sizes:",
                "$(du -sh /opt/*/models 2>/dev/null || echo 'No models cached')",
                "EOF",
                "cat /opt/ami-validation-report.txt"
              ]
            }
          }
        ]
      }
    ]
  })
}
```

## IAM Role for Image Builder

```hcl
# modules/image-builder/iam.tf

resource "aws_iam_role" "imagebuilder" {
  name = "${var.project_name}-imagebuilder-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "imagebuilder_ec2" {
  role       = aws_iam_role.imagebuilder.name
  policy_arn = "arn:aws:iam::aws:policy/EC2InstanceProfileForImageBuilder"
}

resource "aws_iam_role_policy_attachment" "imagebuilder_s3" {
  role       = aws_iam_role.imagebuilder.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_iam_instance_profile" "imagebuilder" {
  name = "${var.project_name}-imagebuilder-profile"
  role = aws_iam_role.imagebuilder.name
}
```

## AWS CLI Manual AMI Creation

For manual/one-off AMI creation without Image Builder:

```bash
#!/bin/bash
# manual-ami-creation.sh

set -e

PROJECT_NAME="whisper-stt"
WORKLOAD_TYPE="stt"  # stt, tts, or llm
MODEL_NAME="large-v3-turbo"
INSTANCE_TYPE="g4dn.xlarge"
REGION="eu-north-1"

# 1. Launch build instance
echo "Launching build instance..."
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id ami-XXXXXXXXX \  # Ubuntu 22.04 Deep Learning AMI
  --instance-type $INSTANCE_TYPE \
  --key-name your-key-pair \
  --security-group-ids sg-XXXXXXXXX \
  --subnet-id subnet-XXXXXXXXX \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3"}}]' \
  --region $REGION \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Instance ID: $INSTANCE_ID"

# 2. Wait for instance running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# 3. Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region $REGION \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "Instance running at: $PUBLIC_IP"
echo "SSH: ssh -i your-key.pem ubuntu@$PUBLIC_IP"

# 4. Create setup script
cat > setup-ami.sh << 'SETUP_EOF'
#!/bin/bash
set -e

WORKLOAD_TYPE="${WORKLOAD_TYPE}"
MODEL_NAME="${MODEL_NAME}"

echo "=== Step 1: Update system ==="
sudo apt-get update
sudo apt-get upgrade -y

echo "=== Step 2: Install NVIDIA drivers ==="
if ! command -v nvidia-smi &> /dev/null; then
  sudo apt-get install -y ubuntu-drivers-common
  sudo ubuntu-drivers autoinstall
fi

echo "=== Step 3: Install CUDA ==="
if ! command -v nvcc &> /dev/null; then
  wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
  sudo dpkg -i cuda-keyring_1.0-1_all.deb
  sudo apt-get update
  sudo apt-get install -y cuda-toolkit-12-1
  echo 'export PATH=/usr/local/cuda-12.1/bin:$PATH' | sudo tee -a /etc/environment
  echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH' | sudo tee -a /etc/environment
fi

echo "=== Step 4: Install system dependencies ==="
sudo apt-get install -y python3.10 python3.10-venv python3.10-dev python3-pip
sudo apt-get install -y ffmpeg build-essential

echo "=== Step 5: Reboot for driver activation ==="
sudo reboot
SETUP_EOF

# 5. Upload and run setup script (Part 1 - before reboot)
scp -i your-key.pem setup-ami.sh ubuntu@$PUBLIC_IP:/tmp/
ssh -i your-key.pem ubuntu@$PUBLIC_IP "bash /tmp/setup-ami.sh"

# 6. Wait for reboot
echo "Waiting for instance to reboot..."
sleep 60
aws ec2 wait instance-status-ok --instance-ids $INSTANCE_ID --region $REGION

# 7. Create post-reboot script
cat > post-reboot-setup.sh << 'POST_EOF'
#!/bin/bash
set -e

WORKLOAD_TYPE="${WORKLOAD_TYPE}"
MODEL_NAME="${MODEL_NAME}"

echo "=== Step 6: Verify NVIDIA ==="
nvidia-smi
nvcc --version

echo "=== Step 7: Create application structure ==="
sudo mkdir -p /opt/$WORKLOAD_TYPE/{models,logs}
sudo python3.10 -m venv /opt/$WORKLOAD_TYPE/venv

echo "=== Step 8: Create service user ==="
sudo useradd -r -s /bin/bash -d /opt/$WORKLOAD_TYPE $WORKLOAD_TYPE
sudo usermod -aG video $WORKLOAD_TYPE

echo "=== Step 9: Install Python dependencies ==="
source /opt/$WORKLOAD_TYPE/venv/bin/activate

if [ "$WORKLOAD_TYPE" = "stt" ]; then
  pip install faster-whisper fastapi uvicorn[standard] python-multipart torch
elif [ "$WORKLOAD_TYPE" = "tts" ]; then
  pip install TTS fastapi uvicorn[standard] python-multipart torch
elif [ "$WORKLOAD_TYPE" = "llm" ]; then
  pip install vllm fastapi uvicorn[standard] transformers torch
fi

echo "=== Step 10: Pre-download model ==="
export HF_HOME=/opt/$WORKLOAD_TYPE/models

if [ "$WORKLOAD_TYPE" = "stt" ]; then
  python3 << PYEOF
from faster_whisper import WhisperModel
import os
os.environ['HF_HOME'] = '/opt/$WORKLOAD_TYPE/models'
model = WhisperModel('$MODEL_NAME', device='cpu', compute_type='int8')
print('Model downloaded successfully')
PYEOF
fi

echo "=== Step 11: Set permissions ==="
sudo chown -R $WORKLOAD_TYPE:$WORKLOAD_TYPE /opt/$WORKLOAD_TYPE
sudo chmod -R 755 /opt/$WORKLOAD_TYPE

echo "=== Step 12: Create systemd service template ==="
sudo tee /etc/systemd/system/$WORKLOAD_TYPE.service > /dev/null << SYSTEMD_EOF
[Unit]
Description=${WORKLOAD_TYPE^^} ML Service
After=network.target

[Service]
Type=simple
User=$WORKLOAD_TYPE
Group=video
WorkingDirectory=/opt/$WORKLOAD_TYPE
Environment="HF_HOME=/opt/$WORKLOAD_TYPE/models"
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/opt/$WORKLOAD_TYPE/venv/bin/python /opt/$WORKLOAD_TYPE/service.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/$WORKLOAD_TYPE/logs/service.log
StandardError=append:/opt/$WORKLOAD_TYPE/logs/error.log

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

sudo systemctl daemon-reload
sudo systemctl enable $WORKLOAD_TYPE.service

echo "=== AMI Setup Complete ==="
nvidia-smi
du -sh /opt/$WORKLOAD_TYPE/models
systemctl list-unit-files | grep $WORKLOAD_TYPE
POST_EOF

# 8. Run post-reboot setup
scp -i your-key.pem post-reboot-setup.sh ubuntu@$PUBLIC_IP:/tmp/
ssh -i your-key.pem ubuntu@$PUBLIC_IP "WORKLOAD_TYPE=$WORKLOAD_TYPE MODEL_NAME=$MODEL_NAME bash /tmp/post-reboot-setup.sh"

# 9. Create AMI
echo "Creating AMI from instance $INSTANCE_ID..."
AMI_ID=$(aws ec2 create-image \
  --instance-id $INSTANCE_ID \
  --name "${PROJECT_NAME}-${WORKLOAD_TYPE}-$(date +%Y%m%d-%H%M%S)" \
  --description "Golden AMI for ${WORKLOAD_TYPE} workload with ${MODEL_NAME}" \
  --region $REGION \
  --query 'ImageId' \
  --output text)

echo "AMI ID: $AMI_ID"

# 10. Wait for AMI available
aws ec2 wait image-available --image-ids $AMI_ID --region $REGION

# 11. Tag AMI
aws ec2 create-tags \
  --resources $AMI_ID \
  --tags \
    Key=Name,Value="${PROJECT_NAME}-${WORKLOAD_TYPE}" \
    Key=WorkloadType,Value=$WORKLOAD_TYPE \
    Key=ModelName,Value=$MODEL_NAME \
    Key=CreatedDate,Value=$(date +%Y-%m-%d) \
  --region $REGION

# 12. Terminate build instance
echo "Terminating build instance..."
aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $REGION

echo "=== AMI Creation Complete ==="
echo "AMI ID: $AMI_ID"
echo "Use this AMI in your launch template for auto-scaling"
```

## Integration with Auto Scaling

Once AMI is created, reference it in your launch template:

```hcl
# In modules/asg/main.tf

data "aws_ami" "ml_workload" {
  most_recent = true
  owners      = ["self"]

  filter {
    name   = "tag:WorkloadType"
    values = [var.workload_type]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

resource "aws_launch_template" "ml_service" {
  name_prefix   = "${var.project_name}-${var.workload_type}-"
  image_id      = data.aws_ami.ml_workload.id  # Use golden AMI
  instance_type = var.instance_type

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    workload_type = var.workload_type
    service_script_url = var.service_script_url
  }))

  # ... rest of launch template config
}
```

## User Data Script for Service Deployment

```bash
#!/bin/bash
# user_data.sh - Runs on instance launch from golden AMI

set -e

WORKLOAD_TYPE="${workload_type}"
SERVICE_SCRIPT_URL="${service_script_url}"

# 1. Download actual service script from S3
aws s3 cp $SERVICE_SCRIPT_URL /opt/$WORKLOAD_TYPE/service.py
chown $WORKLOAD_TYPE:$WORKLOAD_TYPE /opt/$WORKLOAD_TYPE/service.py
chmod +x /opt/$WORKLOAD_TYPE/service.py

# 2. Start service
systemctl start $WORKLOAD_TYPE.service

# 3. Wait for service ready
for i in {1..30}; do
  if curl -f http://localhost:8000/health; then
    echo "Service is healthy"
    break
  fi
  echo "Waiting for service... ($i/30)"
  sleep 2
done

# 4. Publish readiness metric to CloudWatch
aws cloudwatch put-metric-data \
  --namespace "MLWorkloads" \
  --metric-name "InstanceReady" \
  --value 1 \
  --dimensions WorkloadType=$WORKLOAD_TYPE

echo "Instance ready for traffic"
```

## Best Practices

1. AMI Versioning: Tag AMIs with version numbers and creation dates
2. Model Pre-caching: Always pre-download models in AMI to reduce startup time
3. Security: Don't include API keys or credentials in AMI - use Secrets Manager
4. Testing: Validate AMI by launching test instance before using in ASG
5. Regular Updates: Rebuild AMIs weekly/monthly to include security patches
6. Cost Optimization: Delete old AMIs and snapshots to reduce storage costs
7. Multi-Region: Copy AMIs to other regions for disaster recovery
8. Documentation: Maintain AMI changelog with components and model versions

## Troubleshooting

Common issues:

1. NVIDIA driver not loaded after reboot:
   - Check kernel version compatibility
   - Verify Secure Boot is disabled
   - Review /var/log/nvidia-installer.log

2. Model download fails:
   - Check internet connectivity
   - Verify HF_HOME permissions
   - Increase instance disk space

3. systemd service won't start:
   - Check service logs: journalctl -u stt.service
   - Verify user has GPU access: groups stt
   - Test script manually as service user: sudo -u stt /opt/stt/venv/bin/python /opt/stt/service.py

4. Image Builder pipeline fails:
   - Review CloudWatch Logs in S3 bucket
   - Check IAM role permissions
   - Verify component YAML syntax

This comprehensive guide enables automated golden AMI creation for STT, TTS, and LLM workloads with all required dependencies, drivers, and configurations baked in.
