# Terraform Complete Capabilities Reference

> **Comprehensive guide to everything Terraform can do with practical examples and hints**

This document covers all major Terraform capabilities, organized by category, with real-world examples from the FinTech Payment Platform project.

---

## Table of Contents

1. [Infrastructure Provisioning](#1-infrastructure-provisioning)
2. [State Management](#2-state-management)
3. [Module System](#3-module-system)
4. [Variable Management](#4-variable-management)
5. [Output Management](#5-output-management)
6. [Resource Dependencies](#6-resource-dependencies)
7. [Lifecycle Management](#7-lifecycle-management)
8. [Data Sources](#8-data-sources)
9. [Provisioners](#9-provisioners)
10. [Workspaces](#10-workspaces)
11. [Import & Migration](#11-import--migration)
12. [Testing & Validation](#12-testing--validation)
13. [Security & Secrets](#13-security--secrets)
14. [Multi-Cloud Support](#14-multi-cloud-support)
15. [Advanced Features](#15-advanced-features)

---

## 1. Infrastructure Provisioning

### What Terraform Can Provision

Terraform can create, modify, and destroy virtually any cloud or on-premise resource through providers.

### Capabilities

| Capability | Description | Use Case |
|------------|-------------|----------|
| **Resource Creation** | Define and create infrastructure | VPC, EC2, RDS, S3, etc. |
| **Resource Modification** | Update existing resources | Change instance types, scale ASG |
| **Resource Destruction** | Safely delete resources | Cleanup, decommissioning |
| **Multi-Resource Orchestration** | Coordinate multiple resources | Full stack deployment |
| **Dependency Resolution** | Automatic ordering | Create VPC before subnets |

### Examples

#### Basic Resource Creation

```hcl
# Create a VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "payflow-vpc"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

# Create subnets
resource "aws_subnet" "public" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "payflow-public-${count.index + 1}"
    Type = "public"
  }
}
```

**💡 Hint**: Use `count` or `for_each` to create multiple similar resources efficiently.

#### Complex Multi-Resource Stack

```hcl
# Auto Scaling Group with Launch Template
resource "aws_launch_template" "app" {
  name_prefix   = "payflow-app-"
  image_id      = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type

  vpc_security_group_ids = [aws_security_group.app.id]

  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    db_endpoint = aws_db_instance.main.endpoint
    app_version = var.app_version
  }))

  iam_instance_profile {
    name = aws_iam_instance_profile.app.name
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "payflow-app-instance"
    }
  }
}

resource "aws_autoscaling_group" "app" {
  name                = "payflow-app-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  target_group_arns   = [aws_lb_target_group.app.arn]
  health_check_type   = "ELB"
  
  min_size         = var.min_size
  max_size         = var.max_size
  desired_capacity = var.desired_capacity

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "payflow-app-instance"
    propagate_at_launch = true
  }
}
```

**💡 Hint**: Use `templatefile()` to inject dynamic values into user data scripts.

---

## 2. State Management

### What Terraform State Does

State tracks the current status of your infrastructure and maps configuration to real-world resources.

### Capabilities

| Capability | Description | Command |
|------------|-------------|---------|
| **Local State** | Store state on local disk | Default behavior |
| **Remote State** | Store state in S3, Consul, etc. | `backend "s3" {}` |
| **State Locking** | Prevent concurrent modifications | DynamoDB table |
| **State Inspection** | View current state | `terraform state list` |
| **State Manipulation** | Move, remove resources | `terraform state mv/rm` |
| **State Import** | Import existing resources | `terraform import` |
| **State Backup** | Automatic backups | `.terraform.tfstate.backup` |

### Examples

#### Remote State Configuration

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "payflow-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "payflow-terraform-locks"
    
    # Enable versioning for state history
    versioning = true
  }
}
```

**💡 Hint**: Always enable encryption and versioning for production state files.

#### State Commands

```bash
# List all resources in state
terraform state list

# Show details of a specific resource
terraform state show aws_instance.app[0]

# Move a resource to a different address
terraform state mv aws_instance.old aws_instance.new

# Remove a resource from state (doesn't delete actual resource)
terraform state rm aws_instance.decommissioned

# Pull remote state to local
terraform state pull > terraform.tfstate.backup

# Push local state to remote
terraform state push terraform.tfstate
```

**💡 Hint**: Always backup state before manual manipulation: `terraform state pull > backup.tfstate`

#### Remote State Data Source

```hcl
# Reference outputs from another Terraform project
data "terraform_remote_state" "vpc" {
  backend = "s3"
  config = {
    bucket = "payflow-terraform-state"
    key    = "networking/terraform.tfstate"
    region = "us-east-1"
  }
}

# Use outputs from remote state
resource "aws_instance" "app" {
  subnet_id = data.terraform_remote_state.vpc.outputs.private_subnet_ids[0]
  vpc_security_group_ids = [
    data.terraform_remote_state.vpc.outputs.app_security_group_id
  ]
}
```

**💡 Hint**: Use remote state data sources to share outputs between separate Terraform projects.

---

## 3. Module System

### What Modules Enable

Modules are reusable, self-contained packages of Terraform configurations.

### Capabilities

| Capability | Description | Benefit |
|------------|-------------|---------|
| **Code Reusability** | Write once, use many times | DRY principle |
| **Abstraction** | Hide complexity | Simplified interfaces |
| **Versioning** | Pin module versions | Stability |
| **Composition** | Combine modules | Complex architectures |
| **Testing** | Test modules independently | Quality assurance |
| **Sharing** | Publish to registry | Team collaboration |

### Examples

#### Creating a Module

```hcl
# modules/vpc/main.tf
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "availability_zones" {
  description = "List of AZs"
  type        = list(string)
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.environment}-vpc"
    Environment = var.environment
  }
}

resource "aws_subnet" "public" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.environment}-public-${count.index + 1}"
    Type = "public"
  }
}

# modules/vpc/outputs.tf
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}
```

#### Using a Module

```hcl
# environments/prod/main.tf
module "vpc" {
  source = "../../modules/vpc"

  vpc_cidr           = "10.0.0.0/16"
  environment        = "production"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# Reference module outputs
resource "aws_instance" "app" {
  subnet_id = module.vpc.public_subnet_ids[0]
}
```

**💡 Hint**: Use relative paths (`../../modules/vpc`) for local modules, URLs for remote modules.

#### Module from Registry

```hcl
# Use official AWS VPC module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  name = "payflow-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = false
  one_nat_gateway_per_az = true

  tags = {
    Environment = "production"
  }
}
```

**💡 Hint**: Always pin module versions in production to prevent unexpected changes.

---

## 4. Variable Management

### What Variables Enable

Variables make configurations flexible and reusable across environments.

### Capabilities

| Capability | Description | Example |
|------------|-------------|---------|
| **Input Variables** | Accept external values | `var.instance_type` |
| **Variable Types** | String, number, bool, list, map, object | Type safety |
| **Default Values** | Fallback values | `default = "t3.micro"` |
| **Validation** | Enforce constraints | `validation {}` block |
| **Sensitive Variables** | Hide secrets in output | `sensitive = true` |
| **Variable Files** | Organize values | `.tfvars` files |
| **Environment Variables** | OS-level variables | `TF_VAR_*` |

### Examples

#### Variable Declarations

```hcl
# variables.tf
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "instance_count" {
  description = "Number of instances"
  type        = number
  default     = 2
  
  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

variable "enable_monitoring" {
  description = "Enable detailed monitoring"
  type        = bool
  default     = true
}

variable "subnet_cidrs" {
  description = "List of subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project   = "PayFlow"
    ManagedBy = "Terraform"
  }
}

variable "database_config" {
  description = "Database configuration"
  type = object({
    instance_class    = string
    allocated_storage = number
    multi_az          = bool
    backup_retention  = number
  })
  default = {
    instance_class    = "db.t3.small"
    allocated_storage = 20
    multi_az          = true
    backup_retention  = 7
  }
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}
```

#### Variable Files

```hcl
# terraform.tfvars (default file, auto-loaded)
environment     = "production"
instance_type   = "t3.medium"
instance_count  = 5
enable_monitoring = true

tags = {
  Project     = "PayFlow"
  Environment = "Production"
  CostCenter  = "Engineering"
}

# dev.tfvars (use with: terraform apply -var-file="dev.tfvars")
environment     = "dev"
instance_type   = "t3.micro"
instance_count  = 1
enable_monitoring = false

database_config = {
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  multi_az          = false
  backup_retention  = 1
}
```

**💡 Hint**: Use `terraform.tfvars` for common values, environment-specific `.tfvars` for overrides.

#### Environment Variables

```bash
# Set variables via environment
export TF_VAR_environment="production"
export TF_VAR_instance_type="t3.medium"
export TF_VAR_db_password="super-secret-password"

# Run terraform
terraform apply
```

**💡 Hint**: Use `TF_VAR_` prefix for any variable, great for CI/CD pipelines and secrets.

---

## 5. Output Management

### What Outputs Enable

Outputs expose values from your infrastructure for use by other tools or modules.

### Capabilities

| Capability | Description | Use Case |
|------------|-------------|----------|
| **Value Export** | Export resource attributes | Share ALB DNS name |
| **Module Outputs** | Return values from modules | Module composition |
| **Sensitive Outputs** | Hide sensitive data | Database passwords |
| **Output Dependencies** | Create implicit dependencies | Ensure creation order |
| **JSON Output** | Machine-readable format | CI/CD integration |

### Examples

#### Output Declarations

```hcl
# outputs.tf
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "database_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true  # Won't show in console output
}

output "instance_ips" {
  description = "Private IP addresses of EC2 instances"
  value       = aws_instance.app[*].private_ip
}

output "subnet_map" {
  description = "Map of subnet names to IDs"
  value = {
    for subnet in aws_subnet.private :
    subnet.tags.Name => subnet.id
  }
}

output "connection_string" {
  description = "Database connection string"
  value = format(
    "postgresql://%s:%s@%s:%s/%s",
    aws_db_instance.main.username,
    var.db_password,
    aws_db_instance.main.address,
    aws_db_instance.main.port,
    aws_db_instance.main.db_name
  )
  sensitive = true
}
```

#### Using Outputs

```bash
# View all outputs
terraform output

# View specific output
terraform output alb_dns_name

# View sensitive output
terraform output -raw database_endpoint

# Get JSON format (for scripts)
terraform output -json > outputs.json

# Use in shell scripts
ALB_DNS=$(terraform output -raw alb_dns_name)
curl http://$ALB_DNS/health
```

**💡 Hint**: Use `terraform output -json` in CI/CD pipelines to pass values between stages.

---

## 6. Resource Dependencies

### What Dependency Management Does

Terraform automatically determines the order to create, update, or destroy resources.

### Capabilities

| Capability | Description | Example |
|------------|-------------|---------|
| **Implicit Dependencies** | Auto-detected from references | `vpc_id = aws_vpc.main.id` |
| **Explicit Dependencies** | Manually specified | `depends_on = [aws_iam_role.app]` |
| **Dependency Graph** | Visualize relationships | `terraform graph` |
| **Parallel Execution** | Create independent resources simultaneously | Performance |
| **Destroy Order** | Reverse of creation order | Safe teardown |

### Examples

#### Implicit Dependencies

```hcl
# VPC created first (no dependencies)
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# Subnet created after VPC (implicit dependency)
resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id  # References VPC
  cidr_block = "10.0.1.0/24"
}

# Security group created after VPC
resource "aws_security_group" "app" {
  vpc_id = aws_vpc.main.id  # References VPC
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Instance created after subnet and security group
resource "aws_instance" "app" {
  subnet_id              = aws_subnet.public.id  # References subnet
  vpc_security_group_ids = [aws_security_group.app.id]  # References SG
  
  ami           = "ami-12345678"
  instance_type = "t3.micro"
}
```

**💡 Hint**: Terraform automatically detects dependencies from resource references.

#### Explicit Dependencies

```hcl
# IAM role must exist before instance profile
resource "aws_iam_role" "app" {
  name = "payflow-app-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

# Instance profile depends on role
resource "aws_iam_instance_profile" "app" {
  name = "payflow-app-profile"
  role = aws_iam_role.app.name
  
  # Explicit dependency (usually not needed, but shown for example)
  depends_on = [aws_iam_role.app]
}

# S3 bucket policy depends on bucket
resource "aws_s3_bucket_policy" "logs" {
  bucket = aws_s3_bucket.logs.id
  
  # Ensure bucket is fully created before applying policy
  depends_on = [aws_s3_bucket.logs]
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "logging.s3.amazonaws.com"
      }
      Action   = "s3:PutObject"
      Resource = "${aws_s3_bucket.logs.arn}/*"
    }]
  })
}
```

**💡 Hint**: Use `depends_on` only when Terraform can't detect the dependency automatically.

#### Dependency Graph

```bash
# Generate dependency graph
terraform graph > graph.dot

# Convert to image (requires Graphviz)
dot -Tpng graph.dot -o graph.png

# View in browser
terraform graph | dot -Tsvg > graph.svg
```

**💡 Hint**: Use `terraform graph` to visualize complex dependencies and troubleshoot circular references.

---

## 7. Lifecycle Management

### What Lifecycle Rules Do

Control how Terraform creates, updates, and destroys resources.

### Capabilities

| Capability | Description | Use Case |
|------------|-------------|---------|
| **create_before_destroy** | Create replacement before destroying | Zero-downtime updates |
| **prevent_destroy** | Block resource deletion | Protect critical resources |
| **ignore_changes** | Ignore specific attribute changes | External modifications |
| **replace_triggered_by** | Force replacement on changes | Coordinated updates |
| **precondition** | Validate before apply | Safety checks |
| **postcondition** | Validate after apply | Verification |

### Examples

#### Create Before Destroy

```hcl
resource "aws_launch_template" "app" {
  name_prefix   = "payflow-app-"
  image_id      = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    create_before_destroy = true  # Create new template before deleting old
  }
}

resource "aws_autoscaling_group" "app" {
  name = "payflow-app-asg"
  
  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  min_size = 2
  max_size = 10

  lifecycle {
    create_before_destroy = true  # Ensure smooth ASG updates
  }
}
```

**💡 Hint**: Use `create_before_destroy` for resources that can't have downtime during updates.

#### Prevent Destroy

```hcl
resource "aws_db_instance" "main" {
  identifier     = "payflow-prod-db"
  engine         = "postgres"
  instance_class = "db.t3.small"
  
  allocated_storage = 100
  storage_encrypted = true

  lifecycle {
    prevent_destroy = true  # Prevent accidental deletion
  }
}

resource "aws_s3_bucket" "critical_data" {
  bucket = "payflow-critical-data"

  lifecycle {
    prevent_destroy = true  # Protect production data
  }
}
```

**💡 Hint**: Enable `prevent_destroy` for databases and data stores in production.

#### Ignore Changes

```hcl
resource "aws_instance" "app" {
  ami           = var.ami_id
  instance_type = var.instance_type
  
  tags = {
    Name = "payflow-app"
  }

  lifecycle {
    # Ignore changes to tags (might be modified by auto-scaling or external tools)
    ignore_changes = [
      tags,
      user_data,  # Ignore user data changes after initial creation
    ]
  }
}

resource "aws_autoscaling_group" "app" {
  name             = "payflow-app-asg"
  min_size         = 2
  max_size         = 10
  desired_capacity = 5

  lifecycle {
    # Ignore desired_capacity changes (managed by auto-scaling policies)
    ignore_changes = [desired_capacity]
  }
}
```

**💡 Hint**: Use `ignore_changes` for attributes managed by external systems or auto-scaling.

#### Preconditions and Postconditions

```hcl
resource "aws_db_instance" "main" {
  identifier     = "payflow-db"
  engine         = "postgres"
  instance_class = var.db_instance_class
  
  multi_az = var.environment == "prod" ? true : false

  lifecycle {
    # Ensure production databases are always multi-AZ
    precondition {
      condition     = var.environment != "prod" || self.multi_az == true
      error_message = "Production databases must be multi-AZ."
    }
    
    # Verify database is accessible after creation
    postcondition {
      condition     = self.status == "available"
      error_message = "Database must be in available status."
    }
  }
}
```

**💡 Hint**: Use preconditions for safety checks, postconditions for verification.

---

## 8. Data Sources

### What Data Sources Do

Query existing infrastructure and external data without managing it.

### Capabilities

| Capability | Description | Example |
|------------|-------------|---------|
| **Query AWS Resources** | Fetch existing resource data | Latest AMI |
| **External Data** | Read from external sources | HTTP APIs |
| **Computed Values** | Calculate values | CIDR subnets |
| **Template Rendering** | Generate files | User data scripts |
| **Archive Files** | Create ZIP files | Lambda packages |

### Examples

#### AWS Data Sources

```hcl
# Get latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Get available AZs in current region
data "aws_availability_zones" "available" {
  state = "available"
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Get existing VPC
data "aws_vpc" "existing" {
  filter {
    name   = "tag:Name"
    values = ["existing-vpc"]
  }
}

# Use data sources
resource "aws_instance" "app" {
  ami               = data.aws_ami.amazon_linux_2.id
  availability_zone = data.aws_availability_zones.available.names[0]
  
  tags = {
    AccountId = data.aws_caller_identity.current.account_id
  }
}
```

**💡 Hint**: Use data sources to reference existing resources without importing them into state.

#### Template Files

```hcl
# Render user data script
data "template_file" "user_data" {
  template = file("${path.module}/user-data.sh.tpl")

  vars = {
    db_endpoint    = aws_db_instance.main.endpoint
    app_version    = var.app_version
    environment    = var.environment
    s3_bucket      = aws_s3_bucket.app_data.id
    cloudwatch_log = aws_cloudwatch_log_group.app.name
  }
}

resource "aws_instance" "app" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type
  user_data     = data.template_file.user_data.rendered
}
```

**user-data.sh.tpl:**
```bash
#!/bin/bash
export DB_ENDPOINT="${db_endpoint}"
export APP_VERSION="${app_version}"
export ENVIRONMENT="${environment}"
export S3_BUCKET="${s3_bucket}"

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Start application
/opt/app/start.sh
```

**💡 Hint**: Use `templatefile()` function instead of `template_file` data source (newer approach).

#### External Data Source

```hcl
# Query external API
data "external" "latest_version" {
  program = ["bash", "${path.module}/scripts/get-version.sh"]
}

# Use external data
resource "aws_instance" "app" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type
  
  tags = {
    AppVersion = data.external.latest_version.result.version
  }
}
```

**get-version.sh:**
```bash
#!/bin/bash
# Must output valid JSON
curl -s https://api.example.com/version | jq '{version: .latest}'
```

**💡 Hint**: External data sources must return valid JSON with string values only.

---

## 9. Provisioners

### What Provisioners Do

Execute scripts or commands on local or remote machines during resource creation/destruction.

### Capabilities

| Capability | Description | Use Case |
|------------|-------------|---------|
| **local-exec** | Run commands locally | Trigger webhooks |
| **remote-exec** | Run commands on remote | Configure instances |
| **file** | Copy files to remote | Upload configs |
| **connection** | SSH/WinRM connection | Remote access |
| **null_resource** | Trigger provisioners | Standalone scripts |

### Examples

#### Local Exec Provisioner

```hcl
resource "aws_instance" "app" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type

  provisioner "local-exec" {
    command = "echo ${self.private_ip} >> private_ips.txt"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "echo 'Instance ${self.id} is being destroyed' >> destroy_log.txt"
  }
}

