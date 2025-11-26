# Terraform AWS Infrastructure Guide - Part 5

## 17. Troubleshooting

### Common Problems & Solutions

| Error | Root Cause | Solution |
|-------|-----------|----------|
| `Error: Failed to query available provider packages` | Network/registry issue | Check internet connectivity; verify Terraform registry access |
| `Error: error configuring S3 Backend: no valid credential sources` | Missing AWS credentials | Run `aws configure` or set `AWS_ACCESS_KEY_ID` env var |
| `Error: Error acquiring the state lock` | Another process holds lock | Wait for other operation to complete; force-unlock if stuck: `terraform force-unlock <LOCK_ID>` |
| `Error: Error launching source instance: InsufficientInstanceCapacity` | AWS capacity issue in AZ | Change `availability_zone` or `instance_type`; request limit increase |
| `Error: creating Application Load Balancer: DuplicateLoadBalancerName` | ALB name already exists | Use unique name or import existing: `terraform import aws_lb.main <ARN>` |
| `Error: creating S3 Bucket: BucketAlreadyExists` | Bucket name taken globally | Use unique name (add account ID/timestamp) |
| `Error: UnauthorizedOperation: You are not authorized to perform this operation` | Insufficient IAM permissions | Add required permissions to IAM user/role |
| `Error: InvalidParameterValue: Security group sg-xxx does not exist` | SG deleted outside Terraform | Run `terraform apply -refresh-only` to sync state |
| `Error: timeout while waiting for state to become 'available'` | Resource creation timeout | Increase timeout in resource config; check AWS service health |

### Detailed Troubleshooting Steps

#### Problem 1: State Lock Stuck

**Symptoms:**
```
Error: Error acquiring the state lock
Lock Info:
  ID:        a1b2c3d4-5678-90ab-cdef-1234567890ab
  Path:      my-bucket/terraform.tfstate
  Operation: OperationTypeApply
  Who:       user@hostname
  Version:   1.6.5
  Created:   2024-01-15 10:30:00
```

**Solution:**
```bash
# 1. Verify no other Terraform process is running
ps aux | grep terraform

# 2. Check DynamoDB lock table
aws dynamodb scan --table-name terraform-state-lock

# 3. Force unlock (use with caution!)
terraform force-unlock a1b2c3d4-5678-90ab-cdef-1234567890ab

# 4. If DynamoDB item stuck, manually delete
aws dynamodb delete-item \
  --table-name terraform-state-lock \
  --key '{"LockID":{"S":"my-bucket/envs/dev/terraform.tfstate-md5"}}'
```

#### Problem 2: ALB Health Checks Failing

**Symptoms:**
- Targets show "unhealthy" in target group
- 502 Bad Gateway errors

**Diagnosis:**
```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <TARGET_GROUP_ARN>

# Check security group rules
aws ec2 describe-security-groups \
  --group-ids <APP_SG_ID> <ALB_SG_ID>

# SSH to instance and test
ssh -i key.pem ec2-user@<PRIVATE_IP>
curl localhost:80/health
```

**Common Fixes:**
```hcl
# 1. Fix health check path
resource "aws_lb_target_group" "app" {
  health_check {
    path     = "/health"  # Ensure this endpoint exists!
    matcher  = "200"
    interval = 30
    timeout  = 5
  }
}

# 2. Fix security group
resource "aws_security_group_rule" "alb_to_app" {
  type                     = "ingress"
  from_port                = 80
  to_port                  = 80
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
  security_group_id        = aws_security_group.app.id
}

# 3. Verify app is listening
# In user_data.sh:
# netstat -tlnp | grep :80
```

#### Problem 3: EC2 Instance Not Accessible

**Diagnosis:**
```bash
# Check instance status
aws ec2 describe-instance-status --instance-ids <INSTANCE_ID>

# Get system log
aws ec2 get-console-output --instance-id <INSTANCE_ID>

# Check security group
aws ec2 describe-security-groups --group-ids <SG_ID>

# Verify route tables
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<VPC_ID>"
```

**Solutions:**
- Ensure bastion has public IP and internet gateway route
- Verify SSH key is correct
- Check security group allows SSH from your IP
- Verify NACL rules (if used)

#### Problem 4: Terraform Destroy Fails

**Error:**
```
Error: deleting EC2 Instance: UnauthorizedOperation
```

**Solution:**
```bash
# 1. Check for deletion protection
aws ec2 describe-instances --instance-ids <ID> \
  --query 'Reservations[].Instances[].DisableApiTermination'

# 2. Disable protection
aws ec2 modify-instance-attribute \
  --instance-id <ID> \
  --no-disable-api-termination

# 3. Retry destroy
terraform destroy

# 4. For stuck resources, remove from state
terraform state rm aws_instance.stuck_instance
```

