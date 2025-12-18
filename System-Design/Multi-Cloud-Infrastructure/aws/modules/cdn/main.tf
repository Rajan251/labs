resource "aws_cloudfront_distribution" "s3_distribution" {
  origin {
    domain_name = var.s3_bucket_domain_name
    origin_id   = "S3-${var.s3_bucket_name}"

    # S3 specific configuration...
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CDN for ${var.environment}"
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${var.s3_bucket_name}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  price_class = "PriceClass_100" # Use PriceClass_All for global

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    # acm_certificate_arn = var.acm_certificate_arn
    # ssl_support_method = "sni-only"
  }

  tags = {
    Environment = var.environment
  }
}

variable "environment" { type = string }
variable "s3_bucket_domain_name" { type = string }
variable "s3_bucket_name" { type = string }
