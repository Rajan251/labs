# Use Cases & Operational Scenarios

## Overview

This document provides real-world operational scenarios you'll encounter when managing the PayFlow Solutions infrastructure. Each scenario includes the problem, solution approach, Terraform implementation, and verification steps.

---

## Scenario 1: Handling Traffic Spikes

### Business Context
Black Friday sale causes 10x normal traffic. Application must scale automatically without manual intervention.

### Current State
- Normal load: 100 requests/second
- 3 EC2 instances (t3.small)
- CPU utilization: 30-40%

### Traffic Spike
- Peak load: 1,000 requests/second (10x)
- Expected CPU: 80-90% without scaling
- Required instances: 8-10

### Auto Scaling Configuration

```hcl
# modules/compute/main.tf

resource "aws_autoscaling_group" "app" {
  name                = "payflow-asg-app-${var.environment}"
  vpc_zone_identifier = var.private_subnet_ids
  target_group_arns   = [var.target_group_arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300
  
  min_size         = var.asg_min_size
  max_size         = var.asg_max_size
  desired_capacity = var.asg_desired_size
  
  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }
  
  tag {
    key                 = "Name"
    value               = "payflow-ec2-app-${var.environment}"
    propagate_at_launch = true
  }
}

# Target Tracking Policy - Primary scaling method
resource "aws_autoscaling_policy" "target_tracking" {
  name                   = "target-tracking-cpu"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"
  
  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# Step Scaling Policy - Aggressive scale-out for rapid spikes
resource "aws_autoscaling_policy" "scale_out" {
  name                   = "scale-out-cpu-high"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "StepScaling"
  adjustment_type        = "ChangeInCapacity"
  
  step_adjustment {
    scaling_adjustment          = 2
    metric_interval_lower_bound = 0
    metric_interval_upper_bound = 10
  }
  
  step_adjustment {
    scaling_adjustment          = 4
    metric_interval_lower_bound = 10
  }
}

# CloudWatch Alarm for Step Scaling
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "payflow-cpu-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Average"
  threshold           = "85"
  
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app.name
  }
  
  alarm_actions = [aws_autoscaling_policy.scale_out.arn]
}

# Scheduled Scaling - Proactive scaling before known traffic
resource "aws_autoscaling_schedule" "scale_up_morning" {
  scheduled_action_name  = "scale-up-morning"
  min_size               = 5
  max_size               = 10
  desired_capacity       = 5
  recurrence             = "0 8 * * MON-FRI"  # 8 AM weekdays
  autoscaling_group_name = aws_autoscaling_group.app.name
}

resource "aws_autoscaling_schedule" "scale_down_night" {
  scheduled_action_name  = "scale-down-night"
  min_size               = 2
  max_size               = 10
  desired_capacity       = 2
  recurrence             = "0 22 * * *"  # 10 PM daily
  autoscaling_group_name = aws_autoscaling_group.app.name
}
```

### Testing the Scenario

```bash
# 1. Generate load (using Apache Bench)
ab -n 100000 -c 100 https://payflow.example.com/api/v1/health

# 2. Monitor scaling activity
watch -n 5 'aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names payflow-asg-app-prod \
  --query "AutoScalingGroups[0].[DesiredCapacity,Instances[*].InstanceId]"'

# 3. Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=payflow-asg-app-prod \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### Expected Behavior

| Time | CPU % | Instances | Action |
|------|-------|-----------|--------|
| 0:00 | 35% | 3 | Normal operation |
| 0:05 | 75% | 3 | Target tracking triggered |
| 0:07 | 80% | 4 | Scaling out (1 instance) |
| 0:10 | 88% | 4 | Step scaling triggered |
| 0:12 | 85% | 6 | Scaling out (2 instances) |
| 0:15 | 65% | 6 | Stabilizing |
| 0:20 | 60% | 6 | Stable |

---

## Scenario 2: Instance Failure Recovery

### Business Context
EC2 instance crashes due to application bug. System must automatically detect and replace failed instance.

### Failure Detection

```hcl
# Health check configuration
resource "aws_autoscaling_group" "app" {
  health_check_type         = "ELB"  # Use ALB health checks
  health_check_grace_period = 300    # 5 minutes for instance to become healthy
  
  # Replace unhealthy instances automatically
  force_delete = true
  
  # Ensure minimum capacity during replacement
  wait_for_capacity_timeout = "10m"
}

