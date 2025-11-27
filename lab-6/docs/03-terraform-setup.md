# Terraform Infrastructure Provisioning Guide

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [File Structure](#file-structure)
- [Configuration Files Explained](#configuration-files-explained)
- [Step-by-Step Execution](#step-by-step-execution)
- [Understanding the Infrastructure](#understanding-the-infrastructure)
- [Troubleshooting](#troubleshooting)

---

## Overview

This guide explains how to use Terraform to provision AWS infrastructure including VPC, subnets, security groups, and EC2 instances, while automatically generating Ansible inventory.

**What Terraform Will Create:**
- 1 VPC with CIDR 10.0.0.0/16
- 2 Public subnets (10.0.1.0/24, 10.0.2.0/24)
- 1 Internet Gateway
- Route tables and associations
- Security groups (SSH, HTTP, HTTPS)
- SSH key pair
- EC2 instances (configurable count)
- Ansible inventory file (automatic)

---

## Prerequisites

### 1. Install Terraform

```bash
# Download Terraform (Linux)
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify installation
terraform --version
```

### 2. AWS Credentials

**Option A: AWS CLI Configuration**
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region, Output format
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

**Option C: Terraform Variables** (in `terraform.tfvars`)
```hcl
aws_access_key = "your-access-key"
aws_secret_key = "your-secret-key"
```

### 3. SSH Key Pair

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/terraform-key -N ""

# This creates:
# ~/.ssh/terraform-key      (private key - keep secure!)
# ~/.ssh/terraform-key.pub  (public key - uploaded to AWS)
```

---

## File Structure

```
terraform/
├── main.tf                    # Main infrastructure configuration
├── variables.tf               # Variable definitions
├── outputs.tf                 # Output definitions
├── terraform.tfvars.example   # Example variable values
├── inventory_template.tpl     # Ansible inventory template
├── terraform.tfstate          # State file (auto-generated)
└── .terraform/                # Provider plugins (auto-generated)
```

---

## Configuration Files Explained

### main.tf

The main configuration file that defines all AWS resources.

**Key Sections:**

1. **Provider Configuration**
```hcl
provider "aws" {
  region = var.aws_region
}
```
- Specifies AWS as the cloud provider
- Sets the region from variables

2. **VPC (Virtual Private Cloud)**
```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "${var.project_name}-vpc"
  }
}
```
- Creates isolated network in AWS
- CIDR block defines IP range (e.g., 10.0.0.0/16)
- DNS enabled for hostname resolution

3. **Subnets**
```hcl
resource "aws_subnet" "public" {
  count                   = var.subnet_count
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "${var.project_name}-public-${count.index + 1}"
  }
}
```
- Creates multiple subnets using `count`
- `cidrsubnet()` automatically calculates subnet CIDRs
- Public IPs assigned automatically

4. **Internet Gateway**
```hcl
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "${var.project_name}-igw"
  }
}
```
- Allows internet access for VPC
- Required for public subnets

5. **Security Groups**
```hcl
resource "aws_security_group" "web" {
  name        = "${var.project_name}-web-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.main.id
  
  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }
  
  # HTTP access
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```
- Firewall rules for EC2 instances
- Ingress: inbound traffic rules
- Egress: outbound traffic rules

6. **EC2 Instances**
```hcl
resource "aws_instance" "web" {
  count                  = var.instance_count
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.web.id]
  subnet_id              = aws_subnet.public[count.index % var.subnet_count].id
  
  tags = {
    Name        = "${var.project_name}-web-${count.index + 1}"
    Role        = "webserver"
    Environment = var.environment
  }
}
```
- Creates multiple instances using `count`
- Uses latest Ubuntu AMI (auto-discovered)
- Distributes across subnets using modulo operator
- Tags for organization and dynamic inventory

7. **Dynamic Inventory Generation**
```hcl
resource "local_file" "ansible_inventory" {
  content = templatefile("${path.module}/inventory_template.tpl", {
    webservers = aws_instance.web
  })
  filename = "${path.module}/../ansible/inventory/hosts.ini"
  
  depends_on = [aws_instance.web]
}
```
- Automatically creates Ansible inventory
- Uses template file for formatting
- Waits for instances to be created

### variables.tf

Defines all configurable parameters.

**Variable Types:**

```hcl
# String variable
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

# Number variable
variable "instance_count" {
  description = "Number of EC2 instances to create"
  type        = number
  default     = 2
}