# Trigger Ansible after instance creation
resource "null_resource" "configure_app" {
  triggers = {
    instance_id = aws_instance.app.id
  }

  provisioner "local-exec" {
    command = <<-EOT
      ansible-playbook \
        -i ${aws_instance.app.public_ip}, \
        -u ec2-user \
        --private-key ${var.ssh_key_path} \
        playbooks/configure-app.yml
    EOT
  }
}
```

**💡 Hint**: Use `local-exec` for triggering external tools like Ansible, webhooks, or notifications.

#### Remote Exec Provisioner

```hcl
resource "aws_instance" "app" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type
  key_name      = aws_key_pair.deployer.key_name

  connection {
    type        = "ssh"
    user        = "ec2-user"
    private_key = file(var.ssh_private_key_path)
    host        = self.public_ip
  }

  provisioner "remote-exec" {
    inline = [
      "sudo yum update -y",
      "sudo yum install -y docker",
      "sudo systemctl start docker",
      "sudo systemctl enable docker",
      "sudo usermod -aG docker ec2-user"
    ]
  }

  provisioner "remote-exec" {
    script = "${path.module}/scripts/install-app.sh"
  }
}
```

**💡 Hint**: Prefer user_data over provisioners for instance configuration when possible.

#### File Provisioner

```hcl
resource "aws_instance" "app" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type
  key_name      = aws_key_pair.deployer.key_name

  connection {
    type        = "ssh"
    user        = "ec2-user"
    private_key = file(var.ssh_private_key_path)
    host        = self.public_ip
  }

  # Upload single file
  provisioner "file" {
    source      = "configs/app.conf"
    destination = "/tmp/app.conf"
  }

  # Upload directory
  provisioner "file" {
    source      = "configs/"
    destination = "/tmp/configs"
  }

  # Upload content
  provisioner "file" {
    content     = templatefile("configs/database.conf.tpl", {
      db_host = aws_db_instance.main.endpoint
    })
    destination = "/tmp/database.conf"
  }

  # Move files to final location
  provisioner "remote-exec" {
    inline = [
      "sudo mv /tmp/app.conf /etc/app/app.conf",
      "sudo mv /tmp/database.conf /etc/app/database.conf",
      "sudo systemctl restart app"
    ]
  }
}
```

**💡 Hint**: Provisioners are a last resort; prefer cloud-init, user_data, or configuration management tools.

---

## 10. Workspaces

### What Workspaces Enable

Manage multiple instances of the same configuration with separate state files.

### Capabilities

| Capability | Description | Use Case |
|------------|-------------|---------|
| **Multiple States** | Separate state per workspace | Environment isolation |
| **Workspace Switching** | Change active workspace | Switch contexts |
| **Workspace Variables** | Dynamic values per workspace | Environment-specific configs |
| **Default Workspace** | Always exists | Production baseline |

### Examples

#### Workspace Commands

```bash
# List workspaces
terraform workspace list

