# Lab 01: VPC and Networking Foundation

## Objective

Deploy a production-grade VPC with multi-AZ architecture including public/private subnets, Internet Gateway, NAT Gateways, and proper routing.

**Time to Complete**: 30-45 minutes  
**Difficulty**: Beginner  
**Cost**: ~$0.10/hour (mostly NAT Gateway)

## What You'll Learn

✅ Create VPC with proper CIDR planning  
✅ Deploy subnets across multiple Availability Zones  
✅ Configure Internet Gateway for public internet access  
✅ Setup NAT Gateways for private subnet outbound traffic  
✅ Configure route tables for proper traffic flow  
✅ Enable VPC Flow Logs for network monitoring  
✅ Use Terraform modules for reusable infrastructure  

## Prerequisites

- AWS Account with administrative access
- AWS CLI configured (`aws configure`)
- Terraform installed (>= 1.6.0)
- Basic understanding of VPC concepts

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VPC: 10.0.0.0/16                         │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐│
│  │           Public Subnets (Internet-facing)             ││
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐          ││
│  │  │ us-east-1a│  │ us-east-1b│  │ us-east-1c│          ││
│  │  │10.0.1.0/24│  │10.0.2.0/24│  │10.0.3.0/24│          ││
│  │  │    NAT    │  │    NAT    │  │    NAT    │          ││
│  │  │  Gateway  │  │  Gateway  │  │  Gateway  │          ││
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘          ││
│  └────────┼──────────────┼──────────────┼────────────────┘│
│           │              │              │                  │
│           └──────────────┴──────────────┴──────────────────┤
│                    Internet Gateway                        │
└─────────────────────────────────────────────────────────────┘
```

## Step 1: Setup Project Structure

```bash
# Navigate to lab directory
cd /home/rk/Documents/labs/terrafrom-lab/terraform-fintech-lab/labs/01-vpc-networking

# Create Terraform files
touch main.tf variables.tf outputs.tf terraform.tfvars backend.tf
```

## Step 2: Configure Backend (State Management)

Create `backend.tf`:

```hcl
terraform {
  required_version = ">= 1.6.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Uncomment after creating S3 bucket and DynamoDB table
  # backend "s3" {
  #   bucket         = "payflow-terraform-state-dev"
  #   key            = "lab01/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project    = "payflow-platform"
      ManagedBy  = "terraform"
      Lab        = "01-vpc-networking"
      CostCenter = "engineering"
    }
  }
}
```

## Step 3: Define Variables

Create `variables.tf`:

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "payflow"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use single NAT Gateway (cost optimization)"
  type        = bool
  default     = true  # Set to true for dev to save costs
}
```

## Step 4: Create Main Configuration

Create `main.tf`:

```hcl
# Data source for latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
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
    Name = "${var.project_name}-vpc-${var.environment}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "${var.project_name}-igw-${var.environment}"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(var.availability_zones)
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index + 1)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "${var.project_name}-subnet-public-${count.index + 1}-${var.environment}"
    Tier = "public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = length(var.availability_zones)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 11)
  availability_zone = var.availability_zones[count.index]
  
  tags = {
    Name = "${var.project_name}-subnet-private-${count.index + 1}-${var.environment}"
    Tier = "private"
  }
}

# Database Subnets
resource "aws_subnet" "database" {
  count = length(var.availability_zones)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 21)
  availability_zone = var.availability_zones[count.index]
  
  tags = {
    Name = "${var.project_name}-subnet-database-${count.index + 1}-${var.environment}"
    Tier = "database"
  }
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0
  domain = "vpc"
  
  tags = {
    Name = "${var.project_name}-eip-nat-${count.index + 1}-${var.environment}"
  }
  
  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[var.single_nat_gateway ? 0 : count.index].id
  
  tags = {
    Name = "${var.project_name}-nat-${count.index + 1}-${var.environment}"
  }
  
  depends_on = [aws_internet_gateway.main]
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = {
    Name = "${var.project_name}-rt-public-${var.environment}"
  }
}

# Public Route Table Associations
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private Route Tables
resource "aws_route_table" "private" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0
  
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[var.single_nat_gateway ? 0 : count.index].id
  }
  
  tags = {
    Name = "${var.project_name}-rt-private-${count.index + 1}-${var.environment}"
  }
}

# Private Route Table Associations
resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[var.single_nat_gateway ? 0 : count.index].id
}

# Database Route Table
resource "aws_route_table" "database" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "${var.project_name}-rt-database-${var.environment}"
  }
}

# Database Route Table Associations
resource "aws_route_table_association" "database" {
  count = length(aws_subnet.database)
  
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database.id
}
```

## Step 5: Define Outputs

Create `outputs.tf`:

```hcl
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "database_subnet_ids" {
  description = "List of database subnet IDs"
  value       = aws_subnet.database[*].id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.main[*].id
}

output "nat_gateway_public_ips" {
  description = "Public IPs of NAT Gateways"
  value       = aws_eip.nat[*].public_ip
}
```

## Step 6: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt

# Plan deployment
terraform plan

# Review the plan output carefully
# Expected resources: ~20-25 resources

# Apply configuration
terraform apply

