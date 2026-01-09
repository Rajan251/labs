# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = module.networking.vpc_cidr
}

# Network Outputs
output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_app_subnet_ids" {
  description = "IDs of private application subnets"
  value       = module.networking.private_app_subnet_ids
}

output "private_db_subnet_ids" {
  description = "IDs of private database subnets"
  value       = module.networking.private_db_subnet_ids
}

output "nat_gateway_ips" {
  description = "Public IPs of NAT Gateways"
  value       = module.networking.nat_gateway_ips
}

# VPN Outputs
output "vpn_server_ip" {
  description = "Public IP of VPN server"
  value       = module.vpn.vpn_public_ip
}

output "vpn_instance_id" {
  description = "Instance ID of VPN server"
  value       = module.vpn.vpn_instance_id
}

# Load Balancer Outputs
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.loadbalancer.alb_dns_name
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = module.loadbalancer.alb_arn
}

# Auto Scaling Outputs
output "app_asg_name" {
  description = "Name of application Auto Scaling Group"
  value       = module.compute.app_asg_name
}

output "db_asg_name" {
  description = "Name of database Auto Scaling Group"
  value       = module.compute.db_asg_name
}

# CloudFront Outputs
output "cloudfront_domain_name" {
  description = "Domain name of CloudFront distribution"
  value       = module.cdn.cloudfront_domain_name
}

output "cloudfront_distribution_id" {
  description = "ID of CloudFront distribution"
  value       = module.cdn.cloudfront_distribution_id
}

# S3 Outputs
output "s3_bucket_name" {
  description = "Name of S3 bucket for static content"
  value       = module.cdn.s3_bucket_name
}

# Monitoring Outputs
output "sns_topic_arn" {
  description = "ARN of SNS topic for alerts"
  value       = module.monitoring.sns_topic_arn
}

output "cloudtrail_bucket_name" {
  description = "Name of CloudTrail S3 bucket"
  value       = module.monitoring.cloudtrail_bucket_name
}

output "guardduty_detector_id" {
  description = "ID of GuardDuty detector"
  value       = module.monitoring.guardduty_detector_id
}

# Quick Access URLs
output "application_url" {
  description = "Application URL (via ALB)"
  value       = "http://${module.loadbalancer.alb_dns_name}"
}

output "cloudfront_url" {
  description = "CloudFront URL"
  value       = "https://${module.cdn.cloudfront_domain_name}"
}
