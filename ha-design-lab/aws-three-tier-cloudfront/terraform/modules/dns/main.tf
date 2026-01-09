# DNS Module - Route 53

terraform {
  required_version = ">= 1.0"
}

# Route 53 Hosted Zone
resource "aws_route53_zone" "main" {
  count = var.create_hosted_zone ? 1 : 0

  name = var.domain_name

  tags = {
    Name        = "${var.project_name}-${var.environment}-zone"
    Environment = var.environment
    Project     = var.project_name
  }
}

# A Record for CloudFront (Alias)
resource "aws_route53_record" "cloudfront" {
  count = var.create_hosted_zone && var.create_cloudfront_record ? 1 : 0

  zone_id = aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

# CNAME Record for www
resource "aws_route53_record" "www" {
  count = var.create_hosted_zone && var.create_cloudfront_record ? 1 : 0

  zone_id = aws_route53_zone.main[0].zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

# Health Check for ALB
resource "aws_route53_health_check" "alb" {
  count = var.create_hosted_zone && var.create_health_check ? 1 : 0

  fqdn              = var.alb_dns_name
  port              = 80
  type              = "HTTP"
  resource_path     = var.health_check_path
  failure_threshold = "3"
  request_interval  = "30"

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb-health"
    Environment = var.environment
    Project     = var.project_name
  }
}
