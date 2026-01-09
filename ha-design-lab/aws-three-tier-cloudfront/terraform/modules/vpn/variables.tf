variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "vpn_ami_id" {
  description = "AMI ID for VPN server"
  type        = string
}

variable "vpn_instance_type" {
  description = "Instance type for VPN server"
  type        = string
  default     = "t3.small"
}

variable "key_name" {
  description = "Name of the SSH key pair"
  type        = string
}

variable "public_subnet_ids" {
  description = "IDs of public subnets"
  type        = list(string)
}

variable "vpn_security_group_id" {
  description = "ID of VPN security group"
  type        = string
}

variable "vpn_user_data" {
  description = "User data script for VPN server"
  type        = string
  default     = ""
}