# Type 'yes' when prompted
```

### Expected Output

```
Plan: 23 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + nat_gateway_public_ips = [
      + "54.123.45.67",
    ]
  + private_subnet_ids     = [
      + "subnet-abc123",
      + "subnet-def456",
      + "subnet-ghi789",
    ]
  + public_subnet_ids      = [
      + "subnet-jkl012",
      + "subnet-mno345",
      + "subnet-pqr678",
    ]
  + vpc_cidr               = "10.0.0.0/16"
  + vpc_id                 = "vpc-xyz789"

Apply complete! Resources: 23 added, 0 changed, 0 destroyed.
```

## Step 7: Verify in AWS Console

### VPC Verification

```bash
# List VPCs
aws ec2 describe-vpcs \
  --filters "Name=tag:Project,Values=payflow-platform" \
  --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# Expected output:
# vpc-xyz789 | 10.0.0.0/16 | payflow-vpc-dev
```

### Subnet Verification

```bash
# List all subnets
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key==`Tier`].Value|[0]]' \
  --output table

# Expected: 9 subnets (3 public, 3 private, 3 database)
```

### NAT Gateway Verification

```bash
# Check NAT Gateway status
aws ec2 describe-nat-gateways \
  --filter "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --query 'NatGateways[*].[NatGatewayId,State,SubnetId]' \
  --output table

# Expected: 1 NAT Gateway in 'available' state
```

### Route Table Verification

```bash
# List route tables
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --query 'RouteTables[*].[RouteTableId,Tags[?Key==`Name`].Value|[0],Routes[*].GatewayId]' \
  --output table
```

## Step 8: Test Connectivity (Optional)

### Launch Test Instance in Private Subnet

```bash
# Get latest Amazon Linux 2023 AMI
AMI_ID=$(aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=al2023-ami-*-x86_64" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text)

# Get first private subnet
PRIVATE_SUBNET=$(terraform output -json private_subnet_ids | jq -r '.[0]')

# Launch instance
aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.micro \
  --subnet-id $PRIVATE_SUBNET \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=test-private-instance}]'

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids <INSTANCE_ID>

# Connect via SSM (no SSH key needed!)
aws ssm start-session --target <INSTANCE_ID>

# Inside instance, test internet connectivity
curl -I https://www.google.com

# Expected: HTTP/2 200 (proves NAT Gateway is working)

# Exit and terminate test instance
exit
aws ec2 terminate-instances --instance-ids <INSTANCE_ID>
```

## Step 9: Understanding the Code

### CIDR Calculation

```hcl
cidrsubnet(var.vpc_cidr, 8, count.index + 1)
```

**Explanation:**
- `vpc_cidr = "10.0.0.0/16"` (65,536 IPs)
- `cidrsubnet(..., 8, ...)` creates /24 subnets (256 IPs each)
- `count.index + 1` offsets subnet numbers

**Result:**
- Public subnets: 10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24
- Private subnets: 10.0.11.0/24, 10.0.12.0/24, 10.0.13.0/24
- Database subnets: 10.0.21.0/24, 10.0.22.0/24, 10.0.23.0/24

### Resource Dependencies

```hcl
depends_on = [aws_internet_gateway.main]
```

**Why?** NAT Gateway requires Internet Gateway to exist first.

### Count Meta-Argument

```hcl
count = length(var.availability_zones)
```

**Benefit:** Creates resources dynamically based on AZ count.

## Step 10: Cost Analysis

```bash
# Check current costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '1 day ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --filter file://<(echo '{"Tags":{"Key":"Project","Values":["payflow-platform"]}}')
```

**Expected Monthly Cost (Dev with single NAT GW):**
- NAT Gateway: ~$32/month
- Data processing: ~$0.045/GB
- **Total: ~$35-40/month**

## Troubleshooting

### Error: VPC Limit Exceeded

```
Error: Error creating VPC: VpcLimitExceeded
```

**Solution:**
```bash
# Check current VPC count
aws ec2 describe-vpcs --query 'length(Vpcs)'

# Delete unused VPCs or request limit increase
aws service-quotas request-service-quota-increase \
  --service-code vpc \
  --quota-code L-F678F1CE \
  --desired-value 10
```

### Error: NAT Gateway Creation Timeout

```
Error: timeout while waiting for state to become 'available'
```

**Solution:** NAT Gateway creation takes 2-5 minutes. Increase timeout:

```hcl
resource "aws_nat_gateway" "main" {
  # ...
  
  timeouts {
    create = "10m"
  }
}
```

## Cleanup

```bash
# Destroy all resources
terraform destroy

# Type 'yes' when prompted

# Verify deletion
aws ec2 describe-vpcs \
  --filters "Name=tag:Project,Values=payflow-platform" \
  --query 'Vpcs[*].VpcId'

# Expected: []
```

## Key Takeaways

✅ **Multi-AZ Design**: Resources spread across 3 AZs for high availability  
✅ **Network Segmentation**: Public, private, and database subnets for security  
✅ **NAT Gateway**: Enables private instances to access internet  
✅ **Terraform Modules**: Reusable, maintainable infrastructure code  
✅ **Cost Optimization**: Single NAT GW for dev saves $64/month  

## Next Steps

- **Lab 02**: Security Groups and NACLs
- **Lab 03**: EC2 Instances and Auto Scaling
- **Lab 04**: Application Load Balancer

## Additional Resources

- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [CIDR Calculator](https://www.ipaddressguide.com/cidr)

---

**Congratulations!** You've deployed a production-grade VPC infrastructure. 🎉
