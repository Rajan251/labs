# Compute Module - EC2 Instances and Auto Scaling Groups

terraform {
  required_version = ">= 1.0"
}

# ============================================================================
# IAM ROLES FOR EC2 INSTANCES
# ============================================================================

# IAM Role for Application Servers
resource "aws_iam_role" "app" {
  name = "${var.project_name}-${var.environment}-app-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-app-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach CloudWatch Agent Policy
resource "aws_iam_role_policy_attachment" "app_cloudwatch" {
  role       = aws_iam_role.app.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# Attach SSM Policy for Systems Manager
resource "aws_iam_role_policy_attachment" "app_ssm" {
  role       = aws_iam_role.app.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Instance Profile for Application Servers
resource "aws_iam_instance_profile" "app" {
  name = "${var.project_name}-${var.environment}-app-profile"
  role = aws_iam_role.app.name

  tags = {
    Name        = "${var.project_name}-${var.environment}-app-profile"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Role for Database Servers
resource "aws_iam_role" "db" {
  name = "${var.project_name}-${var.environment}-db-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach CloudWatch Agent Policy
resource "aws_iam_role_policy_attachment" "db_cloudwatch" {
  role       = aws_iam_role.db.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# Attach SSM Policy
resource "aws_iam_role_policy_attachment" "db_ssm" {
  role       = aws_iam_role.db.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Instance Profile for Database Servers
resource "aws_iam_instance_profile" "db" {
  name = "${var.project_name}-${var.environment}-db-profile"
  role = aws_iam_role.db.name

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-profile"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ============================================================================
# LAUNCH TEMPLATES
# ============================================================================

# Launch Template for Application Servers
resource "aws_launch_template" "app" {
  name_prefix   = "${var.project_name}-${var.environment}-app-"
  image_id      = var.app_ami_id
  instance_type = var.app_instance_type
  key_name      = var.key_name

  iam_instance_profile {
    name = aws_iam_instance_profile.app.name
  }

  vpc_security_group_ids = [var.app_security_group_id]

  user_data = base64encode(var.app_user_data)

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size           = var.app_volume_size
      volume_type           = "gp3"
      delete_on_termination = true
      encrypted             = true
    }
  }

  monitoring {
    enabled = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name        = "${var.project_name}-${var.environment}-app"
      Environment = var.environment
      Project     = var.project_name
      Tier        = "application"
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-app-lt"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Launch Template for Database Servers
resource "aws_launch_template" "db" {
  name_prefix   = "${var.project_name}-${var.environment}-db-"
  image_id      = var.db_ami_id
  instance_type = var.db_instance_type
  key_name      = var.key_name

  iam_instance_profile {
    name = aws_iam_instance_profile.db.name
  }

  vpc_security_group_ids = [var.db_security_group_id]

  user_data = base64encode(var.db_user_data)

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size           = var.db_volume_size
      volume_type           = "gp3"
      iops                  = 3000
      delete_on_termination = true
      encrypted             = true
    }
  }

  monitoring {
    enabled = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name        = "${var.project_name}-${var.environment}-db"
      Environment = var.environment
      Project     = var.project_name
      Tier        = "database"
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-lt"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ============================================================================
# AUTO SCALING GROUPS
# ============================================================================

# Auto Scaling Group for Application Servers
resource "aws_autoscaling_group" "app" {
  name                = "${var.project_name}-${var.environment}-app-asg"
  vpc_zone_identifier = var.private_app_subnet_ids
  target_group_arns   = [var.target_group_arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300

  min_size         = var.app_min_size
  max_size         = var.app_max_size
  desired_capacity = var.app_desired_capacity

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  enabled_metrics = [
    "GroupMinSize",
    "GroupMaxSize",
    "GroupDesiredCapacity",
    "GroupInServiceInstances",
    "GroupTotalInstances"
  ]

  tag {
    key                 = "Name"
    value               = "${var.project_name}-${var.environment}-app"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "Project"
    value               = var.project_name
    propagate_at_launch = true
  }
}

# Auto Scaling Group for Database Servers
resource "aws_autoscaling_group" "db" {
  name                = "${var.project_name}-${var.environment}-db-asg"
  vpc_zone_identifier = var.private_db_subnet_ids
  health_check_type   = "EC2"
  health_check_grace_period = 300

  min_size         = var.db_min_size
  max_size         = var.db_max_size
  desired_capacity = var.db_desired_capacity

  launch_template {
    id      = aws_launch_template.db.id
    version = "$Latest"
  }

  enabled_metrics = [
    "GroupMinSize",
    "GroupMaxSize",
    "GroupDesiredCapacity",
    "GroupInServiceInstances",
    "GroupTotalInstances"
  ]

  tag {
    key                 = "Name"
    value               = "${var.project_name}-${var.environment}-db"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "Project"
    value               = var.project_name
    propagate_at_launch = true
  }
}

# ============================================================================
# AUTO SCALING POLICIES
# ============================================================================

# Application Server - Scale Up Policy
resource "aws_autoscaling_policy" "app_scale_up" {
  name                   = "${var.project_name}-${var.environment}-app-scale-up"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.app.name
}

# Application Server - Scale Down Policy
resource "aws_autoscaling_policy" "app_scale_down" {
  name                   = "${var.project_name}-${var.environment}-app-scale-down"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.app.name
}

# Database Server - Scale Up Policy
resource "aws_autoscaling_policy" "db_scale_up" {
  name                   = "${var.project_name}-${var.environment}-db-scale-up"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 600
  autoscaling_group_name = aws_autoscaling_group.db.name
}

# Database Server - Scale Down Policy
resource "aws_autoscaling_policy" "db_scale_down" {
  name                   = "${var.project_name}-${var.environment}-db-scale-down"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 600
  autoscaling_group_name = aws_autoscaling_group.db.name
}
