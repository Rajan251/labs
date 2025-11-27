# Terraform AWS Infrastructure Guide - Part 3

## 9. Application Load Balancer

### Complete ALB Module

**File: `modules/alb/variables.tf`**

```hcl
variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "security_group_ids" {
  type = list(string)
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
  default     = ""
}

variable "enable_https" {
  type    = bool
  default = false
}
```

**File: `modules/alb/main.tf`**

```hcl
# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.public_subnet_ids

  enable_deletion_protection = false  # Set true for production
  enable_http2              = true
  enable_cross_zone_load_balancing = true

  tags = {
    Name = "${var.environment}-alb"
  }
}

# Target Group
resource "aws_lb_target_group" "app" {
  name     = "${var.environment}-app-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
  }

  deregistration_delay = 30

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }

  tags = {
    Name = "${var.environment}-app-tg"
  }
}

# HTTP Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = var.enable_https ? "redirect" : "forward"

    dynamic "redirect" {
      for_each = var.enable_https ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    target_group_arn = var.enable_https ? null : aws_lb_target_group.app.arn
  }
}

# HTTPS Listener (conditional)
resource "aws_lb_listener" "https" {
  count             = var.enable_https ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
```

**File: `modules/alb/outputs.tf`**

```hcl
output "alb_arn" {
  value = aws_lb.main.arn
}

output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "target_group_arn" {
  value = aws_lb_target_group.app.arn
}

output "alb_zone_id" {
  value = aws_lb.main.zone_id
}
```

### Common ALB Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Health checks failing | Wrong path/port | Verify `/health` endpoint exists and returns 200 |
| 502 Bad Gateway | App not listening | Check app is running on correct port (80/8080) |
| Timeout errors | Security group blocks traffic | Allow ALB SG → App SG on app port |
| SSL certificate error | Wrong ARN or region | Ensure ACM cert is in same region as ALB |

---

## 10. S3 Buckets

### S3 Module Example

**File: `modules/s3/main.tf`**

```hcl
# Application Storage Bucket
resource "aws_s3_bucket" "app_storage" {
  bucket = "${var.environment}-app-storage-${var.account_id}"

  tags = {
    Name        = "${var.environment}-app-storage"
    Environment = var.environment
  }
}

# Enable Versioning
resource "aws_s3_bucket_versioning" "app_storage" {
  bucket = aws_s3_bucket.app_storage.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "app_storage" {
  bucket = aws_s3_bucket.app_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
      # Or use KMS:
      # sse_algorithm     = "aws:kms"
      # kms_master_key_id = var.kms_key_id
    }
    bucket_key_enabled = true
  }
}

# Block Public Access
resource "aws_s3_bucket_public_access_block" "app_storage" {
  bucket = aws_s3_bucket.app_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle Rules
resource "aws_s3_bucket_lifecycle_configuration" "app_storage" {
  bucket = aws_s3_bucket.app_storage.id

  rule {
    id     = "archive-old-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }

  rule {
    id     = "delete-incomplete-uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# Bucket Policy
resource "aws_s3_bucket_policy" "app_storage" {
  bucket = aws_s3_bucket.app_storage.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyInsecureTransport"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.app_storage.arn,
          "${aws_s3_bucket.app_storage.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
      {
        Sid    = "AllowEC2Access"
        Effect = "Allow"
        Principal = {
          AWS = var.ec2_role_arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.app_storage.arn,
          "${aws_s3_bucket.app_storage.arn}/*"
        ]
      }
    ]
  })
}

# Logging Bucket (optional)
resource "aws_s3_bucket" "logs" {
  bucket = "${var.environment}-app-logs-${var.account_id}"

  tags = {
    Name = "${var.environment}-app-logs"
  }
}

resource "aws_s3_bucket_acl" "logs" {
  bucket = aws_s3_bucket.logs.id
  acl    = "log-delivery-write"
}

# Enable Logging on Main Bucket
resource "aws_s3_bucket_logging" "app_storage" {
  bucket = aws_s3_bucket.app_storage.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "app-storage-logs/"
}
```

### S3 Best Practices

- **Naming**: Use DNS-compliant names, include account ID for uniqueness
- **Encryption**: Always enable (AES256 or KMS)
- **Versioning**: Enable for critical data
- **Lifecycle**: Archive old data to Glacier, delete incomplete uploads
- **Access**: Block public access, use IAM roles instead of keys
- **Logging**: Enable access logs for audit trails

