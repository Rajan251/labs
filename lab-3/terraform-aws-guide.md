# Complete Terraform AWS Infrastructure Guide

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Prerequisites (Ubuntu Server)](#2-prerequisites-ubuntu-server)
3. [Terraform Project Layout](#3-terraform-project-layout)
4. [Remote State & State Locking](#4-remote-state--state-locking)
5. [Provider & Authentication](#5-provider--authentication)
6. [Networking: VPC, Subnets, Routing](#6-networking-vpc-subnets-routing)
7. [Security Groups & IAM](#7-security-groups--iam)
8. [EC2 Instances](#8-ec2-instances)
9. [Application Load Balancer](#9-application-load-balancer)
10. [S3 Buckets](#10-s3-buckets)
11. [Variables, Outputs, Secrets](#11-variables-outputs-secrets)
12. [Modules & Reusability](#12-modules--reusability)
13. [CI/CD for Terraform](#13-cicd-for-terraform)
14. [Testing & Validation](#14-testing--validation)
15. [Change Management & Rollback](#15-change-management--rollback)
16. [Cost & Security Considerations](#16-cost--security-considerations)
17. [Troubleshooting](#17-troubleshooting)
18. [End-to-End Code Examples](#18-end-to-end-code-examples)
19. [Step-by-Step Runbook](#19-step-by-step-runbook)
20. [Cleanup & Destroy](#20-cleanup--destroy)
21. [Deliverables & File List](#21-deliverables--file-list)
22. [Advanced Topics](#22-advanced-topics)
23. [Best Practices Checklist](#23-best-practices-checklist)

---

## 1. Project Overview

### Goal
This guide demonstrates how to provision a production-ready AWS infrastructure using Terraform from an Ubuntu server. The end state includes:

- **VPC** with public and private subnets across multiple Availability Zones
- **Bastion host** for secure SSH access
- **EC2 application servers** in private subnets
- **Application Load Balancer (ALB)** distributing traffic to app instances
- **S3 buckets** for storage, artifacts, and Terraform state
- **Security groups** and IAM roles following least privilege
- **Remote state** with locking for team collaboration

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          AWS Region                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    VPC (10.0.0.0/16)                      │  │
│  │                                                           │  │
│  │  ┌──────────────────────┐  ┌──────────────────────┐     │  │
│  │  │  Public Subnet AZ-A  │  │  Public Subnet AZ-B  │     │  │
│  │  │    (10.0.1.0/24)     │  │    (10.0.2.0/24)     │     │  │
│  │  │                      │  │                      │     │  │
│  │  │  ┌──────────────┐    │  │    ┌──────────────┐ │     │  │
│  │  │  │   Bastion    │    │  │    │     ALB      │ │     │  │
│  │  │  │    Host      │    │  │    │  (Public)    │ │     │  │
│  │  │  └──────────────┘    │  │    └──────┬───────┘ │     │  │
│  │  │  ┌──────────────┐    │  │           │         │     │  │
│  │  │  │ NAT Gateway  │    │  │           │         │     │  │
│  │  │  └──────┬───────┘    │  │           │         │     │  │
│  │  └─────────┼────────────┘  └───────────┼─────────┘     │  │
│  │            │                            │               │  │
│  │            │  Internet Gateway          │               │  │
│  │            │         ▲                  │               │  │
│  │  ┌─────────┼─────────┼──────────────────┼─────────┐     │  │
│  │  │         │         │                  │         │     │  │
│  │  │  Private Subnet AZ-A    Private Subnet AZ-B    │     │  │
│  │  │    (10.0.11.0/24)         (10.0.12.0/24)       │     │  │
│  │  │                                                 │     │  │
│  │  │  ┌──────────────┐       ┌──────────────┐       │     │  │
│  │  │  │  App Server  │       │  App Server  │       │     │  │
│  │  │  │   EC2 (ASG)  │       │   EC2 (ASG)  │       │     │  │
│  │  │  └──────┬───────┘       └──────┬───────┘       │     │  │
│  │  │         │                      │               │     │  │
│  │  │         └──────────┬───────────┘               │     │  │
│  │  │                    │                           │     │  │
│  │  └────────────────────┼───────────────────────────┘     │  │
│  │                       │                                 │  │
│  └───────────────────────┼─────────────────────────────────┘  │
│                          │                                    │
│                          ▼                                    │
│                   ┌─────────────┐                             │
│                   │  S3 Buckets │                             │
│                   │  - State    │                             │
│                   │  - Artifacts│                             │
│                   │  - Storage  │                             │
│                   └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### Use Cases

This pattern is appropriate for:

- **Multi-tier web applications** requiring high availability
- **Microservices architectures** with load balancing
- **Production workloads** needing secure network isolation
- **Team environments** with shared infrastructure state
- **Compliance requirements** demanding private subnets and bastion access

---

## 2. Prerequisites (Ubuntu Server)

### Minimum Requirements

- **OS**: Ubuntu 20.04 LTS or later (22.04 recommended)
- **RAM**: 2GB minimum
- **Disk**: 20GB free space
- **Network**: Internet connectivity
- **AWS Account** with programmatic access

### Step 1: Update System and Install Base Tools

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y \
  curl \
  wget \
  unzip \
  git \
  jq \
  software-properties-common \
  gnupg \
  ca-certificates
```

### Step 2: Install AWS CLI

```bash
# Download AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Unzip and install
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
# Expected output: aws-cli/2.x.x Python/3.x.x Linux/x.x.x

# Cleanup
rm -rf aws awscliv2.zip
```

### Step 3: Configure AWS Credentials

```bash
# Create AWS credentials directory
mkdir -p ~/.aws

# Configure credentials (interactive)
aws configure

# Or manually create credentials file
cat > ~/.aws/credentials << 'EOF'
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY

[terraform]
aws_access_key_id = YOUR_TERRAFORM_ACCESS_KEY
aws_secret_access_key = YOUR_TERRAFORM_SECRET_KEY
EOF

# Create config file
cat > ~/.aws/config << 'EOF'
[default]
region = us-east-1
output = json

[profile terraform]
region = us-east-1
output = json
EOF

# Secure credentials
chmod 600 ~/.aws/credentials
chmod 600 ~/.aws/config
```

### Step 4: Verify AWS Access

```bash
# Test AWS CLI access
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDAXXXXXXXXXXXXXXXXX",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-user"
# }

# List S3 buckets (test permissions)
aws s3 ls

# Check EC2 regions
aws ec2 describe-regions --query 'Regions[].RegionName' --output table
```

### Step 5: Install Terraform

```bash
# Add HashiCorp GPG key
wget -O- https://apt.releases.hashicorp.com/gpg | \
  gpg --dearmor | \
  sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Add HashiCorp repository
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
  https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
  sudo tee /etc/apt/sources.list.d/hashicorp.list

# Update and install Terraform
sudo apt update
sudo apt install -y terraform

# Verify installation
terraform version
# Expected output: Terraform v1.6.x or later

# Enable tab completion
terraform -install-autocomplete
```

### Alternative: Manual Terraform Installation

```bash
# Set Terraform version
TERRAFORM_VERSION="1.6.5"

# Download Terraform
wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# Download SHA256 checksums
wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_SHA256SUMS

# Verify checksum
sha256sum -c terraform_${TERRAFORM_VERSION}_SHA256SUMS 2>&1 | grep OK

# Unzip and install
unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify
terraform version

# Cleanup
rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip terraform_${TERRAFORM_VERSION}_SHA256SUMS
```

### Step 6: Install Additional Tools (Optional but Recommended)

```bash
# Install tflint for linting
curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Install checkov for security scanning
pip3 install checkov

# Install terraform-docs for documentation
curl -Lo ./terraform-docs.tar.gz https://github.com/terraform-docs/terraform-docs/releases/download/v0.16.0/terraform-docs-v0.16.0-linux-amd64.tar.gz
tar -xzf terraform-docs.tar.gz
sudo mv terraform-docs /usr/local/bin/
rm terraform-docs.tar.gz
```

---

## 3. Terraform Project Layout

### Recommended Directory Structure

```
terraform-aws-infrastructure/
├── README.md
├── .gitignore
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   ├── ec2-asg/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── user_data.sh
│   │   └── README.md
│   ├── alb/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── s3/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── envs/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── terraform.tfvars
│       └── backend.tf
├── scripts/
│   ├── init.sh
│   ├── plan.sh
│   ├── apply.sh
│   └── destroy.sh
└── docs/
    ├── architecture.md
    └── runbook.md
```

### Key Files Explained

| File | Purpose |
|------|---------|
| `versions.tf` | Terraform and provider version constraints |
| `providers.tf` | Provider configuration (AWS, region, profile) |
| `main.tf` | Main resource definitions |
| `variables.tf` | Input variable declarations |
| `outputs.tf` | Output value definitions |
| `terraform.tfvars` | Variable values (environment-specific) |
| `backend.tf` | Remote state backend configuration |
| `.gitignore` | Exclude sensitive files from version control |

### Example `.gitignore`

```gitignore
# Local .terraform directories
**/.terraform/*

# .tfstate files
*.tfstate
*.tfstate.*

# Crash log files
crash.log
crash.*.log

# Exclude all .tfvars files (may contain sensitive data)
*.tfvars
*.tfvars.json

# Ignore override files
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Ignore CLI configuration files
.terraformrc
terraform.rc

# Ignore plan files
*.tfplan
*.plan

# Ignore lock files (optional - some teams commit this)
# .terraform.lock.hcl
```

### Example `versions.tf`

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

### Modules vs Single-File Setup

**Use modules when:**
- Infrastructure is reused across environments
- Team collaboration requires clear boundaries
- Components are complex and benefit from encapsulation
- You need to version and test components independently

**Use single-file when:**
- Quick prototypes or proof-of-concepts
- Very simple infrastructure (< 100 lines)
- Learning Terraform basics

---

## 4. Remote State & State Locking

### Why Remote State?

- **Collaboration**: Multiple team members can work together
- **Security**: State files contain sensitive data (IPs, passwords)
- **Reliability**: Cloud storage is more reliable than local disks
- **Locking**: Prevents concurrent modifications
- **Versioning**: Track state history and enable rollback

### Step 1: Create S3 Bucket for State

```bash
# Set variables
AWS_REGION="us-east-1"
BUCKET_NAME="my-terraform-state-$(date +%s)"  # Unique name
DYNAMODB_TABLE="terraform-state-lock"

# Create S3 bucket
aws s3api create-bucket \
  --bucket ${BUCKET_NAME} \
  --region ${AWS_REGION}

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ${BUCKET_NAME} \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket ${BUCKET_NAME} \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket ${BUCKET_NAME} \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### Step 2: Create DynamoDB Table for Locking

```bash
# Create DynamoDB table
aws dynamodb create-table \
  --table-name ${DYNAMODB_TABLE} \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ${AWS_REGION}

# Wait for table to be active
aws dynamodb wait table-exists --table-name ${DYNAMODB_TABLE}

# Verify table
aws dynamodb describe-table --table-name ${DYNAMODB_TABLE} --query 'Table.TableStatus'
```

### Step 3: Configure Backend in Terraform

Create `backend.tf`:

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state-1234567890"  # Replace with your bucket
    key            = "envs/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
    
    # Optional: Use KMS for encryption
    # kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
  }
}
```

### Step 4: Secure Backend with IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::my-terraform-state-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::my-terraform-state-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/terraform-state-lock"
    }
  ]
}
```

### Step 5: Initialize with Backend

```bash
# Initialize Terraform
terraform init

# Or with backend config file
terraform init -backend-config=backend.hcl

# Migrate existing local state to remote
terraform init -migrate-state
```

### Using Backend Config Files

Create `backend.hcl`:

```hcl
bucket         = "my-terraform-state-1234567890"
key            = "envs/prod/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "terraform-state-lock"
profile        = "terraform"
```

Initialize:

```bash
terraform init -backend-config=backend.hcl
```

---

## 5. Provider & Authentication Configuration

### Example `providers.tf`

```hcl
provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "Terraform"
      Project     = var.project_name
      Owner       = var.owner
    }
  }
}

# Optional: Additional provider for different region
provider "aws" {
  alias   = "us_west_2"
  region  = "us-west-2"
  profile = var.aws_profile
}
```

### Authentication Methods

#### Method 1: AWS Profile (Recommended for Local Development)

```hcl
provider "aws" {
  region  = "us-east-1"
  profile = "terraform"  # References ~/.aws/credentials
}
```

#### Method 2: Environment Variables

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

terraform plan
```

```hcl
provider "aws" {
  region = "us-east-1"
  # Credentials automatically picked from environment
}
```

#### Method 3: Instance Profile (For EC2-based CI/CD)

```hcl
provider "aws" {
  region = "us-east-1"
  # Credentials automatically from EC2 instance metadata
}
```

### IAM Policy for Terraform User (Least Privilege Example)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2Permissions",
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:CreateSubnet",
        "ec2:DeleteSubnet",
        "ec2:CreateInternetGateway",
        "ec2:AttachInternetGateway",
        "ec2:DetachInternetGateway",
        "ec2:DeleteInternetGateway",
        "ec2:CreateNatGateway",
        "ec2:DeleteNatGateway",
        "ec2:AllocateAddress",
        "ec2:ReleaseAddress",
        "ec2:CreateRouteTable",
        "ec2:DeleteRouteTable",
        "ec2:CreateRoute",
        "ec2:DeleteRoute",
        "ec2:AssociateRouteTable",
        "ec2:DisassociateRouteTable",
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:CreateTags",
        "ec2:DeleteTags",
        "ec2:CreateKeyPair",
        "ec2:DeleteKeyPair",
        "ec2:CreateLaunchTemplate",
        "ec2:DeleteLaunchTemplate"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ELBPermissions",
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AutoScalingPermissions",
      "Effect": "Allow",
      "Action": [
        "autoscaling:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3Permissions",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:ListBucket",
        "s3:GetBucketPolicy",
        "s3:PutBucketPolicy",
        "s3:GetBucketVersioning",
        "s3:PutBucketVersioning",
        "s3:GetEncryptionConfiguration",
        "s3:PutEncryptionConfiguration",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::my-app-*",
        "arn:aws:s3:::my-app-*/*"
      ]
    },
    {
      "Sid": "IAMPermissions",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:PassRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:CreateInstanceProfile",
        "iam:DeleteInstanceProfile",
        "iam:AddRoleToInstanceProfile",
        "iam:RemoveRoleFromInstanceProfile",
        "iam:GetInstanceProfile",
        "iam:ListInstanceProfilesForRole"
      ],
      "Resource": "*"
    }
  ]
}
```

---

*Continued in next section...*