# Create new workspace
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch workspace
terraform workspace select dev

# Show current workspace
terraform workspace show

# Delete workspace (must be empty)
terraform workspace delete dev
```

#### Using Workspaces in Configuration

```hcl
# variables.tf
locals {
  # Environment-specific configurations
  env_config = {
    dev = {
      instance_type = "t3.micro"
      instance_count = 1
      multi_az = false
    }
    staging = {
      instance_type = "t3.small"
      instance_count = 2
      multi_az = true
    }
    prod = {
      instance_type = "t3.medium"
      instance_count = 5
      multi_az = true
    }
  }
  
  # Get config for current workspace
  current_config = local.env_config[terraform.workspace]
}

# main.tf
resource "aws_instance" "app" {
  count         = local.current_config.instance_count
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = local.current_config.instance_type

  tags = {
    Name        = "payflow-app-${terraform.workspace}-${count.index + 1}"
    Environment = terraform.workspace
  }
}

resource "aws_db_instance" "main" {
  identifier     = "payflow-db-${terraform.workspace}"
  engine         = "postgres"
  instance_class = "db.t3.small"
  multi_az       = local.current_config.multi_az

  tags = {
    Environment = terraform.workspace
  }
}
```

**💡 Hint**: Workspaces are good for simple environment separation, but separate directories are better for production.

#### Workspace-Specific Backend

```hcl
terraform {
  backend "s3" {
    bucket = "payflow-terraform-state"
    key    = "terraform.tfstate"  # Workspace name automatically appended
    region = "us-east-1"
    
    # State files stored as:
    # - env:/dev/terraform.tfstate
    # - env:/staging/terraform.tfstate
    # - env:/prod/terraform.tfstate
  }
}
```

**💡 Hint**: S3 backend automatically organizes state files by workspace.

---

## 11. Import & Migration

### What Import Enables

Bring existing infrastructure under Terraform management.

### Capabilities

| Capability | Description | Use Case |
|------------|-------------|---------|
| **Resource Import** | Import existing resources | Adopt existing infra |
| **State Migration** | Move state between backends | Backend changes |
| **Resource Moving** | Reorganize state | Refactoring |
| **State Removal** | Remove from management | Decomission |

### Examples

#### Importing Resources

```bash
# Import existing VPC
terraform import aws_vpc.main vpc-12345678

