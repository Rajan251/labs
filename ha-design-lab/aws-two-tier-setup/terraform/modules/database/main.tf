# Database Module - MongoDB Instances

# Get latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# MongoDB User Data Template
data "template_file" "mongodb_userdata" {
  template = file("${path.module}/userdata/mongodb-setup.sh")

  vars = {
    admin_password = var.mongodb_admin_password
    app_password   = var.mongodb_app_password
  }
}

# MongoDB Primary Instance
resource "aws_instance" "mongodb_primary" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type
  key_name      = var.key_name
  subnet_id     = var.private_subnet_ids[0]

  vpc_security_group_ids = [var.db_security_group_id]

  root_block_device {
    volume_size           = 100
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  user_data = data.template_file.mongodb_userdata.rendered

  tags = {
    Name = "${var.environment}-mongodb-primary"
    Role = "database"
    Type = "primary"
  }
}

# MongoDB Secondary Instance
resource "aws_instance" "mongodb_secondary" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type
  key_name      = var.key_name
  subnet_id     = var.private_subnet_ids[1]

  vpc_security_group_ids = [var.db_security_group_id]

  root_block_device {
    volume_size           = 100
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  user_data = data.template_file.mongodb_userdata.rendered

  tags = {
    Name = "${var.environment}-mongodb-secondary"
    Role = "database"
    Type = "secondary"
  }
}
