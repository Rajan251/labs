# Security Module - Security Groups and NACLs

terraform {
  required_version = ">= 1.0"
}

# ============================================================================
# SECURITY GROUPS
# ============================================================================

# VPN Server Security Group
resource "aws_security_group" "vpn" {
  name_description = "${var.project_name}-${var.environment}-vpn-sg"
  description      = "Security group for VPN server"
  vpc_id           = var.vpc_id

  # SSH access from allowed IPs
  ingress {
    description = "SSH from allowed IPs"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.vpn_allowed_ips
  }

  # OpenVPN access
  ingress {
    description = "OpenVPN"
    from_port   = 1194
    to_port     = 1194
    protocol    = "udp"
    cidr_blocks = var.vpn_allowed_ips
  }

  # HTTPS for OpenVPN (alternative)
  ingress {
    description = "OpenVPN HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.vpn_allowed_ips
  }

  # Outbound - all traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpn-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = var.vpc_id

  # HTTP from internet
  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS from internet
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound - to application servers
  egress {
    description     = "To application servers"
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Application Server Security Group
resource "aws_security_group" "app" {
  name        = "${var.project_name}-${var.environment}-app-sg"
  description = "Security group for application servers"
  vpc_id      = var.vpc_id

  # Application port from ALB
  ingress {
    description     = "Application port from ALB"
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # SSH from VPN
  ingress {
    description     = "SSH from VPN"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.vpn.id]
  }

  # Outbound - to database
  egress {
    description     = "To database servers"
    from_port       = var.db_port
    to_port         = var.db_port
    protocol        = "tcp"
    security_groups = [aws_security_group.db.id]
  }

  # Outbound - to internet (for updates, etc.)
  egress {
    description = "To internet"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-app-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Database Server Security Group
resource "aws_security_group" "db" {
  name        = "${var.project_name}-${var.environment}-db-sg"
  description = "Security group for database servers"
  vpc_id      = var.vpc_id

  # Database port from application servers
  ingress {
    description     = "Database port from app servers"
    from_port       = var.db_port
    to_port         = var.db_port
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  # SSH from VPN
  ingress {
    description     = "SSH from VPN"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.vpn.id]
  }

  # Replication port (for MongoDB replica set, etc.)
  ingress {
    description = "Replication between DB servers"
    from_port   = var.db_port
    to_port     = var.db_port
    protocol    = "tcp"
    self        = true
  }

  # Outbound - to internet (for updates, etc.)
  egress {
    description = "To internet"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound - replication
  egress {
    description = "Replication between DB servers"
    from_port   = var.db_port
    to_port     = var.db_port
    protocol    = "tcp"
    self        = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ============================================================================
# NETWORK ACLs
# ============================================================================

# Public Subnet NACL
resource "aws_network_acl" "public" {
  vpc_id     = var.vpc_id
  subnet_ids = var.public_subnet_ids

  # Inbound Rules
  # HTTP
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }

  # HTTPS
  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }

  # SSH from allowed IPs
  ingress {
    protocol   = "tcp"
    rule_no    = 120
    action     = "allow"
    cidr_block = var.vpn_allowed_ips[0] # First allowed IP range
    from_port  = 22
    to_port    = 22
  }

  # OpenVPN
  ingress {
    protocol   = "udp"
    rule_no    = 130
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1194
    to_port    = 1194
  }

  # Ephemeral ports (return traffic)
  ingress {
    protocol   = "tcp"
    rule_no    = 140
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  # Outbound Rules
  # All traffic
  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-public-nacl"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Private Application Subnet NACL
resource "aws_network_acl" "private_app" {
  vpc_id     = var.vpc_id
  subnet_ids = var.private_app_subnet_ids

  # Inbound Rules
  # Application port from VPC
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = var.app_port
    to_port    = var.app_port
  }

  # SSH from VPC
  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 22
    to_port    = 22
  }

  # Ephemeral ports
  ingress {
    protocol   = "tcp"
    rule_no    = 120
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  # Outbound Rules
  # All traffic
  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-private-app-nacl"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Private Database Subnet NACL
resource "aws_network_acl" "private_db" {
  vpc_id     = var.vpc_id
  subnet_ids = var.private_db_subnet_ids

  # Inbound Rules
  # Database port from VPC
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = var.db_port
    to_port    = var.db_port
  }

  # SSH from VPC
  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 22
    to_port    = 22
  }

  # Ephemeral ports
  ingress {
    protocol   = "tcp"
    rule_no    = 120
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  # Outbound Rules
  # All traffic
  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-private-db-nacl"
    Environment = var.environment
    Project     = var.project_name
  }
}