# Import EC2 instance
terraform import aws_instance.app i-1234567890abcdef0

# Import S3 bucket
terraform import aws_s3_bucket.data my-existing-bucket

# Import RDS instance
terraform import aws_db_instance.main payflow-prod-db

# Import security group
terraform import aws_security_group.app sg-12345678
```

**Workflow:**
```bash
# 1. Write configuration for existing resource
cat > main.tf <<EOF
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  # Add other attributes after import
}
EOF

# 2. Import the resource
terraform import aws_vpc.main vpc-12345678

# 3. Verify state
terraform state show aws_vpc.main

# 4. Update configuration to match actual resource
# 5. Run plan to verify no changes
terraform plan  # Should show no changes
```

**💡 Hint**: Always run `terraform plan` after import to ensure configuration matches reality.

#### Bulk Import Script

```bash
#!/bin/bash
# import-existing-infra.sh

# Import VPC
terraform import aws_vpc.main vpc-12345678

# Import subnets
terraform import 'aws_subnet.public[0]' subnet-11111111
terraform import 'aws_subnet.public[1]' subnet-22222222
terraform import 'aws_subnet.public[2]' subnet-33333333

# Import security groups
terraform import aws_security_group.alb sg-aaaaaaaa
terraform import aws_security_group.app sg-bbbbbbbb
terraform import aws_security_group.db sg-cccccccc