---

## 18. End-to-End Code Examples

### Complete Working Example

**File: `envs/dev/main.tf`**

```hcl
terraform {
  required_version = ">= 1.6.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "terraform-state-123456789012"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = "us-east-1"
  
  default_tags {
    tags = {
      Environment = "dev"
      ManagedBy   = "Terraform"
      Project     = "demo-app"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "dev-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "dev-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "dev-public-${count.index + 1}"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 11}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "dev-private-${count.index + 1}"
  }
}

# NAT Gateway
resource "aws_eip" "nat" {
  domain = "vpc"
  tags = {
    Name = "dev-nat-eip"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  
  tags = {
    Name = "dev-nat"
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
    Name = "dev-public-rt"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }
  
  tags = {
    Name = "dev-private-rt"
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
  name_prefix = "dev-alb-"
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
    Name = "dev-alb-sg"
  }
}

resource "aws_security_group" "app" {
  name_prefix = "dev-app-"
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
    Name = "dev-app-sg"
  }
}

# ALB
resource "aws_lb" "main" {
  name               = "dev-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
  
  tags = {
    Name = "dev-alb"
  }
}

resource "aws_lb_target_group" "app" {
  name     = "dev-app-tg"
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

# Launch Template & ASG
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_launch_template" "app" {
  name_prefix   = "dev-app-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  
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
      Name = "dev-app-instance"
    }
  }
}

resource "aws_autoscaling_group" "app" {
  name                = "dev-app-asg"
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
    value               = "dev-app-asg"
    propagate_at_launch = true
  }
}

# S3 Bucket
resource "aws_s3_bucket" "app" {
  bucket = "dev-app-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name = "dev-app-bucket"
  }
}

resource "aws_s3_bucket_versioning" "app" {
  bucket = aws_s3_bucket.app.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "app" {
  bucket = aws_s3_bucket.app.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Outputs
output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "bucket_name" {
  value = aws_s3_bucket.app.id
}
```

---

## 19. Step-by-Step Runbook

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/yourorg/terraform-aws-infra.git
cd terraform-aws-infra

# 2. Configure AWS credentials
aws configure --profile terraform
# Enter: Access Key, Secret Key, Region (us-east-1), Output (json)

# 3. Verify AWS access
aws sts get-caller-identity --profile terraform

# 4. Create backend resources (one-time setup)
./scripts/create-backend.sh
```

### Deploy Infrastructure

```bash
# 1. Navigate to environment
cd envs/dev

# 2. Initialize Terraform
terraform init

# Expected output:
# Initializing the backend...
# Successfully configured the backend "s3"!
# Terraform has been successfully initialized!

# 3. Validate configuration
terraform validate

# Expected output:
# Success! The configuration is valid.

# 4. Format code
terraform fmt -recursive

# 5. Create execution plan
terraform plan -out=tfplan

# Review the plan output carefully!
# Look for: X to add, Y to change, Z to destroy

# 6. Apply the plan
terraform apply tfplan

# Expected output:
# Apply complete! Resources: X added, 0 changed, 0 destroyed.
# Outputs:
# alb_dns_name = "dev-alb-1234567890.us-east-1.elb.amazonaws.com"

# 7. View outputs
terraform output

# 8. Get specific output
terraform output -raw alb_dns_name
```

### Verify Deployment

```bash
# 1. Check ALB DNS
ALB_DNS=$(terraform output -raw alb_dns_name)
curl http://$ALB_DNS

# Expected: HTML response from app server

# 2. Verify AWS resources via CLI
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=dev-vpc"
aws ec2 describe-instances --filters "Name=tag:Name,Values=dev-app-instance"
aws elbv2 describe-load-balancers --names dev-alb
aws s3 ls | grep dev-app

# 3. Check target health
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw target_group_arn)

# Expected: State: healthy

# 4. View Auto Scaling Group
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names dev-app-asg
```

### Make Changes

```bash
# 1. Edit Terraform code
vim main.tf

# 2. Plan changes
terraform plan -out=tfplan

# 3. Review what will change
terraform show tfplan

# 4. Apply changes
terraform apply tfplan
```

### Inspect State

```bash
# List all resources
terraform state list

# Show specific resource
terraform state show aws_vpc.main

# Pull current state
terraform state pull > state.json

# Refresh state from AWS
terraform refresh
```

---

*Continued in final file...*
