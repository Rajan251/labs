# Production-Ready Terraform Project - Step-by-Step Execution Guide

## Overview

This guide provides **exact steps** to deploy the production-ready Terraform AWS infrastructure. Follow these steps in order for a successful deployment.

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Ubuntu 20.04+ server (or WSL2 on Windows)
- [ ] AWS account with admin access
- [ ] AWS CLI installed and configured
- [ ] Terraform 1.6+ installed
- [ ] Git installed
- [ ] 2GB+ RAM, 20GB+ disk space
- [ ] Internet connectivity

---

## Phase 1: Environment Setup (15-20 minutes)

### Step 1: Update System and Install Tools

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget unzip git jq software-properties-common gnupg ca-certificates

# Verify installations
curl --version
git --version
jq --version
```

**What this does:** Prepares your Ubuntu system with required tools for Terraform and AWS CLI.

---

### Step 2: Install AWS CLI

```bash
# Download AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Unzip
unzip awscliv2.zip

# Install
sudo ./aws/install

# Verify installation
aws --version
# Expected: aws-cli/2.x.x Python/3.x.x Linux/x.x.x

# Cleanup
rm -rf aws awscliv2.zip
```

**What this does:** Installs the latest AWS CLI for managing AWS resources.

---

### Step 3: Configure AWS Credentials

```bash
# Interactive configuration
aws configure

# You'll be prompted for:
# AWS Access Key ID: [Enter your access key]
# AWS Secret Access Key: [Enter your secret key]
# Default region name: us-east-1
# Default output format: json
```

**Alternative: Manual configuration**

```bash
# Create credentials file
mkdir -p ~/.aws

cat > ~/.aws/credentials << 'EOF'
[default]
aws_access_key_id = YOUR_ACCESS_KEY_HERE
aws_secret_access_key = YOUR_SECRET_KEY_HERE

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

# Secure the files
chmod 600 ~/.aws/credentials
chmod 600 ~/.aws/config
```

**What this does:** Configures AWS credentials so Terraform can create resources in your AWS account.

---

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

# Test permissions
aws ec2 describe-regions --output table

# List S3 buckets (should work even if empty)
aws s3 ls
```

**What this does:** Verifies your AWS credentials are working correctly.

---

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
# Expected: Terraform v1.6.x or later

# Enable tab completion (optional)
terraform -install-autocomplete
```

**What this does:** Installs Terraform, the infrastructure-as-code tool.

---

## Phase 2: Project Setup (10 minutes)

### Step 6: Create Project Directory

```bash
# Navigate to your workspace
cd ~/Documents/labs/lab-3

# Or create a new project
mkdir -p ~/terraform-aws-project
cd ~/terraform-aws-project

# Verify you're in the right directory
pwd
```

**What this does:** Sets up your working directory for the Terraform project.

---

### Step 7: Create Backend Resources (S3 + DynamoDB)

This is a **one-time setup** for storing Terraform state remotely.

```bash
# Make script executable
chmod +x scripts/create-backend.sh

# Run the backend creation script
./scripts/create-backend.sh

# The script will:
# 1. Create S3 bucket for state storage
# 2. Enable versioning on the bucket
# 3. Enable encryption (AES256)
# 4. Block public access
# 5. Create DynamoDB table for state locking
```

**Expected output:**
```
Creating Terraform backend resources...
Region: us-east-1
Profile: default
Bucket: terraform-state-123456789012
DynamoDB Table: terraform-state-lock

✓ Bucket created
✓ Versioning enabled
✓ Encryption enabled
✓ Public access blocked
✓ Table created

Backend resources created successfully!

Add this to your backend.tf:

terraform {
  backend "s3" {
    bucket         = "terraform-state-123456789012"
    key            = "envs/ENV_NAME/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
    profile        = "default"
  }
}
```

**What this does:** Creates secure remote storage for Terraform state files, enabling team collaboration and state locking.

---

### Step 8: Create Project Structure

```bash
# Create directory structure
mkdir -p envs/dev
mkdir -p modules/{vpc,ec2-asg,alb,s3}
mkdir -p scripts

# Verify structure
tree -L 2
```

**Expected output:**
```
.
├── envs
│   └── dev
├── modules
│   ├── alb
│   ├── ec2-asg
│   ├── s3
│   └── vpc
└── scripts
```

**What this does:** Creates organized directory structure for modules and environments.

---

## Phase 3: Create Terraform Configuration (20-30 minutes)

### Step 9: Create Simple Dev Environment

Let's start with a **minimal working example** for dev environment.

**Create `envs/dev/backend.tf`:**

```bash
cat > envs/dev/backend.tf << 'EOF'
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "terraform-state-123456789012"  # Replace with your bucket name
    key            = "envs/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
    profile        = "default"
  }
}
EOF
```

**What this does:** Configures Terraform version, AWS provider, and remote state backend.

---

**Create `envs/dev/main.tf`:**

```bash
cat > envs/dev/main.tf << 'EOF'
provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "Terraform"
      Project     = var.project_name
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.environment}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.environment}-igw"
  }
}

