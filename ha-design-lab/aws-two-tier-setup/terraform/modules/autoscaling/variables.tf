variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "IDs of public subnets"
  type        = list(string)
}

variable "webapp_security_group_id" {
  description = "ID of web/app security group"
  type        = string
}

variable "target_group_arn" {
  description = "ARN of the target group"
  type        = string
}

variable "key_name" {
  description = "EC2 key pair name"
  type        = string
}

variable "instance_type" {
  description = "Instance type for web/app servers"
  type        = string
  default     = "t3.medium"
}

variable "min_size" {
  description = "Minimum number of instances"
  type        = number
  default     = 2
}

variable "max_size" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "desired_capacity" {
  description = "Desired number of instances"
  type        = number
  default     = 2
}

variable "mongodb_primary_ip" {
  description = "Private IP of MongoDB primary"
  type        = string
}

variable "mongodb_secondary_ip" {
  description = "Private IP of MongoDB secondary"
  type        = string
}

variable "mongodb_app_password" {
  description = "MongoDB application user password"
  type        = string
  sensitive   = true
}

variable "alb_full_name" {
  description = "Full name of the ALB for metrics"
  type        = string
  default     = ""
}

variable "target_group_full_name" {
  description = "Full name of the target group for metrics"
  type        = string
  default     = ""
}
