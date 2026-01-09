variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "domain_name" {
  description = "Domain name for Route 53"
  type        = string
}

variable "create_hosted_zone" {
  description = "Create Route 53 hosted zone"
  type        = bool
  default     = false
}

variable "create_cloudfront_record" {
  description = "Create CloudFront DNS record"
  type        = bool
  default     = false
}

variable "create_health_check" {
  description = "Create health check for ALB"
  type        = bool
  default     = false
}

variable "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  type        = string
  default     = ""
}

variable "cloudfront_hosted_zone_id" {
  description = "CloudFront hosted zone ID"
  type        = string
  default     = ""
}

variable "alb_dns_name" {
  description = "ALB DNS name"
  type        = string
  default     = ""
}

variable "health_check_path" {
  description = "Health check path"
  type        = string
  default     = "/"
}
