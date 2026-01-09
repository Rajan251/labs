# VPN Module - VPN Server

terraform {
  required_version = ">= 1.0"
}

# IAM Role for VPN Server
resource "aws_iam_role" "vpn" {
  name = "${var.project_name}-${var.environment}-vpn-role"

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
    Name        = "${var.project_name}-${var.environment}-vpn-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach CloudWatch Agent Policy
resource "aws_iam_role_policy_attachment" "vpn_cloudwatch" {
  role       = aws_iam_role.vpn.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# Attach SSM Policy
resource "aws_iam_role_policy_attachment" "vpn_ssm" {
  role       = aws_iam_role.vpn.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Instance Profile for VPN Server
resource "aws_iam_instance_profile" "vpn" {
  name = "${var.project_name}-${var.environment}-vpn-profile"
  role = aws_iam_role.vpn.name

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpn-profile"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Elastic IP for VPN Server
resource "aws_eip" "vpn" {
  domain = "vpc"

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpn-eip"
    Environment = var.environment
    Project     = var.project_name
  }
}

# VPN Server Instance
resource "aws_instance" "vpn" {
  ami           = var.vpn_ami_id
  instance_type = var.vpn_instance_type
  key_name      = var.key_name
  subnet_id     = var.public_subnet_ids[0]

  vpc_security_group_ids = [var.vpn_security_group_id]
  iam_instance_profile   = aws_iam_instance_profile.vpn.name

  user_data = var.vpn_user_data

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }

  monitoring = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpn"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Associate Elastic IP with VPN Server
resource "aws_eip_association" "vpn" {
  instance_id   = aws_instance.vpn.id
  allocation_id = aws_eip.vpn.id
}
