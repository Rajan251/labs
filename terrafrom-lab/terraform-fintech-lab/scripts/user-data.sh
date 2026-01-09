#!/bin/bash
# User data script for PayFlow application instances

set -e

# Update system
yum update -y

# Install Docker
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Create application directory
mkdir -p /opt/payflow

# Set environment variables
cat > /etc/environment <<EOF
DB_ENDPOINT=${db_endpoint}
APP_VERSION=${app_version}
ENVIRONMENT=${environment}
AWS_REGION=${aws_region}
EOF

# Create systemd service for application
cat > /etc/systemd/system/payflow.service <<EOF
[Unit]
Description=PayFlow Application
After=docker.service
Requires=docker.service

[Service]
Type=simple
EnvironmentFile=/etc/environment
ExecStart=/usr/bin/docker run --name payflow -p 8080:8080 payflow:latest
ExecStop=/usr/bin/docker stop payflow
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable payflow.service

# Install monitoring tools
yum install -y htop iotop

# Configure CloudWatch Logs
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<EOF
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/messages",
            "log_group_name": "/aws/ec2/${environment}/system",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
EOF

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

echo "User data script completed successfully"
