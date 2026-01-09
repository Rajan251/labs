# Complete Terraform Modules Reference

This document contains all the Terraform modules for the PayFlow Solutions infrastructure. Each module is production-ready and follows best practices.

## Module Structure

```
modules/
├── vpc/          # VPC, subnets, routing
├── security/     # Security groups, NACLs
├── compute/      # EC2, ASG, Launch Templates
├── alb/          # Application Load Balancer
├── rds/          # RDS PostgreSQL
├── s3/           # S3 buckets
├── iam/          # IAM roles and policies
├── monitoring/   # CloudWatch, SNS
└── bastion/      # Bastion host
```

---

## VPC Module

### modules/vpc/main.tf

```hcl
# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-vpc-${var.environment}"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-igw-${var.environment}"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(var.availability_zones)
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index + 1)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-subnet-public-${count.index + 1}-${var.environment}"
    Tier = "public"
  })
}

# Private Subnets (Application)
resource "aws_subnet" "private" {
  count = length(var.availability_zones)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 11)
  availability_zone = var.availability_zones[count.index]
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-subnet-private-${count.index + 1}-${var.environment}"
    Tier = "private"
  })
}

# Database Subnets
resource "aws_subnet" "database" {
  count = length(var.availability_zones)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 21)
  availability_zone = var.availability_zones[count.index]
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-subnet-database-${count.index + 1}-${var.environment}"
    Tier = "database"
  })
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0
  domain = "vpc"
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-eip-nat-${count.index + 1}-${var.environment}"
  })
  
  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[var.single_nat_gateway ? 0 : count.index].id
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-nat-${count.index + 1}-${var.environment}"
  })
  
  depends_on = [aws_internet_gateway.main]
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-rt-public-${var.environment}"
  })
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
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-rt-private-${count.index + 1}-${var.environment}"
  })
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
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-rt-database-${var.environment}"
  })
}

# Database Route Table Associations
resource "aws_route_table_association" "database" {
  count = length(aws_subnet.database)
  
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database.id
}

# VPC Flow Logs
resource "aws_flow_log" "main" {
  count = var.enable_flow_logs ? 1 : 0
  
  vpc_id          = aws_vpc.main.id
  traffic_type    = "ALL"
  iam_role_arn    = aws_iam_role.flow_logs[0].arn
  log_destination = aws_cloudwatch_log_group.flow_logs[0].arn
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-flow-logs-${var.environment}"
  })
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0
  
  name              = "/aws/vpc/${var.project_name}-${var.environment}"
  retention_in_days = 30
  
  tags = var.common_tags
}

resource "aws_iam_role" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0
  
  name = "${var.project_name}-vpc-flow-logs-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
  
  tags = var.common_tags
}

resource "aws_iam_role_policy" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0
  
  name = "flow-logs-policy"
  role = aws_iam_role.flow_logs[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}
```

### modules/vpc/variables.tf

```hcl
variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use single NAT Gateway (cost optimization for dev)"
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
```

### modules/vpc/outputs.tf

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

output "internet_gateway_id" {
  description = "Internet Gateway ID"
  value       = aws_internet_gateway.main.id
}
```

---

## Security Module

### modules/security/main.tf

```hcl
# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-sg-alb-${var.environment}"
  description = "Security group for Application Load Balancer"
  vpc_id      = var.vpc_id
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-sg-alb-${var.environment}"
  })
}

resource "aws_security_group_rule" "alb_http_ingress" {
  type              = "ingress"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.alb.id
  description       = "Allow HTTP from Internet"
}

resource "aws_security_group_rule" "alb_https_ingress" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.alb.id
  description       = "Allow HTTPS from Internet"
}

resource "aws_security_group_rule" "alb_app_egress" {
  type                     = "egress"
  from_port                = var.app_port
  to_port                  = var.app_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.app.id
  security_group_id        = aws_security_group.alb.id
  description              = "Allow traffic to application servers"
}

# Application Security Group
resource "aws_security_group" "app" {
  name        = "${var.project_name}-sg-app-${var.environment}"
  description = "Security group for application servers"
  vpc_id      = var.vpc_id
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-sg-app-${var.environment}"
  })
}

resource "aws_security_group_rule" "app_alb_ingress" {
  type                     = "ingress"
  from_port                = var.app_port
  to_port                  = var.app_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
  security_group_id        = aws_security_group.app.id
  description              = "Allow traffic from ALB"
}

resource "aws_security_group_rule" "app_db_egress" {
  type                     = "egress"
  from_port                = var.db_port
  to_port                  = var.db_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.db.id
  security_group_id        = aws_security_group.app.id
  description              = "Allow traffic to database"
}

resource "aws_security_group_rule" "app_https_egress" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.app.id
  description       = "Allow HTTPS to Internet"
}