# Import load balancer
terraform import aws_lb.main arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/payflow-alb/1234567890abcdef

# Import RDS
terraform import aws_db_instance.main payflow-prod-db

echo "Import complete! Run 'terraform plan' to verify."
```

**💡 Hint**: Create import scripts for bulk imports to ensure consistency.

#### State Migration

```bash
# Migrate from local to S3 backend

# 1. Current state is local
terraform state list

# 2. Add backend configuration
cat > backend.tf <<EOF
terraform {
  backend "s3" {
    bucket = "payflow-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}
EOF

# 3. Initialize with migration
terraform init -migrate-state

# 4. Verify migration
terraform state list
```

**💡 Hint**: Always backup state before migration: `cp terraform.tfstate terraform.tfstate.backup`

---

## 12. Testing & Validation

### What Testing Capabilities Exist

Validate and test Terraform configurations before applying.

### Capabilities

| Capability | Description | Tool |
|------------|-------------|------|
| **Syntax Validation** | Check HCL syntax | `terraform validate` |
| **Formatting** | Standardize code style | `terraform fmt` |
| **Plan Testing** | Preview changes | `terraform plan` |
| **Policy Validation** | Enforce policies | Sentinel, OPA |
| **Security Scanning** | Find vulnerabilities | Checkov, tfsec |
| **Unit Testing** | Test modules | Terratest |
| **Integration Testing** | Test full stacks | Kitchen-Terraform |

### Examples

#### Basic Validation

```bash
# Format code
terraform fmt -recursive

# Validate syntax
terraform validate

# Check for errors
echo $?  # 0 = success, non-zero = error
```

#### Linting with tflint

```bash
# Install tflint
curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Create config
cat > .tflint.hcl <<EOF
plugin "aws" {
  enabled = true
  version = "0.21.1"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

rule "terraform_naming_convention" {
  enabled = true
}

rule "terraform_deprecated_interpolation" {
  enabled = true
}
EOF

# Run linter
tflint --init
tflint
```

**💡 Hint**: Integrate tflint into CI/CD to catch issues early.

#### Security Scanning with Checkov

```bash
# Install checkov
pip install checkov

# Scan Terraform files
checkov -d .

# Scan specific file
checkov -f main.tf

# Output JSON for CI/CD
checkov -d . -o json > checkov-results.json

# Skip specific checks
checkov -d . --skip-check CKV_AWS_20,CKV_AWS_21
```

**Example output:**
```
Check: CKV_AWS_20: "S3 Bucket has an ACL defined which allows public READ access."
	FAILED for resource: aws_s3_bucket.public_assets
	File: /main.tf:45-52

Check: CKV_AWS_23: "Ensure every security groups rule has a description"
	PASSED for resource: aws_security_group.app
```

**💡 Hint**: Use Checkov in CI/CD to enforce security best practices.

#### Unit Testing with Terratest

```go
// test/vpc_test.go
package test

import (
	"testing"
	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestVPCModule(t *testing.T) {
	terraformOptions := &terraform.Options{
		TerraformDir: "../modules/vpc",
		Vars: map[string]interface{}{
			"vpc_cidr":    "10.0.0.0/16",
			"environment": "test",
		},
	}

	defer terraform.Destroy(t, terraformOptions)
	terraform.InitAndApply(t, terraformOptions)

	vpcID := terraform.Output(t, terraformOptions, "vpc_id")
	assert.NotEmpty(t, vpcID)
}
```

**💡 Hint**: Use Terratest for automated testing of modules in CI/CD.

---

## 13. Security & Secrets

### What Security Features Exist

Protect sensitive data and enforce security policies.

### Capabilities

| Capability | Description | Tool |
|------------|-------------|------|
| **Sensitive Variables** | Hide secrets in output | `sensitive = true` |
| **State Encryption** | Encrypt state files | S3 encryption |
| **Secrets Management** | External secret stores | AWS Secrets Manager |
| **Policy Enforcement** | Enforce compliance | Sentinel, OPA |
| **Audit Logging** | Track changes | CloudTrail |

### Examples

#### Sensitive Variables

```hcl
variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

output "database_endpoint" {
  value     = aws_db_instance.main.endpoint
  sensitive = true
}

# Won't show in console
# terraform apply
# ...
# database_endpoint = <sensitive>
```

#### AWS Secrets Manager Integration

```hcl
# Store secret in Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name = "payflow/db/master-password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}

# Retrieve secret
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
}

# Use in RDS
resource "aws_db_instance" "main" {
  identifier     = "payflow-db"
  engine         = "postgres"
  username       = "admin"
  password       = jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["password"]
  
  # Or if secret is plain string:
  # password = data.aws_secretsmanager_secret_version.db_password.secret_string
}
```

**💡 Hint**: Never commit secrets to version control; use Secrets Manager or environment variables.

#### Encrypted State

```hcl
terraform {
  backend "s3" {
    bucket         = "payflow-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true  # Enable encryption at rest
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
    dynamodb_table = "payflow-terraform-locks"
  }
}
```

**💡 Hint**: Always enable encryption for state files containing sensitive data.

---

## 14. Multi-Cloud Support

### What Providers Enable

Terraform supports 3000+ providers for multi-cloud and SaaS platforms.

### Major Providers

| Provider | Use Case | Resources |
|----------|----------|-----------|
| **AWS** | Amazon Web Services | 1000+ resources |
| **Azure** | Microsoft Azure | 1000+ resources |
| **GCP** | Google Cloud Platform | 500+ resources |
| **Kubernetes** | Container orchestration | 100+ resources |
| **GitHub** | Code repository management | 50+ resources |
| **Datadog** | Monitoring | 100+ resources |

### Examples

#### Multi-Cloud Configuration

```hcl
# providers.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

provider "azurerm" {
  features {}
}

provider "google" {
  project = "my-project"
  region  = "us-central1"
}

# AWS resources
resource "aws_s3_bucket" "data" {
  bucket = "payflow-data-aws"
}

# Azure resources
resource "azurerm_storage_account" "data" {
  name                     = "payflowdataazure"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = "East US"
  account_tier             = "Standard"
  account_replication_type = "GRS"
}

# GCP resources
resource "google_storage_bucket" "data" {
  name     = "payflow-data-gcp"
  location = "US"
}
```

**💡 Hint**: Use provider aliases for multi-region deployments within the same cloud.

#### Multiple AWS Regions

```hcl
provider "aws" {
  alias  = "us_east"
  region = "us-east-1"
}

provider "aws" {
  alias  = "us_west"
  region = "us-west-2"
}

# Primary region resources
resource "aws_vpc" "primary" {
  provider   = aws.us_east
  cidr_block = "10.0.0.0/16"
}

# DR region resources
resource "aws_vpc" "dr" {
  provider   = aws.us_west
  cidr_block = "10.1.0.0/16"
}

# Cross-region replication
resource "aws_s3_bucket_replication_configuration" "replication" {
  provider = aws.us_east
  
  role   = aws_iam_role.replication.arn
  bucket = aws_s3_bucket.primary.id

  rule {
    id     = "replicate-to-dr"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.dr.arn
      storage_class = "STANDARD_IA"
    }
  }
}
```

**💡 Hint**: Use provider aliases for disaster recovery and multi-region architectures.

---

## 15. Advanced Features

### Dynamic Blocks

```hcl
# Dynamic security group rules
resource "aws_security_group" "app" {
  name   = "payflow-app-sg"
  vpc_id = aws_vpc.main.id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
      description = ingress.value.description
    }
  }
}

