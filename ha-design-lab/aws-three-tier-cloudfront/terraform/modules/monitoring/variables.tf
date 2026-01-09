variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = ""
}

variable "app_asg_name" {
  description = "Name of application Auto Scaling Group"
  type        = string
}

variable "db_asg_name" {
  description = "Name of database Auto Scaling Group"
  type        = string
}

variable "app_scale_up_policy_arn" {
  description = "ARN of application scale up policy"
  type        = string
}

variable "app_scale_down_policy_arn" {
  description = "ARN of application scale down policy"
  type        = string
}

variable "db_scale_up_policy_arn" {
  description = "ARN of database scale up policy"
  type        = string
}

variable "db_scale_down_policy_arn" {
  description = "ARN of database scale down policy"
  type        = string
}

variable "alb_arn_suffix" {
  description = "ARN suffix of the ALB"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "ARN suffix of the target group"
  type        = string
}
