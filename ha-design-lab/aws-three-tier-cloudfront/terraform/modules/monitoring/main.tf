# Monitoring Module - CloudWatch, SNS, CloudTrail, GuardDuty

terraform {
  required_version = ">= 1.0"
}

# ============================================================================
# SNS TOPIC FOR ALERTS
# ============================================================================

# SNS Topic
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"

  tags = {
    Name        = "${var.project_name}-${var.environment}-alerts"
    Environment = var.environment
    Project     = var.project_name
  }
}

# SNS Topic Subscription (Email)
resource "aws_sns_topic_subscription" "email" {
  count = var.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ============================================================================
# CLOUDWATCH ALARMS - APPLICATION TIER
# ============================================================================

# High CPU Alarm - Application
resource "aws_cloudwatch_metric_alarm" "app_high_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-app-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "70"
  alarm_description   = "This metric monitors application server CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn, var.app_scale_up_policy_arn]

  dimensions = {
    AutoScalingGroupName = var.app_asg_name
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-app-high-cpu"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Low CPU Alarm - Application
resource "aws_cloudwatch_metric_alarm" "app_low_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-app-low-cpu"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "30"
  alarm_description   = "This metric monitors application server CPU utilization"
  alarm_actions       = [var.app_scale_down_policy_arn]

  dimensions = {
    AutoScalingGroupName = var.app_asg_name
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-app-low-cpu"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ============================================================================
# CLOUDWATCH ALARMS - DATABASE TIER
# ============================================================================

# High CPU Alarm - Database
resource "aws_cloudwatch_metric_alarm" "db_high_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-db-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors database server CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn, var.db_scale_up_policy_arn]

  dimensions = {
    AutoScalingGroupName = var.db_asg_name
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-high-cpu"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Low CPU Alarm - Database
resource "aws_cloudwatch_metric_alarm" "db_low_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-db-low-cpu"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "5"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "600"
  statistic           = "Average"
  threshold           = "40"
  alarm_description   = "This metric monitors database server CPU utilization"
  alarm_actions       = [var.db_scale_down_policy_arn]

  dimensions = {
    AutoScalingGroupName = var.db_asg_name
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-low-cpu"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ============================================================================
# CLOUDWATCH ALARMS - LOAD BALANCER
# ============================================================================

# Unhealthy Host Count Alarm
resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_hosts" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-unhealthy-hosts"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Average"
  threshold           = "0"
  alarm_description   = "This metric monitors unhealthy target count"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.target_group_arn_suffix
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb-unhealthy-hosts"
    Environment = var.environment
    Project     = var.project_name
  }
}

# High Response Time Alarm
resource "aws_cloudwatch_metric_alarm" "alb_high_response_time" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "This metric monitors ALB response time"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb-high-response-time"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ============================================================================
# CLOUDTRAIL
# ============================================================================

# S3 Bucket for CloudTrail Logs
resource "aws_s3_bucket" "cloudtrail" {
  bucket = "${var.project_name}-${var.environment}-cloudtrail-logs"

  tags = {
    Name        = "${var.project_name}-${var.environment}-cloudtrail-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# S3 Bucket Policy for CloudTrail
resource "aws_s3_bucket_policy" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail.arn
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}

# CloudTrail
resource "aws_cloudtrail" "main" {
  name                          = "${var.project_name}-${var.environment}-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true

  event_selector {
    read_write_type           = "All"
    include_management_events = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-trail"
    Environment = var.environment
    Project     = var.project_name
  }

  depends_on = [aws_s3_bucket_policy.cloudtrail]
}

# ============================================================================
# GUARDDUTY
# ============================================================================

# GuardDuty Detector
resource "aws_guardduty_detector" "main" {
  enable = true

  finding_publishing_frequency = "FIFTEEN_MINUTES"

  tags = {
    Name        = "${var.project_name}-${var.environment}-guardduty"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Event Rule for GuardDuty Findings
resource "aws_cloudwatch_event_rule" "guardduty" {
  name        = "${var.project_name}-${var.environment}-guardduty-findings"
  description = "Capture GuardDuty findings"

  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Finding"]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-guardduty-findings"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Event Target (SNS)
resource "aws_cloudwatch_event_target" "guardduty_sns" {
  rule      = aws_cloudwatch_event_rule.guardduty.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.alerts.arn
}

# SNS Topic Policy for CloudWatch Events
resource "aws_sns_topic_policy" "guardduty" {
  arn = aws_sns_topic.alerts.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action   = "SNS:Publish"
        Resource = aws_sns_topic.alerts.arn
      }
    ]
  })
}
