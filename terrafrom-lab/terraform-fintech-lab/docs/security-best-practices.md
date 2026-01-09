# Security Best Practices: PayFlow Solutions Infrastructure

## Overview

This document outlines security best practices implemented in the PayFlow Solutions infrastructure, aligned with PCI-DSS compliance requirements and AWS Well-Architected Framework security pillar.

## 1. Terraform State Security

### Remote State with Encryption

**Problem:** Terraform state files contain sensitive data (passwords, keys, IPs)

**Solution:** S3 backend with encryption and versioning

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "payflow-terraform-state-prod"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:ACCOUNT:key/KEY-ID"
    dynamodb_table = "terraform-state-lock"
    
    # Prevent accidental deletion
    versioning = true
  }
}
```

**S3 Bucket Configuration:**

```hcl
resource "aws_s3_bucket" "terraform_state" {
  bucket = "payflow-terraform-state-prod"
  
  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }
  
  tags = {
    Name        = "Terraform State"
    Environment = "prod"
    Compliance  = "pci-dss"
  }
}

# Enable versioning
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable logging
resource "aws_s3_bucket_logging" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "terraform-state-access/"
}
```

**State Locking with DynamoDB:**

```hcl
resource "aws_dynamodb_table" "terraform_lock" {
  name           = "terraform-state-lock"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"
  
  attribute {
    name = "LockID"
    type = "S"
  }
  
  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }
  
  # Enable encryption
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }
  
  tags = {
    Name        = "Terraform State Lock"
    Environment = "prod"
  }
}
```

### Best Practices

✅ **Never commit state files to Git**
```bash
# .gitignore
*.tfstate
*.tfstate.*
.terraform/
```

✅ **Use separate state files per environment**
```
s3://bucket/dev/terraform.tfstate
s3://bucket/staging/terraform.tfstate
s3://bucket/prod/terraform.tfstate
```

✅ **Restrict state file access**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT:role/TerraformRole"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::payflow-terraform-state-prod/*"
    }
  ]
}
```

## 2. Secrets Management

### AWS Secrets Manager Integration

**Never hardcode secrets in Terraform:**

❌ **Bad Practice:**
```hcl
resource "aws_db_instance" "main" {
  username = "admin"
  password = "SuperSecret123!"  # NEVER DO THIS
}
```

✅ **Good Practice:**
```hcl
# Create secret
resource "aws_secretsmanager_secret" "db_password" {
  name = "payflow/prod/db-password"
  
  recovery_window_in_days = 7
  
  tags = {
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

# Generate random password
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Store password
resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

# Use in RDS
resource "aws_db_instance" "main" {
  username = "admin"
  password = random_password.db_password.result
  
  # Password will be in state file, but state is encrypted
}
```

### Automatic Secret Rotation

```hcl
resource "aws_secretsmanager_secret_rotation" "db_password" {
  secret_id           = aws_secretsmanager_secret.db_password.id
  rotation_lambda_arn = aws_lambda_function.rotate_secret.arn
  
  rotation_rules {
    automatically_after_days = 30
  }
}
```

### Application Access to Secrets

```hcl
# IAM policy for EC2 instances
resource "aws_iam_role_policy" "read_secrets" {
  name = "read-secrets"
  role = aws_iam_role.ec2_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.db_password.arn,
          "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:payflow/prod/*"
        ]
      }
    ]
  })
}
```

**Application code (Python):**
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
db_creds = get_secret('payflow/prod/db-password')
```

## 3. IAM Least Privilege

### Principle: Grant Minimum Required Permissions

**EC2 Instance Role (Application Servers):**

```hcl
resource "aws_iam_role" "ec2_app_role" {
  name = "payflow-ec2-app-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# CloudWatch Logs - Write only
resource "aws_iam_role_policy" "cloudwatch_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.ec2_app_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:us-east-1:ACCOUNT:log-group:/aws/ec2/payflow-app:*"
      }
    ]
  })
}