# ALB Target Group health check
resource "aws_lb_target_group" "app" {
  health_check {
    enabled             = true
    interval            = 30
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }
  
  deregistration_delay = 30  # Drain connections before terminating
}
```

### Simulate Failure

```bash
# 1. Terminate instance manually
aws ec2 terminate-instances --instance-ids i-abc123

# 2. Or crash application (from inside instance)
aws ssm start-session --target i-abc123
sudo systemctl stop payflow-app

# 3. Monitor replacement
watch -n 5 'aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names payflow-asg-app-prod \
  --query "AutoScalingGroups[0].Instances[*].[InstanceId,LifecycleState,HealthStatus]" \
  --output table'
```

### Recovery Timeline

| Time | Event | Instance Count | Status |
|------|-------|----------------|--------|
| 0:00 | Instance crashes | 3 healthy | Normal |
| 0:30 | Health check fails (3 consecutive) | 2 healthy, 1 unhealthy | Detected |
| 1:00 | ASG marks instance unhealthy | 2 healthy, 1 terminating | Replacing |
| 1:30 | New instance launching | 2 healthy, 1 pending | Recovering |
| 2:00 | New instance in service | 3 healthy | Recovered |

**Total Recovery Time: ~2 minutes**

---

## Scenario 3: Rolling Updates (Zero Downtime)

### Business Context
Deploy new application version without downtime. Must maintain minimum capacity during deployment.

### Instance Refresh Configuration

```hcl
# Launch Template with versioning
resource "aws_launch_template" "app" {
  name_prefix   = "payflow-lt-app-${var.environment}-"
  image_id      = var.ami_id  # Update this for new version
  instance_type = var.instance_type
  
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    app_version = var.app_version  # v1.2.0 → v1.3.0
    environment = var.environment
  }))
  
  # Create new version on every change
  lifecycle {
    create_before_destroy = true
  }
}

# Auto Scaling Group with instance refresh
resource "aws_autoscaling_group" "app" {
  # ... other config ...
  
  instance_refresh {
    strategy = "Rolling"
    
    preferences {
      min_healthy_percentage = 90  # Keep 90% healthy during refresh
      instance_warmup        = 300 # Wait 5 min before moving to next
      
      checkpoint_percentages = [25, 50, 75]  # Pause points for verification
      checkpoint_delay       = 300           # Wait 5 min at each checkpoint
    }
  }
}
```

### Deployment Process

```bash
# 1. Update application version
cd environments/prod
terraform plan -var="app_version=v1.3.0"

# 2. Apply changes
terraform apply -var="app_version=v1.3.0"

# 3. Monitor instance refresh
aws autoscaling describe-instance-refreshes \
  --auto-scaling-group-name payflow-asg-app-prod \
  --output table

# 4. Watch instance replacement
watch -n 10 'aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names payflow-asg-app-prod \
  --query "AutoScalingGroups[0].Instances[*].[InstanceId,LaunchTemplate.Version]" \
  --output table'
```

### Rolling Update Timeline (6 instances)

| Time | Old Version | New Version | Status |
|------|-------------|-------------|--------|
| 0:00 | 6 | 0 | Starting |
| 0:05 | 5 | 1 | 1st instance replaced |
| 0:10 | 4 | 2 | 25% checkpoint |
| 0:15 | 3 | 3 | 50% checkpoint |
| 0:20 | 2 | 4 | 75% checkpoint |
| 0:25 | 1 | 5 | Almost complete |
| 0:30 | 0 | 6 | Complete |

**Total Deployment Time: ~30 minutes (zero downtime)**

### Rollback Procedure

```bash
# If issues detected, cancel instance refresh
aws autoscaling cancel-instance-refresh \
  --auto-scaling-group-name payflow-asg-app-prod

# Revert to previous version
terraform apply -var="app_version=v1.2.0"

