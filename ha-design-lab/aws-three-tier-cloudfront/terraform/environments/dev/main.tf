# Main Terraform Configuration for Development Environment

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data source for latest Amazon Linux 2 AMI
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

# Networking Module
module "networking" {
  source = "../../modules/networking"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  enable_nat_gateway = var.enable_nat_gateway
  enable_flow_logs   = var.enable_flow_logs
}

# Security Module
module "security" {
  source = "../../modules/security"

  project_name           = var.project_name
  environment            = var.environment
  vpc_id                 = module.networking.vpc_id
  vpc_cidr               = module.networking.vpc_cidr
  public_subnet_ids      = module.networking.public_subnet_ids
  private_app_subnet_ids = module.networking.private_app_subnet_ids
  private_db_subnet_ids  = module.networking.private_db_subnet_ids
  vpn_allowed_ips        = var.vpn_allowed_ips
  app_port               = var.app_port
  db_port                = var.db_port
}

# Load Balancer Module
module "loadbalancer" {
  source = "../../modules/loadbalancer"

  project_name              = var.project_name
  environment               = var.environment
  vpc_id                    = module.networking.vpc_id
  public_subnet_ids         = module.networking.public_subnet_ids
  alb_security_group_id     = module.security.alb_security_group_id
  app_port                  = var.app_port
  health_check_path         = var.health_check_path
  enable_deletion_protection = var.enable_deletion_protection
  ssl_certificate_arn       = var.ssl_certificate_arn
}

# Compute Module
module "compute" {
  source = "../../modules/compute"

  project_name           = var.project_name
  environment            = var.environment
  key_name               = var.key_name
  private_app_subnet_ids = module.networking.private_app_subnet_ids
  private_db_subnet_ids  = module.networking.private_db_subnet_ids
  app_security_group_id  = module.security.app_security_group_id
  db_security_group_id   = module.security.db_security_group_id
  target_group_arn       = module.loadbalancer.target_group_arn

  # Application Server Configuration
  app_ami_id           = data.aws_ami.amazon_linux_2.id
  app_instance_type    = var.app_instance_type
  app_volume_size      = var.app_volume_size
  app_min_size         = var.app_min_size
  app_max_size         = var.app_max_size
  app_desired_capacity = var.app_desired_capacity
  app_user_data        = file("${path.module}/../../../configs/user-data/app-server.sh")

  # Database Server Configuration
  db_ami_id           = data.aws_ami.amazon_linux_2.id
  db_instance_type    = var.db_instance_type
  db_volume_size      = var.db_volume_size
  db_min_size         = var.db_min_size
  db_max_size         = var.db_max_size
  db_desired_capacity = var.db_desired_capacity
  db_user_data        = file("${path.module}/../../../configs/user-data/db-server.sh")
}

# VPN Module
module "vpn" {
  source = "../../modules/vpn"

  project_name          = var.project_name
  environment           = var.environment
  vpn_ami_id            = data.aws_ami.amazon_linux_2.id
  vpn_instance_type     = var.vpn_instance_type
  key_name              = var.key_name
  public_subnet_ids     = module.networking.public_subnet_ids
  vpn_security_group_id = module.security.vpn_security_group_id
  vpn_user_data         = file("${path.module}/../../../configs/user-data/vpn-server.sh")
}

# CDN Module
module "cdn" {
  source = "../../modules/cdn"

  project_name        = var.project_name
  environment         = var.environment
  alb_dns_name        = module.loadbalancer.alb_dns_name
  price_class         = var.cloudfront_price_class
  domain_aliases      = var.domain_aliases
  ssl_certificate_arn = var.cloudfront_ssl_certificate_arn
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"

  project_name              = var.project_name
  environment               = var.environment
  alert_email               = var.alert_email
  app_asg_name              = module.compute.app_asg_name
  db_asg_name               = module.compute.db_asg_name
  app_scale_up_policy_arn   = module.compute.app_scale_up_policy_arn
  app_scale_down_policy_arn = module.compute.app_scale_down_policy_arn
  db_scale_up_policy_arn    = module.compute.db_scale_up_policy_arn
  db_scale_down_policy_arn  = module.compute.db_scale_down_policy_arn
  alb_arn_suffix            = split("/", module.loadbalancer.alb_arn)[1]
  target_group_arn_suffix   = split(":", module.loadbalancer.target_group_arn)[5]
}
