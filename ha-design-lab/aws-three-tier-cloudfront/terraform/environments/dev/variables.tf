# Project Configuration
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "three-tier-app"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Network Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway"
  type        = bool
  default     = true
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

# Security Configuration
variable "vpn_allowed_ips" {
  description = "List of CIDR blocks allowed to access VPN"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Change this to your IP range
}

variable "app_port" {
  description = "Application server port"
  type        = number
  default     = 8080
}

variable "db_port" {
  description = "Database server port"
  type        = number
  default     = 27017
}

# Compute Configuration
variable "key_name" {
  description = "Name of the SSH key pair"
  type        = string
}

variable "vpn_instance_type" {
  description = "Instance type for VPN server"
  type        = string
  default     = "t3.small"
}

variable "app_instance_type" {
  description = "Instance type for application servers"
  type        = string
  default     = "t3.medium"
}

variable "app_volume_size" {
  description = "EBS volume size for application servers (GB)"
  type        = number
  default     = 20
}

variable "app_min_size" {
  description = "Minimum number of application servers"
  type        = number
  default     = 2
}

variable "app_max_size" {
  description = "Maximum number of application servers"
  type        = number
  default     = 6
}

variable "app_desired_capacity" {
  description = "Desired number of application servers"
  type        = number
  default     = 2
}

variable "db_instance_type" {
  description = "Instance type for database servers"
  type        = string
  default     = "t3.large"
}

variable "db_volume_size" {
  description = "EBS volume size for database servers (GB)"
  type        = number
  default     = 50
}

variable "db_min_size" {
  description = "Minimum number of database servers"
  type        = number
  default     = 2
}

variable "db_max_size" {
  description = "Maximum number of database servers"
  type        = number
  default     = 4
}

variable "db_desired_capacity" {
  description = "Desired number of database servers"
  type        = number
  default     = 2
}

# Load Balancer Configuration
variable "health_check_path" {
  description = "Health check path for ALB"
  type        = string
  default     = "/health"
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for ALB"
  type        = bool
  default     = false
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for ALB HTTPS listener"
  type        = string
  default     = ""
}

# CloudFront Configuration
variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}

variable "domain_aliases" {
  description = "List of domain aliases for CloudFront"
  type        = list(string)
  default     = []
}

variable "cloudfront_ssl_certificate_arn" {
  description = "ARN of ACM certificate for CloudFront (must be in us-east-1)"
  type        = string
  default     = ""
}

# Monitoring Configuration
variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = ""
}
