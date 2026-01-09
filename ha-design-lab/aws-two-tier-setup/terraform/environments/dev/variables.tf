# Variables for Two-Tier Architecture

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "your_ip" {
  description = "Your IP address for SSH access (CIDR notation)"
  type        = string
  # Get your IP: curl ifconfig.me
  default     = "0.0.0.0/0" # CHANGE THIS TO YOUR IP
}

variable "key_name" {
  description = "EC2 key pair name"
  type        = string
  default     = "two-tier-key"
}

# Database Variables
variable "db_instance_type" {
  description = "Instance type for MongoDB servers"
  type        = string
  default     = "t3.large"
}

variable "mongodb_admin_password" {
  description = "MongoDB admin password"
  type        = string
  sensitive   = true
  # Set via environment variable: TF_VAR_mongodb_admin_password
}

variable "mongodb_app_password" {
  description = "MongoDB application user password"
  type        = string
  sensitive   = true
  # Set via environment variable: TF_VAR_mongodb_app_password
}

# Web/App Variables
variable "webapp_instance_type" {
  description = "Instance type for web/app servers"
  type        = string
  default     = "t3.medium"
}

variable "asg_min_size" {
  description = "Minimum number of instances in ASG"
  type        = number
  default     = 2
}

variable "asg_max_size" {
  description = "Maximum number of instances in ASG"
  type        = number
  default     = 10
}

variable "asg_desired_capacity" {
  description = "Desired number of instances in ASG"
  type        = number
  default     = 2
}

variable "cpu_target_value" {
  description = "Target CPU utilization for auto-scaling"
  type        = number
  default     = 70
}