# Database Security Group
resource "aws_security_group" "db" {
  name        = "${var.project_name}-sg-db-${var.environment}"
  description = "Security group for RDS database"
  vpc_id      = var.vpc_id
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-sg-db-${var.environment}"
  })
}

resource "aws_security_group_rule" "db_app_ingress" {
  type                     = "ingress"
  from_port                = var.db_port
  to_port                  = var.db_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.app.id
  security_group_id        = aws_security_group.db.id
  description              = "Allow traffic from application servers"
}

# Bastion Security Group
resource "aws_security_group" "bastion" {
  count = var.enable_bastion ? 1 : 0
  
  name        = "${var.project_name}-sg-bastion-${var.environment}"
  description = "Security group for bastion host"
  vpc_id      = var.vpc_id
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-sg-bastion-${var.environment}"
  })
}

resource "aws_security_group_rule" "bastion_ssh_ingress" {
  count = var.enable_bastion ? 1 : 0
  
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = var.bastion_allowed_cidrs
  security_group_id = aws_security_group.bastion[0].id
  description       = "Allow SSH from allowed IPs"
}

resource "aws_security_group_rule" "bastion_app_egress" {
  count = var.enable_bastion ? 1 : 0
  
  type                     = "egress"
  from_port                = 22
  to_port                  = 22
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.app.id
  security_group_id        = aws_security_group.bastion[0].id
  description              = "Allow SSH to application servers"
}

# Allow SSH from bastion to app servers
resource "aws_security_group_rule" "app_bastion_ingress" {
  count = var.enable_bastion ? 1 : 0
  
  type                     = "ingress"
  from_port                = 22
  to_port                  = 22
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.bastion[0].id
  security_group_id        = aws_security_group.app.id
  description              = "Allow SSH from bastion"
}
```

### modules/security/variables.tf

```hcl
variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "app_port" {
  description = "Application port"
  type        = number
  default     = 8080
}

variable "db_port" {
  description = "Database port"
  type        = number
  default     = 5432
}

variable "enable_bastion" {
  description = "Enable bastion host security group"
  type        = bool
  default     = false
}

variable "bastion_allowed_cidrs" {
  description = "CIDR blocks allowed to SSH to bastion"
  type        = list(string)
  default     = []
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
```

### modules/security/outputs.tf

```hcl
output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "app_security_group_id" {
  description = "Application security group ID"
  value       = aws_security_group.app.id
}

output "db_security_group_id" {
  description = "Database security group ID"
  value       = aws_security_group.db.id
}

output "bastion_security_group_id" {
  description = "Bastion security group ID"
  value       = var.enable_bastion ? aws_security_group.bastion[0].id : null
}
```

---

## Compute Module

### modules/compute/main.tf

```hcl
# Launch Template
resource "aws_launch_template" "app" {
  name_prefix   = "${var.project_name}-lt-app-${var.environment}-"
  image_id      = var.ami_id
  instance_type = var.instance_type
  
  vpc_security_group_ids = [var.security_group_id]
  
  iam_instance_profile {
    name = aws_iam_instance_profile.app.name
  }
  
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    app_version = var.app_version
    environment = var.environment
    region      = var.region
  }))
  
  block_device_mappings {
    device_name = "/dev/xvda"
    
    ebs {
      volume_size           = var.root_volume_size
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }
  
  monitoring {
    enabled = true
  }
  
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # IMDSv2
    http_put_response_hop_limit = 1
  }
  
  tag_specifications {
    resource_type = "instance"
    
    tags = merge(var.common_tags, {
      Name = "${var.project_name}-ec2-app-${var.environment}"
    })
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "app" {
  name                = "${var.project_name}-asg-app-${var.environment}"
  vpc_zone_identifier = var.subnet_ids
  target_group_arns   = [var.target_group_arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300
  
  min_size         = var.asg_min_size
  max_size         = var.asg_max_size
  desired_capacity = var.asg_desired_size
  
  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }
  
  instance_refresh {
    strategy = "Rolling"
    
    preferences {
      min_healthy_percentage = 90
      instance_warmup        = 300
    }
  }
  
  enabled_metrics = [
    "GroupDesiredCapacity",
    "GroupInServiceInstances",
    "GroupMaxSize",
    "GroupMinSize",
    "GroupPendingInstances",
    "GroupStandbyInstances",
    "GroupTerminatingInstances",
    "GroupTotalInstances"
  ]
  
  tag {
    key                 = "Name"
    value               = "${var.project_name}-asg-app-${var.environment}"
    propagate_at_launch = false
  }
  
  dynamic "tag" {
    for_each = var.common_tags
    
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}

# Target Tracking Scaling Policy
resource "aws_autoscaling_policy" "target_tracking" {
  name                   = "${var.project_name}-policy-target-tracking-${var.environment}"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"
  
  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = var.target_cpu_utilization
  }
}

# IAM Role for EC2 Instances
resource "aws_iam_role" "app" {
  name = "${var.project_name}-role-ec2-app-${var.environment}"
  
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
  
  tags = var.common_tags
}

# Attach SSM policy for Session Manager
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.app.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# CloudWatch Logs policy
resource "aws_iam_role_policy" "cloudwatch_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.app.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "app" {
  name = "${var.project_name}-profile-ec2-app-${var.environment}"
  role = aws_iam_role.app.name
  
  tags = var.common_tags
}
```

### modules/compute/user-data.sh

```bash
#!/bin/bash
set -e

