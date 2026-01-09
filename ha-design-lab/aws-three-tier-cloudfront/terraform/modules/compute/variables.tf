variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "key_name" {
  description = "Name of the SSH key pair"
  type        = string
}

variable "private_app_subnet_ids" {
  description = "IDs of private application subnets"
  type        = list(string)
}

variable "private_db_subnet_ids" {
  description = "IDs of private database subnets"
  type        = list(string)
}

variable "app_security_group_id" {
  description = "ID of application server security group"
  type        = string
}

variable "db_security_group_id" {
  description = "ID of database server security group"
  type        = string
}

variable "target_group_arn" {
  description = "ARN of the ALB target group"
  type        = string
}

# Application Server Configuration
variable "app_ami_id" {
  description = "AMI ID for application servers"
  type        = string
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

variable "app_user_data" {
  description = "User data script for application servers"
  type        = string
  default     = ""
}

# Database Server Configuration
variable "db_ami_id" {
  description = "AMI ID for database servers"
  type        = string
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

variable "db_user_data" {
  description = "User data script for database servers"
  type        = string
  default     = ""
}