# List variable
variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# Map variable
variable "instance_tags" {
  description = "Tags for EC2 instances"
  type        = map(string)
  default = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
```

**Why Use Variables?**
- ✅ Reusability across environments
- ✅ Easy to customize without editing main code
- ✅ Type validation
- ✅ Default values for convenience

### outputs.tf

Exports important information after infrastructure creation.

```hcl
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "instance_public_ips" {
  description = "Public IP addresses of EC2 instances"
  value       = aws_instance.web[*].public_ip
}

output "instance_private_ips" {
  description = "Private IP addresses of EC2 instances"
  value       = aws_instance.web[*].private_ip
}
```

**Uses:**
- View with `terraform output`
- Pass to other tools (Ansible, scripts)
- Use in automation pipelines

### inventory_template.tpl

Template for generating Ansible inventory.

```hcl
[webservers]
%{ for instance in webservers ~}
${instance.tags.Name} ansible_host=${instance.public_ip} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/terraform-key
%{ endfor ~}

[all:vars]
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
```

**Template Syntax:**
- `%{ for ... ~}`: Loop through instances
- `${variable}`: Interpolate values
- `~`: Trim whitespace

---

## Step-by-Step Execution

### Step 1: Initialize Terraform

```bash
cd terraform
terraform init
```

**What happens:**
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.23.0...
- Installed hashicorp/aws v5.23.0

Terraform has been successfully initialized!
```

**Behind the scenes:**
- Downloads AWS provider plugin
- Creates `.terraform/` directory
- Creates `.terraform.lock.hcl` (locks provider versions)
- Initializes backend (local or remote state storage)

### Step 2: Validate Configuration

```bash
terraform validate
```

**Output:**
```
Success! The configuration is valid.
```

**Checks:**
- Syntax errors
- Invalid resource references
- Type mismatches

### Step 3: Format Code (Optional)

```bash
terraform fmt
```

**What it does:**
- Formats `.tf` files to canonical style
- Ensures consistent formatting
- Shows which files were modified

### Step 4: Plan Infrastructure

```bash
terraform plan
```

**Output example:**
```
Terraform will perform the following actions:

  # aws_vpc.main will be created
  + resource "aws_vpc" "main" {
      + cidr_block           = "10.0.0.0/16"
      + enable_dns_hostnames = true
      + id                   = (known after apply)
    }

  # aws_instance.web[0] will be created
  + resource "aws_instance" "web" {
      + ami                    = "ami-0c55b159cbfafe1f0"
      + instance_type          = "t2.micro"
      + public_ip              = (known after apply)
    }

Plan: 12 to add, 0 to change, 0 to destroy.
```

**What to review:**
- Resources being created (+)
- Resources being modified (~)
- Resources being destroyed (-)
- Total count of changes

### Step 5: Apply Configuration

```bash
terraform apply
```

**Interactive mode:**
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes
```

**Auto-approve mode:**
```bash
terraform apply -auto-approve
```

**Execution output:**
```
aws_vpc.main: Creating...
aws_vpc.main: Creation complete after 2s [id=vpc-0abc123]
aws_subnet.public[0]: Creating...
aws_subnet.public[0]: Creation complete after 1s [id=subnet-0def456]
aws_instance.web[0]: Creating...
aws_instance.web[0]: Still creating... [10s elapsed]
aws_instance.web[0]: Creation complete after 32s [id=i-0123abc]

Apply complete! Resources: 12 added, 0 changed, 0 destroyed.

Outputs:

instance_public_ips = [
  "54.123.45.67",
  "54.123.45.68",
]
vpc_id = "vpc-0abc123"
```

### Step 6: View Outputs

```bash
# View all outputs
terraform output

# View specific output
terraform output instance_public_ips

# Output as JSON
terraform output -json
```

### Step 7: Verify Inventory Generation

```bash
cat ../ansible/inventory/hosts.ini
```

**Expected output:**
```ini
[webservers]
terraform-web-1 ansible_host=54.123.45.67 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/terraform-key
terraform-web-2 ansible_host=54.123.45.68 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/terraform-key

[all:vars]
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
```

---

## Understanding the Infrastructure

### Resource Dependencies

Terraform automatically handles dependencies:

```
aws_vpc.main
    │
    ├─> aws_subnet.public (depends on VPC)
    │       │
    │       └─> aws_instance.web (depends on subnet)
    │
    ├─> aws_internet_gateway.main (depends on VPC)
    │       │
    │       └─> aws_route_table.public (depends on IGW)
    │
    └─> aws_security_group.web (depends on VPC)
            │
            └─> aws_instance.web (depends on SG)
```

**Terraform creates resources in correct order automatically!**

### State Management

**terraform.tfstate file:**
```json
{
  "version": 4,
  "terraform_version": "1.6.0",
  "resources": [
    {
      "type": "aws_instance",
      "name": "web",
      "instances": [
        {
          "attributes": {
            "id": "i-0123abc",
            "public_ip": "54.123.45.67"
          }
        }
      ]
    }
  ]
}
```

**Important:**
- ⚠️ Contains sensitive data (IPs, IDs)
- ⚠️ Should be in `.gitignore`
- ✅ Use remote backend (S3) for teams
- ✅ Enable state locking to prevent conflicts

### Cost Estimation

**Resources created and approximate costs:**

| Resource | Count | Monthly Cost (approx) |
|----------|-------|----------------------|
| VPC | 1 | $0 (free) |
| Subnets | 2 | $0 (free) |
| Internet Gateway | 1 | $0 (free) |
| EC2 t2.micro | 2 | $16.80 ($8.40 each) |
| **Total** | | **~$17/month** |

**Note:** Costs vary by region and usage. Use AWS Cost Calculator for accurate estimates.

---

## Troubleshooting

### Error: "No valid credential sources found"

**Cause:** AWS credentials not configured

**Solution:**
```bash
aws configure
# OR
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

### Error: "Error launching source instance: InvalidKeyPair.NotFound"

**Cause:** SSH key not uploaded to AWS

**Solution:**
```bash
# Ensure public key exists
ls ~/.ssh/terraform-key.pub

# Terraform will create the key pair automatically
# Just make sure the path in variables.tf is correct
```

### Error: "Error creating VPC: VpcLimitExceeded"

**Cause:** AWS account VPC limit reached (default: 5 per region)

**Solution:**
- Delete unused VPCs
- Request limit increase from AWS Support
- Use different region

### Error: "Error: Duplicate resource"

**Cause:** Resource defined multiple times

**Solution:**
```bash
# Find duplicate resources
grep -r "resource \"aws_instance\" \"web\"" .

# Ensure each resource has unique name
```

### Instances created but can't SSH

**Cause:** Security group or key issues

**Debugging:**
```bash
# 1. Check security group allows SSH from your IP
terraform output security_group_id

# 2. Verify key permissions
chmod 400 ~/.ssh/terraform-key

# 3. Test SSH connection
ssh -i ~/.ssh/terraform-key ubuntu@$(terraform output -raw instance_public_ips | jq -r '.[0]')

# 4. Check instance status
aws ec2 describe-instance-status --instance-ids $(terraform output -raw instance_ids | jq -r '.[0]')
```

---

## Best Practices

### 1. Use Variables for Everything Configurable

❌ **Bad:**
```hcl
resource "aws_instance" "web" {
  instance_type = "t2.micro"
  ami           = "ami-0c55b159cbfafe1f0"
}
```

✅ **Good:**
```hcl
resource "aws_instance" "web" {
  instance_type = var.instance_type
  ami           = data.aws_ami.ubuntu.id
}
```

### 2. Use Data Sources for Dynamic Values

```hcl
# Automatically get latest Ubuntu AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}
```

### 3. Tag Everything

```hcl
tags = {
  Name        = "${var.project_name}-web-${count.index + 1}"
  Environment = var.environment
  ManagedBy   = "terraform"
  Project     = var.project_name
  CostCenter  = var.cost_center
}
```

### 4. Use Remote State for Teams

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### 5. Use Workspaces for Environments

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch workspace
terraform workspace select dev

# List workspaces
terraform workspace list
```

---

## Next Steps

Now that infrastructure is provisioned:

1. **Verify instances are running:**
   ```bash
   aws ec2 describe-instances --filters "Name=tag:Name,Values=*web*" --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress]'
   ```

2. **Check inventory file:**
   ```bash
   cat ../ansible/inventory/hosts.ini
   ```

3. **Proceed to Ansible configuration:**
   - [Ansible Setup Guide](04-ansible-setup.md)

---

[← Previous: Architecture](02-architecture.md) | [Next: Ansible Setup →](04-ansible-setup.md)
