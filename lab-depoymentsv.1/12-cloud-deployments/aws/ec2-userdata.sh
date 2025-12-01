#!/bin/bash
# 12-cloud-deployments/aws/ec2-userdata.sh
# AWS EC2 User Data script to bootstrap an application

# Update system
yum update -y

# Install dependencies
yum install -y docker git
service docker start
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone repo
cd /home/ec2-user
git clone https://github.com/example/myapp.git
cd myapp

# Start application
docker-compose up -d
