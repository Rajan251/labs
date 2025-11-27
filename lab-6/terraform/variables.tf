# ============================================================================
# Terraform Variable Definitions
# ============================================================================
# This file defines all configurable parameters for the infrastructure.
# Override values in terraform.tfvars or via command line.
# ============================================================================

# ============================================================================
# General Configuration
# ============================================================================

variable "project_name" {
  description = "Name of the project, used for resource naming"
  type        = string
  default     = "terraform-ansible"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "owner" {
  description = "Owner of the infrastructure"
  type        = string
  default     = "DevOps Team"
}

# ============================================================================
# AWS Configuration
# ============================================================================

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

# ============================================================================
# Network Configuration
# ============================================================================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "subnet_count" {
  description = "Number of subnets to create"
  type        = number
  default     = 2
  
  validation {
    condition     = var.subnet_count >= 1 && var.subnet_count <= 6
    error_message = "Subnet count must be between 1 and 6."
  }
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH to instances (use your IP/32 for security)"
  type        = string
  default     = "0.0.0.0/0" # WARNING: Change this to your IP for production!
}

# ============================================================================
# EC2 Instance Configuration
# ============================================================================

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
  
  validation {
    condition     = can(regex("^t[2-3]\\.(nano|micro|small|medium|large)", var.instance_type))
    error_message = "Instance type must be a valid t2 or t3 instance type."
  }
}

variable "web_instance_count" {
  description = "Number of web server instances to create"
  type        = number
  default     = 2
  
  validation {
    condition     = var.web_instance_count >= 1 && var.web_instance_count <= 10
    error_message = "Web instance count must be between 1 and 10."
  }
}

variable "app_instance_count" {
  description = "Number of application server instances to create"
  type        = number
  default     = 1
  
  validation {
    condition     = var.app_instance_count >= 0 && var.app_instance_count <= 10
    error_message = "App instance count must be between 0 and 10."
  }
}

# ============================================================================
# SSH Key Configuration
# ============================================================================

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/terraform-key.pub"
}

variable "ssh_private_key_path" {
  description = "Path to SSH private key file (for Ansible)"
  type        = string
  default     = "~/.ssh/terraform-key"
}

# ============================================================================
# Ansible Configuration
# ============================================================================

variable "ansible_user" {
  description = "SSH user for Ansible connections"
  type        = string
  default     = "ubuntu"
}

# ============================================================================
# Tags
# ============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