# Public Subnet
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.environment}-public-${count.index + 1}"
  }
}

# Private Subnet
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 11}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.environment}-private-${count.index + 1}"
  }
}

# NAT Gateway
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "${var.environment}-nat-eip"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "${var.environment}-nat"
  }

  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.environment}-public-rt"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "${var.environment}-private-rt"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Security Groups
resource "aws_security_group" "alb" {
  name_prefix = "${var.environment}-alb-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-alb-sg"
  }
}

resource "aws_security_group" "app" {
  name_prefix = "${var.environment}-app-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-app-sg"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name = "${var.environment}-alb"
  }
}

resource "aws_lb_target_group" "app" {
  name     = "${var.environment}-app-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
  }

  tags = {
    Name = "${var.environment}-app-tg"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# Launch Template
resource "aws_launch_template" "app" {
  name_prefix   = "${var.environment}-app-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  vpc_security_group_ids = [aws_security_group.app.id]

  user_data = base64encode(<<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "<h1>Hello from $(hostname -f)</h1>" > /var/www/html/index.html
              EOF
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.environment}-app-instance"
    }
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "app" {
  name                = "${var.environment}-app-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  target_group_arns   = [aws_lb_target_group.app.arn]
  health_check_type   = "ELB"
  min_size            = 2
  max_size            = 4
  desired_capacity    = 2

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.environment}-app-asg"
    propagate_at_launch = true
  }
}
EOF
```

**What this does:** Creates complete AWS infrastructure including VPC, subnets, ALB, and Auto Scaling Group.

---

**Create `envs/dev/variables.tf`:**

```bash
cat > envs/dev/variables.tf << 'EOF'
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile"
  type        = string
  default     = "default"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "myapp"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}
EOF
```

**What this does:** Defines input variables for customization.

---

**Create `envs/dev/outputs.tf`:**

```bash
cat > envs/dev/outputs.tf << 'EOF'
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "ALB URL"
  value       = "http://${aws_lb.main.dns_name}"
}
EOF
```

**What this does:** Defines outputs to display after deployment.

---

## Phase 4: Deploy Infrastructure (10-15 minutes)

### Step 10: Initialize Terraform

```bash
# Navigate to dev environment
cd envs/dev

# Initialize Terraform
terraform init

# Expected output:
# Initializing the backend...
# Successfully configured the backend "s3"!
# Initializing provider plugins...
# - Finding hashicorp/aws versions matching "~> 5.0"...
# - Installing hashicorp/aws v5.x.x...
# Terraform has been successfully initialized!
```

**What this does:**
- Downloads AWS provider plugin
- Configures S3 backend
- Prepares working directory

---

### Step 11: Validate Configuration

```bash
# Format code
terraform fmt

# Validate configuration
terraform validate

# Expected output:
# Success! The configuration is valid.
```

**What this does:** Checks for syntax errors and validates configuration.

---

### Step 12: Create Execution Plan

```bash
# Create plan
terraform plan -out=tfplan

# Review the output carefully!
# Look for:
# Plan: X to add, 0 to change, 0 to destroy.
```

**What this does:** Shows what Terraform will create without actually creating it.

**Expected resources to be created:**
- 1 VPC
- 1 Internet Gateway
- 1 NAT Gateway
- 2 Public subnets
- 2 Private subnets
- 2 Route tables
- 4 Route table associations
- 2 Security groups
- 1 Application Load Balancer
- 1 Target group
- 1 Listener
- 1 Launch template
- 1 Auto Scaling Group

**Total: ~20 resources**

---

### Step 13: Apply Configuration

```bash
# Apply the plan
terraform apply tfplan

# This will take 5-10 minutes
# Watch for:
# - VPC creation
# - Subnet creation
# - NAT Gateway creation (slowest, ~2-3 minutes)
# - ALB creation
# - EC2 instances launching

# Expected final output:
# Apply complete! Resources: 20 added, 0 changed, 0 destroyed.
#
# Outputs:
# alb_dns_name = "dev-alb-1234567890.us-east-1.elb.amazonaws.com"
# alb_url = "http://dev-alb-1234567890.us-east-1.elb.amazonaws.com"
# vpc_id = "vpc-0123456789abcdef0"
```

**What this does:** Creates all AWS resources defined in your Terraform configuration.

---

## Phase 5: Verify Deployment (5 minutes)

### Step 14: View Outputs

```bash
# View all outputs
terraform output

# Get specific output
terraform output alb_dns_name

# Get URL
terraform output -raw alb_url
```

**What this does:** Displays important information about deployed resources.

---

### Step 15: Test the Application

```bash
# Get ALB URL
ALB_URL=$(terraform output -raw alb_url)

# Test the application (wait 2-3 minutes for instances to be healthy)
curl $ALB_URL

# Expected output:
# <h1>Hello from ip-10-0-11-xxx.ec2.internal</h1>