# variables.tf
variable "ingress_rules" {
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
    description = string
  }))
  default = [
    {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTP from anywhere"
    },
    {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTPS from anywhere"
    }
  ]
}
```

### For Expressions

```hcl
# Create map from list
locals {
  subnet_map = {
    for subnet in aws_subnet.private :
    subnet.availability_zone => subnet.id
  }
  
  # Filter and transform
  large_instances = [
    for instance in aws_instance.app :
    instance.id if instance.instance_type == "t3.large"
  ]
}
```

### Conditional Expressions

```hcl
resource "aws_db_instance" "main" {
  identifier     = "payflow-db"
  engine         = "postgres"
  instance_class = var.instance_class
  
  # Multi-AZ only in production
  multi_az = var.environment == "prod" ? true : false
  
  # Backup retention based on environment
  backup_retention_period = var.environment == "prod" ? 30 : 7
  
  # Storage encryption
  storage_encrypted = var.environment != "dev"
}
```

### Functions

```hcl
locals {
  # String functions
  upper_env = upper(var.environment)
  lower_env = lower(var.environment)
  
  # Collection functions
  all_subnets = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
  unique_azs  = distinct([for subnet in aws_subnet.public : subnet.availability_zone])
  
  # Numeric functions
  max_instances = max(var.min_size, var.desired_capacity)
  
  # Encoding functions
  user_data = base64encode(file("user-data.sh"))
  
  # Date/time functions
  timestamp = formatdate("YYYY-MM-DD", timestamp())
  
  # Networking functions
  subnet_cidrs = [for i in range(3) : cidrsubnet("10.0.0.0/16", 8, i)]
}
```

---

## Quick Reference Commands

```bash
# Initialization
terraform init                    # Initialize working directory
terraform init -upgrade           # Upgrade providers