# S3 - Read config, Write logs
resource "aws_iam_role_policy" "s3_access" {
  name = "s3-access"
  role = aws_iam_role.ec2_app_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "arn:aws:s3:::payflow-config-prod/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "arn:aws:s3:::payflow-logs-prod/*"
      }
    ]
  })
}

# Secrets Manager - Read only specific secrets
resource "aws_iam_role_policy" "secrets_access" {
  name = "secrets-access"
  role = aws_iam_role.ec2_app_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.db_password.arn,
          aws_secretsmanager_secret.api_key.arn
        ]
      }
    ]
  })
}

# SSM Session Manager - No SSH keys needed
resource "aws_iam_role_policy_attachment" "ssm_managed_instance" {
  role       = aws_iam_role.ec2_app_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
```

### Terraform Execution Role

```hcl
# Separate role for Terraform (used by CI/CD)
resource "aws_iam_role" "terraform_role" {
  name = "terraform-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::ACCOUNT:user/ci-cd-user"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "sts:ExternalId" = "unique-external-id"
          }
        }
      }
    ]
  })
}

# Attach managed policies
resource "aws_iam_role_policy_attachment" "terraform_ec2" {
  role       = aws_iam_role.terraform_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

# Custom policy for specific resources
resource "aws_iam_role_policy" "terraform_custom" {
  name = "terraform-custom"
  role = aws_iam_role.terraform_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds:*",
          "elasticloadbalancing:*",
          "autoscaling:*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = "us-east-1"
          }
        }
      }
    ]
  })
}
```

## 4. Network Security

### Security Groups (Stateful Firewall)

**Layered Security Group Architecture:**

```hcl
# ALB Security Group - Internet-facing
resource "aws_security_group" "alb" {
  name        = "payflow-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id
  
  # Inbound: HTTPS from anywhere
  ingress {
    description = "HTTPS from Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Inbound: HTTP (redirect to HTTPS)
  ingress {
    description = "HTTP from Internet (redirect)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Outbound: To application tier only
  egress {
    description     = "To application servers"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
  
  tags = {
    Name = "payflow-alb-sg"
  }
}

# Application Security Group - Private subnet
resource "aws_security_group" "app" {
  name        = "payflow-app-sg"
  description = "Security group for application servers"
  vpc_id      = aws_vpc.main.id
  
  # Inbound: From ALB only
  ingress {
    description     = "HTTP from ALB"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  # Inbound: SSH from bastion only
  ingress {
    description     = "SSH from bastion"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }
  
  # Outbound: To database
  egress {
    description     = "PostgreSQL to database"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.db.id]
  }
  
  # Outbound: HTTPS for external APIs
  egress {
    description = "HTTPS to Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "payflow-app-sg"
  }
}

# Database Security Group - Most restrictive
resource "aws_security_group" "db" {
  name        = "payflow-db-sg"
  description = "Security group for RDS database"
  vpc_id      = aws_vpc.main.id
  
  # Inbound: From application tier only
  ingress {
    description     = "PostgreSQL from app servers"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
  
  # No outbound rules (database doesn't initiate connections)
  
  tags = {
    Name = "payflow-db-sg"
  }
}

# Bastion Security Group
resource "aws_security_group" "bastion" {
  name        = "payflow-bastion-sg"
  description = "Security group for bastion host"
  vpc_id      = aws_vpc.main.id
  
  # Inbound: SSH from office IP only
  ingress {
    description = "SSH from office"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["203.0.113.0/24"]  # Replace with your office IP
  }
  
  # Outbound: SSH to app servers
  egress {
    description     = "SSH to app servers"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
  
  tags = {
    Name = "payflow-bastion-sg"
  }
}
```

### Network ACLs (Stateless Firewall)

```hcl
# Public Subnet NACL
resource "aws_network_acl" "public" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.public[*].id
  
  # Inbound: HTTP
  ingress {
    rule_no    = 100
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }
  
  # Inbound: HTTPS
  ingress {
    rule_no    = 110
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }
  
  # Inbound: Ephemeral ports (return traffic)
  ingress {
    rule_no    = 120
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }
  
  # Outbound: All (stateless, must allow return traffic)
  egress {
    rule_no    = 100
    protocol   = "-1"
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }
  
  tags = {
    Name = "payflow-public-nacl"
  }
}

# Private Subnet NACL
resource "aws_network_acl" "private" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.private[*].id
  
  # Inbound: From VPC only
  ingress {
    rule_no    = 100
    protocol   = "-1"
    action     = "allow"
    cidr_block = aws_vpc.main.cidr_block
    from_port  = 0
    to_port    = 0
  }
  
  # Outbound: All
  egress {
    rule_no    = 100
    protocol   = "-1"
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }
  
  tags = {
    Name = "payflow-private-nacl"
  }
}
```

## 5. Encryption

### Encryption at Rest

**RDS Database:**
```hcl
resource "aws_db_instance" "main" {
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn
}
```

**S3 Buckets:**
```hcl
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
  }
}
```

**EBS Volumes:**
```hcl
resource "aws_launch_template" "app" {
  block_device_mappings {
    device_name = "/dev/xvda"
    
    ebs {
      encrypted   = true
      kms_key_id  = aws_kms_key.ebs.arn
      volume_size = 20
      volume_type = "gp3"
    }
  }
}
```

### Encryption in Transit

**ALB with TLS:**
```hcl
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.main.arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}
```

**RDS with SSL:**
```hcl
resource "aws_db_instance" "main" {
  # ... other config ...
  
  # Require SSL connections
  parameter_group_name = aws_db_parameter_group.ssl_required.name
}

resource "aws_db_parameter_group" "ssl_required" {
  family = "postgres15"
  
  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }
}
```

## 6. Tagging Strategy

### Consistent Tagging for Security and Compliance

```hcl
locals {
  common_tags = {
    Project     = "payflow-platform"
    ManagedBy   = "terraform"
    Environment = var.environment
    CostCenter  = "engineering"
    Compliance  = "pci-dss"
    Owner       = "devops-team"
  }
  
  # Additional tags for sensitive resources
  sensitive_tags = merge(local.common_tags, {
    DataClassification = "confidential"
    BackupRequired     = "true"
    MonitoringLevel    = "critical"
  })
}

# Apply to all resources
resource "aws_instance" "app" {
  # ... config ...
  tags = local.common_tags
}

resource "aws_db_instance" "main" {
  # ... config ...
  tags = local.sensitive_tags
}
```

### Tag-Based Access Control

```hcl
# IAM policy: Only access resources in dev environment
resource "aws_iam_policy" "dev_only" {
  name = "dev-environment-only"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "ec2:*"
        Resource = "*"
        Condition = {
          StringEquals = {
            "ec2:ResourceTag/Environment" = "dev"
          }
        }
      }
    ]
  })
}
```

## 7. Naming Conventions

### Consistent Resource Naming

```hcl
# Format: {project}-{resource}-{environment}-{region}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "payflow-vpc-prod-us-east-1"
  }
}

# Subnets
resource "aws_subnet" "public" {
  count = 3
  tags = {
    Name = "payflow-subnet-public-${count.index + 1}-prod-us-east-1${local.azs[count.index]}"
  }
}

# Security Groups
resource "aws_security_group" "alb" {
  name = "payflow-sg-alb-prod"
}

# EC2 Instances (via ASG)
resource "aws_launch_template" "app" {
  name_prefix = "payflow-lt-app-prod-"
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "payflow-ec2-app-prod"
    }
  }
}

# RDS
resource "aws_db_instance" "main" {
  identifier = "payflow-rds-postgres-prod"
}

# S3 Buckets (must be globally unique)
resource "aws_s3_bucket" "state" {
  bucket = "payflow-terraform-state-prod-us-east-1-${data.aws_caller_identity.current.account_id}"
}
```

## 8. Audit Logging

### CloudTrail for API Auditing

```hcl
resource "aws_cloudtrail" "main" {
  name                          = "payflow-cloudtrail-prod"
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  
  # Encrypt logs
  kms_key_id = aws_kms_key.cloudtrail.arn
  
  event_selector {
    read_write_type           = "All"
    include_management_events = true
    
    # Log data events (S3, Lambda)
    data_resource {
      type   = "AWS::S3::Object"
      values = ["${aws_s3_bucket.sensitive.arn}/"]
    }
  }
  
  tags = local.sensitive_tags
}
```

### VPC Flow Logs

```hcl
resource "aws_flow_log" "main" {
  vpc_id          = aws_vpc.main.id
  traffic_type    = "ALL"
  iam_role_arn    = aws_iam_role.flow_logs.arn
  log_destination = aws_cloudwatch_log_group.flow_logs.arn
  
  tags = {
    Name = "payflow-vpc-flow-logs-prod"
  }
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/aws/vpc/payflow-prod"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.logs.arn
}
```

## Security Checklist

### Pre-Deployment

- [ ] All secrets stored in Secrets Manager (no hardcoded values)
- [ ] State file encrypted and access restricted
- [ ] IAM roles follow least privilege
- [ ] Security groups deny by default, allow specific
- [ ] Encryption at rest enabled (RDS, S3, EBS)
- [ ] Encryption in transit enabled (TLS 1.2+)
- [ ] CloudTrail enabled for audit logging
- [ ] VPC Flow Logs enabled
- [ ] Resource tagging complete and consistent
- [ ] Naming conventions followed

### Post-Deployment

- [ ] Run security scanner (Checkov, tfsec)
- [ ] Review security group rules
- [ ] Verify no public database access
- [ ] Test bastion host access
- [ ] Verify CloudWatch alarms configured
- [ ] Review IAM policies for over-permissions
- [ ] Check S3 bucket public access (should be blocked)
- [ ] Verify backup configurations

### Ongoing

- [ ] Rotate secrets every 30 days
- [ ] Review CloudTrail logs weekly
- [ ] Update security group rules as needed
- [ ] Patch EC2 instances monthly
- [ ] Review IAM access quarterly
- [ ] Conduct penetration testing annually
- [ ] Review and update security policies

## Tools and Automation

### Security Scanning

```bash
# Checkov - Terraform security scanner
checkov -d . --framework terraform

# tfsec - Terraform static analysis
tfsec .

# Terraform validate
terraform validate

# AWS Config - Compliance checking
aws configservice describe-compliance-by-config-rule
```

### Automated Compliance

```hcl
# AWS Config rule: Ensure encryption
resource "aws_config_config_rule" "encrypted_volumes" {
  name = "encrypted-volumes"
  
  source {
    owner             = "AWS"
    source_identifier = "ENCRYPTED_VOLUMES"
  }
  
  depends_on = [aws_config_configuration_recorder.main]
}
```

## Next Steps

- Review [Troubleshooting Guide](troubleshooting.md)
- Study [Use Cases & Scenarios](use-cases.md)
- Begin [Lab 01: VPC Networking](../labs/01-vpc-networking/README.md)