# Test multiple times to see load balancing
for i in {1..5}; do
  curl $ALB_URL
  echo ""
done
```

**What this does:** Verifies your application is running and load balancer is working.

---

### Step 16: Verify AWS Resources

```bash
# Check VPC
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=dev-vpc" --query 'Vpcs[0].VpcId'

# Check EC2 instances
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=dev-app-asg" \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PrivateIpAddress]' \
  --output table

# Check ALB
aws elbv2 describe-load-balancers \
  --names dev-alb \
  --query 'LoadBalancers[0].[LoadBalancerName,DNSName,State.Code]' \
  --output table

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw target_group_arn 2>/dev/null || echo "")

# Check Auto Scaling Group
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names dev-app-asg \
  --query 'AutoScalingGroups[0].[AutoScalingGroupName,DesiredCapacity,MinSize,MaxSize]' \
  --output table
```

**What this does:** Verifies resources in AWS Console via CLI.

---

## Phase 6: Make Changes (Optional)

### Step 17: Modify Infrastructure

Let's scale up the application:

```bash
# Edit variables
cat > terraform.tfvars << 'EOF'
instance_type = "t3.small"  # Upgrade from t3.micro
EOF

# Plan the change
terraform plan -out=tfplan

# Review changes
# Should show:
# Plan: 0 to add, 1 to change, 0 to destroy.

# Apply
terraform apply tfplan
```

**What this does:** Demonstrates how to make infrastructure changes safely.

---

## Phase 7: Cleanup (5 minutes)

### Step 18: Destroy Infrastructure

**⚠️ WARNING: This will delete all resources!**

```bash
# Review what will be destroyed
terraform plan -destroy

# Destroy resources
terraform destroy

# Type 'yes' when prompted

# This will take 5-10 minutes
# Resources are destroyed in reverse dependency order
```

**What this does:** Removes all AWS resources created by Terraform.

---

## Production Deployment Workflow

For production, use this workflow:

### 1. Create Production Environment

```bash
# Copy dev to prod
cp -r envs/dev envs/prod

# Edit envs/prod/backend.tf
# Change key to: "envs/prod/terraform.tfstate"

# Edit envs/prod/variables.tf
# Change environment default to: "prod"

# Create terraform.tfvars for prod
cat > envs/prod/terraform.tfvars << 'EOF'
environment   = "prod"
instance_type = "t3.small"
aws_profile   = "terraform"
EOF
```

### 2. Use Helper Scripts

```bash
# Initialize
./scripts/init.sh prod

# Plan
./scripts/plan.sh prod

# Review plan carefully!

# Apply
./scripts/apply.sh prod
```

### 3. Enable Modern Practices

For production, implement:

1. **OIDC Authentication** (see modern-production-practices.md)
2. **GitOps with Atlantis** (PR-based workflow)
3. **Security Scanning** (tfsec, Checkov)
4. **Cost Estimation** (Infracost)
5. **Multi-region** (for DR)

---

## Troubleshooting

### Issue: "Error acquiring state lock"

**Solution:**
```bash
# Force unlock (use with caution!)
terraform force-unlock <LOCK_ID>
```

### Issue: "InsufficientInstanceCapacity"

**Solution:**
```bash
# Change availability zone or instance type
# Edit variables.tf and change instance_type
```

### Issue: ALB health checks failing

**Solution:**
```bash
# Wait 2-3 minutes for instances to become healthy
# Check target health
aws elbv2 describe-target-health --target-group-arn <ARN>

# Check security groups allow ALB → EC2 traffic
```

### Issue: "Bucket already exists"

**Solution:**
```bash
# Use a unique bucket name
# Edit backend.tf and add timestamp or account ID to bucket name
```

---

## Cost Estimate

Running this infrastructure will cost approximately:

| Resource | Monthly Cost (us-east-1) |
|----------|-------------------------|
| 2x t3.micro EC2 | ~$15 |
| 1x NAT Gateway | ~$32 |
| 1x ALB | ~$22 |
| Data transfer | ~$5 |
| **Total** | **~$74/month** |

**To minimize costs:**
- Use t3.micro for dev
- Destroy when not in use
- Use single NAT gateway for dev

---

## Next Steps

1. ✅ **Review** the deployment
2. ✅ **Test** the application
3. ✅ **Implement** modern practices (OIDC, GitOps, security scanning)
4. ✅ **Add** monitoring and alerting
5. ✅ **Set up** CI/CD pipeline
6. ✅ **Document** your changes

---

## Summary

You've successfully:

- ✅ Set up Ubuntu environment with Terraform and AWS CLI
- ✅ Created remote state backend (S3 + DynamoDB)
- ✅ Deployed complete AWS infrastructure (VPC, ALB, ASG)
- ✅ Verified deployment with tests
- ✅ Learned how to make changes and destroy resources

**Your infrastructure is now production-ready!**

For modern production practices, see:
- [Modern Production Practices](modern-production-practices.md)
- [Modern vs Traditional Comparison](modern-vs-traditional.md)
