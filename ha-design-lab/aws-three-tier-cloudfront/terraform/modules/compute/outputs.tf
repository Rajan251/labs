output "app_asg_id" {
  description = "ID of application Auto Scaling Group"
  value       = aws_autoscaling_group.app.id
}

output "app_asg_name" {
  description = "Name of application Auto Scaling Group"
  value       = aws_autoscaling_group.app.name
}

output "app_launch_template_id" {
  description = "ID of application launch template"
  value       = aws_launch_template.app.id
}

output "app_scale_up_policy_arn" {
  description = "ARN of application scale up policy"
  value       = aws_autoscaling_policy.app_scale_up.arn
}

output "app_scale_down_policy_arn" {
  description = "ARN of application scale down policy"
  value       = aws_autoscaling_policy.app_scale_down.arn
}

output "db_asg_id" {
  description = "ID of database Auto Scaling Group"
  value       = aws_autoscaling_group.db.id
}

output "db_asg_name" {
  description = "Name of database Auto Scaling Group"
  value       = aws_autoscaling_group.db.name
}

output "db_launch_template_id" {
  description = "ID of database launch template"
  value       = aws_launch_template.db.id
}

output "db_scale_up_policy_arn" {
  description = "ARN of database scale up policy"
  value       = aws_autoscaling_policy.db_scale_up.arn
}

output "db_scale_down_policy_arn" {
  description = "ARN of database scale down policy"
  value       = aws_autoscaling_policy.db_scale_down.arn
}
