variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "your_ip" {
  description = "Your IP address for SSH access (CIDR notation)"
  type        = string
}