# Start new instance refresh
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name payflow-asg-app-prod
```

---

## Scenario 4: Database Failover

### Business Context
Primary RDS instance fails. System must automatically failover to standby with minimal downtime.

### Multi-AZ Configuration

```hcl
resource "aws_db_instance" "main" {
  identifier     = "payflow-rds-postgres-${var.environment}"
  engine         = "postgres"
  engine_version = "15.4"
  
  instance_class = var.db_instance_class
  
  # Multi-AZ for automatic failover
  multi_az = true
  
  # Automated backups
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # Enable enhanced monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval             = 60
  monitoring_role_arn            = aws_iam_role.rds_monitoring.arn
}

# CloudWatch Alarm for failover detection
resource "aws_cloudwatch_metric_alarm" "db_cpu" {
  alarm_name          = "payflow-rds-cpu-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

### Test Failover

```bash
# 1. Initiate manual failover
aws rds reboot-db-instance \
  --db-instance-identifier payflow-rds-postgres-prod \
  --force-failover

# 2. Monitor failover progress
watch -n 5 'aws rds describe-db-instances \
  --db-instance-identifier payflow-rds-postgres-prod \
  --query "DBInstances[0].[DBInstanceStatus,AvailabilityZone,SecondaryAvailabilityZone]" \
  --output table'

# 3. Check application connectivity
# Application should automatically reconnect
curl https://payflow.example.com/api/v1/health
```

### Failover Timeline

| Time | Event | Status | Availability |
|------|-------|--------|--------------|
| 0:00 | Failover initiated | Primary: us-east-1a | Available |
| 0:15 | Failover in progress | Switching | Brief interruption |
| 0:30 | Failover complete | Primary: us-east-1b | Available |
| 1:00 | New standby created | Standby: us-east-1a | Fully redundant |

**RTO: 60-120 seconds**  
**RPO: 0 (synchronous replication)**

---

## Scenario 5: Cost Optimization

### Business Context
Infrastructure costs exceeding budget. Need to reduce costs without impacting performance or availability.

### Cost Analysis

```bash
# Identify cost drivers
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE \
  --filter file://filter.json

# filter.json
{
  "Tags": {
    "Key": "Project",
    "Values": ["payflow-platform"]
  }
}
```

### Optimization Strategies

#### 1. Right-Size Instances

```hcl
# Use different instance types per environment
variable "instance_type" {
  type = map(string)
  default = {
    dev     = "t3.micro"   # $0.0104/hour = $7.50/month
    staging = "t3.small"   # $0.0208/hour = $15/month
    prod    = "t3.medium"  # $0.0416/hour = $30/month
  }
}

# Use Reserved Instances for prod (30% savings)
# Purchase via AWS Console or:
aws ec2 purchase-reserved-instances-offering \
  --reserved-instances-offering-id xxx \
  --instance-count 3
```

#### 2. Optimize NAT Gateway Costs

```hcl
# Dev: Single NAT Gateway (save $64/month)
locals {
  nat_gateway_count = var.environment == "prod" ? 3 : 1
}

resource "aws_nat_gateway" "main" {
  count = local.nat_gateway_count
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
}

# Or use NAT Instance for dev (save $30/month)
resource "aws_instance" "nat" {
  count         = var.environment == "dev" ? 1 : 0
  ami           = data.aws_ami.nat.id
  instance_type = "t3.micro"
  
  source_dest_check = false
}
```

#### 3. S3 Lifecycle Policies

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id
  
  rule {
    id     = "archive-old-logs"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"  # Save 50%
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"  # Save 85%
    }
    
    expiration {
      days = 365  # Delete after 1 year
    }
  }
}
```

#### 4. Auto Scaling Schedule

```hcl
# Scale down during off-hours (save ~40% on compute)
resource "aws_autoscaling_schedule" "scale_down_night" {
  scheduled_action_name  = "scale-down-night"
  min_size               = 1
  max_size               = 5
  desired_capacity       = 1
  recurrence             = "0 22 * * *"  # 10 PM
  autoscaling_group_name = aws_autoscaling_group.app.name
}

