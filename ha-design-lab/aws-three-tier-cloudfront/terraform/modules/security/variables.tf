variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "IDs of public subnets"
  type        = list(string)
}

variable "private_app_subnet_ids" {
  description = "IDs of private application subnets"
  type        = list(string)
}

variable "private_db_subnet_ids" {
  description = "IDs of private database subnets"
  type        = list(string)
}

variable "vpn_allowed_ips" {
  description = "List of CIDR blocks allowed to access VPN"
  type        = list(string)
  default     = ["0.0.0.0/0"]
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
