output "alb_security_group_id" {
  description = "ID of ALB security group"
  value       = aws_security_group.alb.id
}

output "webapp_security_group_id" {
  description = "ID of web/app security group"
  value       = aws_security_group.webapp.id
}

output "db_security_group_id" {
  description = "ID of database security group"
  value       = aws_security_group.database.id
}