# Update system
yum update -y

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Install application dependencies
yum install -y python3 python3-pip postgresql15

# Create application directory
mkdir -p /opt/payflow-app
cd /opt/payflow-app

# Download application (placeholder - replace with actual deployment)
echo "Deploying application version: ${app_version}"
echo "Environment: ${environment}"

# Create systemd service
cat > /etc/systemd/system/payflow-app.service <<EOF
[Unit]
Description=PayFlow Payment API
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/payflow-app
ExecStart=/usr/bin/python3 /opt/payflow-app/app.py
Restart=always
Environment="APP_VERSION=${app_version}"
Environment="ENVIRONMENT=${environment}"
Environment="AWS_REGION=${region}"

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable payflow-app
systemctl start payflow-app

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json <<EOF
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/payflow-app.log",
            "log_group_name": "/aws/ec2/payflow-app",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
EOF

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json

echo "Instance setup complete"
```

### modules/compute/variables.tf

```hcl
variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "ami_id" {
  description = "AMI ID for EC2 instances"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "security_group_id" {
  description = "Security group ID for instances"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for ASG"
  type        = list(string)
}

variable "target_group_arn" {
  description = "Target group ARN for ALB"
  type        = string
}

variable "asg_min_size" {
  description = "Minimum number of instances"
  type        = number
}

variable "asg_max_size" {
  description = "Maximum number of instances"
  type        = number
}

variable "asg_desired_size" {
  description = "Desired number of instances"
  type        = number
}

variable "target_cpu_utilization" {
  description = "Target CPU utilization for scaling"
  type        = number
  default     = 70
}

variable "app_version" {
  description = "Application version"
  type        = string
  default     = "v1.0.0"
}

variable "root_volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 20
}

variable "common_tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
```

### modules/compute/outputs.tf

```hcl
output "autoscaling_group_id" {
  description = "Auto Scaling Group ID"
  value       = aws_autoscaling_group.app.id
}

output "autoscaling_group_name" {
  description = "Auto Scaling Group name"
  value       = aws_autoscaling_group.app.name
}

output "launch_template_id" {
  description = "Launch Template ID"
  value       = aws_launch_template.app.id
}

output "iam_role_arn" {
  description = "IAM role ARN"
  value       = aws_iam_role.app.arn
}
```

---

*This document continues with ALB, RDS, S3, IAM, Monitoring, and Bastion modules. Due to length, the complete reference is provided in the project repository.*

## Quick Module Usage

### Example: Using VPC Module

```hcl
module "vpc" {
  source = "./modules/vpc"
  
  project_name       = "payflow"
  environment        = "prod"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  
  enable_nat_gateway  = true
  single_nat_gateway  = false  # Use 3 NAT GWs for HA
  enable_flow_logs    = true
  
  common_tags = {
    Project    = "payflow-platform"
    ManagedBy  = "terraform"
    CostCenter = "engineering"
  }
}
```

### Example: Complete Environment

```hcl
# environments/prod/main.tf

module "vpc" {
  source = "../../modules/vpc"
  # ... configuration
}

module "security" {
  source = "../../modules/security"
  
  vpc_id = module.vpc.vpc_id
  # ... configuration
}

module "alb" {
  source = "../../modules/alb"
  
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.public_subnet_ids
  security_group_id = module.security.alb_security_group_id
  # ... configuration
}

module "compute" {
  source = "../../modules/compute"
  
  subnet_ids        = module.vpc.private_subnet_ids
  security_group_id = module.security.app_security_group_id
  target_group_arn  = module.alb.target_group_arn
  # ... configuration
}

module "rds" {
  source = "../../modules/rds"
  
  subnet_ids        = module.vpc.database_subnet_ids
  security_group_id = module.security.db_security_group_id
  # ... configuration
}
```

## Next Steps

1. Review each module's variables and customize for your needs
2. Start with Lab 01 to deploy VPC module
3. Progress through labs to build complete infrastructure
4. Test operational scenarios from use-cases.md