---

## 11. Variables, Outputs, Secrets

### Example `variables.tf`

```hcl
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
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "min_size" {
  description = "Minimum ASG size"
  type        = number
  default     = 2
}

variable "max_size" {
  description = "Maximum ASG size"
  type        = number
  default     = 6
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to SSH"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
```

### Example `outputs.tf`

```hcl
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.alb.alb_dns_name
}

output "bastion_public_ip" {
  description = "Bastion host public IP"
  value       = aws_eip.bastion.public_ip
}

output "app_bucket_name" {
  description = "Application S3 bucket name"
  value       = module.s3.app_bucket_name
}

output "nat_gateway_ips" {
  description = "NAT Gateway IPs"
  value       = module.vpc.nat_gateway_ips
}

# Sensitive output
output "db_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}
```

### Using Locals

```hcl
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Owner       = "DevOps Team"
  }

  # Derived values
  vpc_name = "${var.project_name}-${var.environment}-vpc"
  
  # Conditional logic
  enable_nat = var.environment == "prod" ? true : false
  
  # Map transformations
  subnet_tags = {
    for idx, subnet in var.private_subnet_cidrs :
    "subnet-${idx}" => {
      Name = "${var.environment}-private-${idx}"
      Tier = "Private"
    }
  }
}
```

### Secrets Handling

**❌ NEVER do this:**

```hcl
variable "db_password" {
  default = "MyPassword123"  # NEVER hardcode secrets!
}
```

**✅ Recommended approaches:**

**1. Environment Variables**

```bash
export TF_VAR_db_password="SecurePassword123"
terraform plan
```

**2. terraform.tfvars (gitignored)**

```hcl
# terraform.tfvars (DO NOT commit to git)
db_password = "SecurePassword123"
```

**3. AWS Secrets Manager**

```hcl
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "prod/db/password"
}

locals {
  db_password = jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["password"]
}
```

**4. SSM Parameter Store**

```hcl
data "aws_ssm_parameter" "db_password" {
  name = "/prod/db/password"
}

resource "aws_db_instance" "main" {
  password = data.aws_ssm_parameter.db_password.value
}
```

**5. Mark Variables as Sensitive**

```hcl
variable "db_password" {
  type      = string
  sensitive = true  # Prevents display in logs
}
```

---

## 12. Modules & Reusability

### Creating a VPC Module

**Directory: `modules/vpc/`**

Already shown in Section 6. Key points:
- Clear inputs via `variables.tf`
- Useful outputs via `outputs.tf`
- Self-contained resources in `main.tf`
- Include `README.md` with usage examples

### Using Modules in Environment

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
    bucket         = "my-terraform-state-1234567890"
    key            = "envs/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = local.common_tags
  }
}

# Data sources
data "aws_caller_identity" "current" {}

# Local values
locals {
  account_id = data.aws_caller_identity.current.account_id
  
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  vpc_cidr             = var.vpc_cidr
  environment          = var.environment
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]
  enable_nat_gateway   = true
  single_nat_gateway   = true  # Cost saving for dev
}

# ALB Module
module "alb" {
  source = "../../modules/alb"

  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  security_group_ids = [module.vpc.alb_sg_id]
}

# EC2 ASG Module
module "ec2_asg" {
  source = "../../modules/ec2-asg"

  environment          = var.environment
  vpc_id               = module.vpc.vpc_id
  private_subnet_ids   = module.vpc.private_subnet_ids
  security_group_ids   = [module.vpc.app_sg_id]
  instance_type        = var.instance_type
  min_size             = var.min_size
  max_size             = var.max_size
  desired_capacity     = 2
  target_group_arns    = [module.alb.target_group_arn]
  iam_instance_profile = aws_iam_instance_profile.ec2_app_profile.name
}

# S3 Module
module "s3" {
  source = "../../modules/s3"

  environment   = var.environment
  account_id    = local.account_id
  ec2_role_arn  = aws_iam_role.ec2_app_role.arn
}
```

**File: `envs/dev/terraform.tfvars`**

```hcl
aws_region   = "us-east-1"
aws_profile  = "terraform"
environment  = "dev"
project_name = "myapp"

vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

instance_type = "t3.small"
min_size      = 2
max_size      = 4

allowed_ssh_cidrs = ["203.0.113.0/24"]  # Replace with your IP
```

---

*Continued in next file...*
