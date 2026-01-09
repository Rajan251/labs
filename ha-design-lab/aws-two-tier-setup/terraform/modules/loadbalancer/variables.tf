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

variable "alb_security_group_id" {
  description = "ID of ALB security group"
  type        = string
}

# Optional: Uncomment if using HTTPS
# variable "certificate_arn" {
#   description = "ARN of SSL certificate"
#   type        = string
#   default     = ""
# }
