# Outputs for Two-Tier Architecture

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = module.vpc.private_subnet_ids
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.loadbalancer.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the ALB (for Route53)"
  value       = module.loadbalancer.alb_zone_id
}

output "mongodb_primary_private_ip" {
  description = "Private IP of MongoDB primary"
  value       = module.database.mongodb_primary_private_ip
}

output "mongodb_secondary_private_ip" {
  description = "Private IP of MongoDB secondary"
  value       = module.database.mongodb_secondary_private_ip
}

output "mongodb_connection_string" {
  description = "MongoDB connection string for application"
  value       = "mongodb://appuser:PASSWORD@${module.database.mongodb_primary_private_ip}:27017,${module.database.mongodb_secondary_private_ip}:27017/myapp?replicaSet=rs0&readPreference=primaryPreferred"
  sensitive   = true
}

output "autoscaling_group_name" {
  description = "Name of the Auto Scaling Group"
  value       = module.autoscaling.autoscaling_group_name
}

output "autoscaling_group_arn" {
  description = "ARN of the Auto Scaling Group"
  value       = module.autoscaling.autoscaling_group_arn
}

output "launch_template_id" {
  description = "ID of the launch template"
  value       = module.autoscaling.launch_template_id
}

output "application_url" {
  description = "URL to access the application"
  value       = "http://${module.loadbalancer.alb_dns_name}"
}

output "health_check_url" {
  description = "Health check endpoint URL"
  value       = "http://${module.loadbalancer.alb_dns_name}/health"
}