resource "aws_autoscaling_schedule" "scale_up_morning" {
  scheduled_action_name  = "scale-up-morning"
  min_size               = 2
  max_size               = 10
  desired_capacity       = 3
  recurrence             = "0 6 * * *"  # 6 AM
  autoscaling_group_name = aws_autoscaling_group.app.name
}
```

### Cost Savings Summary

| Optimization | Monthly Savings | Annual Savings |
|--------------|-----------------|----------------|
| Dev: Single NAT GW | $64 | $768 |
| Reserved Instances (prod) | $27 | $324 |
| S3 Lifecycle Policies | $15 | $180 |
| Off-hours scaling | $120 | $1,440 |
| Right-sized instances | $45 | $540 |
| **Total** | **$271** | **$3,252** |

---

## Scenario 6: Security Incident Response

### Business Context
Suspicious activity detected. Need to investigate and contain potential breach.

### Detection

```bash
# 1. Check CloudTrail for unauthorized API calls
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=RunInstances \
  --max-results 50 \
  --output table

# 2. Review VPC Flow Logs for unusual traffic
aws logs filter-log-events \
  --log-group-name /aws/vpc/payflow-prod \
  --filter-pattern "[version, account, eni, source, destination, srcport, destport=22, protocol=6, packets, bytes, windowstart, windowend, action=ACCEPT, flowlogstatus]" \
  --start-time $(date -u -d '1 hour ago' +%s)000

# 3. Check for security group changes
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AuthorizeSecurityGroupIngress \
  --max-results 20
```

### Containment

```hcl
# Immediately revoke suspicious security group rule
resource "aws_security_group_rule" "emergency_revoke" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]  # Remove this
  security_group_id = aws_security_group.app.id
  
  # Comment out or delete this rule
  # lifecycle {
  #   prevent_destroy = true
  # }
}

# Apply immediately
# terraform apply -target=aws_security_group_rule.emergency_revoke
```

### Investigation

```bash
# 1. Isolate compromised instance
aws ec2 modify-instance-attribute \
  --instance-id i-compromised \
  --groups sg-isolated

# 2. Create forensic snapshot
aws ec2 create-snapshot \
  --volume-id vol-abc123 \
  --description "Forensic snapshot - incident 2024-01-08"

# 3. Review instance logs
aws ssm start-session --target i-compromised
sudo journalctl -u payflow-app --since "1 hour ago"
```

---

## Scenario 7: Disaster Recovery Drill

### Business Context
Quarterly DR drill to ensure RTO/RPO targets are met.

### DR Configuration

```hcl
# Automated snapshots
resource "aws_db_instance" "main" {
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  copy_tags_to_snapshot  = true
  
  # Enable automated backups to different region
  # (requires separate configuration)
}

# Cross-region replication for S3
resource "aws_s3_bucket_replication_configuration" "replication" {
  bucket = aws_s3_bucket.main.id
  role   = aws_iam_role.replication.arn
  
  rule {
    id     = "replicate-all"
    status = "Enabled"
    
    destination {
      bucket        = "arn:aws:s3:::payflow-backup-us-west-2"
      storage_class = "STANDARD_IA"
    }
  }
}
```

### DR Drill Steps

```bash
# 1. Simulate region failure (use different region)
export AWS_DEFAULT_REGION=us-west-2

# 2. Restore RDS from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier payflow-rds-dr \
  --db-snapshot-identifier payflow-rds-prod-2024-01-08

# 3. Deploy infrastructure in DR region
cd environments/prod
terraform apply -var="region=us-west-2" -var="dr_mode=true"

# 4. Update Route53 to point to DR region
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456 \
  --change-batch file://failover.json

# 5. Verify application functionality
curl https://payflow.example.com/api/v1/health

# 6. Measure RTO/RPO
# RTO: Time from failure detection to service restoration
# RPO: Data loss (should be < 15 minutes)
```

---

## Summary

These scenarios demonstrate real-world operational challenges and solutions. Practice each scenario in your lab environment to build confidence and muscle memory.

### Key Takeaways

✅ **Auto-scaling** handles traffic spikes automatically  
✅ **Health checks** detect and replace failed instances  
✅ **Instance refresh** enables zero-downtime deployments  
✅ **Multi-AZ RDS** provides automatic failover  
✅ **Cost optimization** reduces spend without sacrificing reliability  
✅ **Security monitoring** detects and contains incidents  
✅ **DR drills** ensure preparedness for disasters  

### Next Steps

- Practice these scenarios in [Lab Exercises](../labs/)
- Review [Architecture Documentation](architecture.md)
- Study [Security Best Practices](security-best-practices.md)