# Planning
terraform plan                    # Preview changes
terraform plan -out=tfplan        # Save plan to file
terraform plan -target=resource   # Plan specific resource

# Applying
terraform apply                   # Apply changes
terraform apply tfplan            # Apply saved plan
terraform apply -auto-approve     # Skip confirmation

# Destroying
terraform destroy                 # Destroy all resources
terraform destroy -target=resource # Destroy specific resource

# State Management
terraform state list              # List resources
terraform state show resource     # Show resource details
terraform state mv source dest    # Move resource
terraform state rm resource       # Remove from state
terraform state pull              # Download state
terraform state push              # Upload state

# Workspace Management
terraform workspace list          # List workspaces
terraform workspace new name      # Create workspace
terraform workspace select name   # Switch workspace

# Output
terraform output                  # Show all outputs
terraform output name             # Show specific output
terraform output -json            # JSON format

# Validation
terraform validate                # Validate syntax
terraform fmt                     # Format code
terraform fmt -check              # Check formatting

# Other
terraform graph                   # Generate dependency graph
terraform show                    # Show current state
terraform version                 # Show version
```

---

## Best Practices Summary

1. **Always use remote state** with encryption and locking
2. **Pin provider versions** in production
3. **Use modules** for reusable components
4. **Enable state encryption** for sensitive data
5. **Use workspaces or separate directories** for environments
6. **Implement CI/CD** for automated testing and deployment
7. **Use data sources** instead of hardcoding values
8. **Enable prevent_destroy** for critical resources
9. **Use variables and outputs** for flexibility
10. **Run security scans** (Checkov, tfsec) regularly

---

**Related Documents:**
- [Terraform Workflow Diagrams](terraform-workflow-diagrams.md)
- [Architecture Overview](architecture.md)
- [Security Best Practices](security-best-practices.md)
