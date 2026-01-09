variable "environment" {
  description = "Environment name"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs of private subnets"
  type        = list(string)
}

variable "db_security_group_id" {
  description = "ID of database security group"
  type        = string
}

variable "key_name" {
  description = "EC2 key pair name"
  type        = string
}

variable "instance_type" {
  description = "Instance type for MongoDB servers"
  type        = string
  default     = "t3.large"
}

variable "mongodb_admin_password" {
  description = "MongoDB admin password"
  type        = string
  sensitive   = true
}

variable "mongodb_app_password" {
  description = "MongoDB application user password"
  type        = string
  sensitive   = true
}
