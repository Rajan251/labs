# AWS Two-Tier Architecture - Terraform Configuration

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
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "TwoTierArchitecture"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"
  
  environment         = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

# Security Groups Module
module "security" {
  source = "../../modules/security"
  
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  your_ip     = var.your_ip
}

# Load Balancer Module
module "loadbalancer" {
  source = "../../modules/loadbalancer"
  
  environment        = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  alb_security_group_id = module.security.alb_security_group_id
}

# Database Module (MongoDB)
module "database" {
  source = "../../modules/database"
  
  environment           = var.environment
  private_subnet_ids    = module.vpc.private_subnet_ids
  db_security_group_id  = module.security.db_security_group_id
  key_name             = var.key_name
  instance_type        = var.db_instance_type
  mongodb_admin_password = var.mongodb_admin_password
  mongodb_app_password   = var.mongodb_app_password
}

# Auto-Scaling Module
module "autoscaling" {
  source = "../../modules/autoscaling"
  
  environment              = var.environment
  vpc_id                  = module.vpc.vpc_id
  public_subnet_ids       = module.vpc.public_subnet_ids
  webapp_security_group_id = module.security.webapp_security_group_id
  target_group_arn        = module.loadbalancer.target_group_arn
  key_name                = var.key_name
  instance_type           = var.webapp_instance_type
  min_size                = var.asg_min_size
  max_size                = var.asg_max_size
  desired_capacity        = var.asg_desired_capacity
  
  mongodb_primary_ip      = module.database.mongodb_primary_private_ip
  mongodb_secondary_ip    = module.database.mongodb_secondary_private_ip
  mongodb_app_password    = var.mongodb_app_password
}
