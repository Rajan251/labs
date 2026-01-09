output "hosted_zone_id" {
  description = "ID of the Route 53 hosted zone"
  value       = var.create_hosted_zone ? aws_route53_zone.main[0].zone_id : ""
}

output "hosted_zone_name_servers" {
  description = "Name servers for the hosted zone"
  value       = var.create_hosted_zone ? aws_route53_zone.main[0].name_servers : []
}

output "health_check_id" {
  description = "ID of the health check"
  value       = var.create_health_check ? aws_route53_health_check.alb[0].id : ""
}
