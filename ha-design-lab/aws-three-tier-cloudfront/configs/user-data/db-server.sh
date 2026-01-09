#!/bin/bash
# Database Server User Data Script
# This script installs and configures MongoDB

set -e

# Update system
yum update -y

# Install CloudWatch Agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Add MongoDB repository
cat > /etc/yum.repos.d/mongodb-org-6.0.repo <<'EOF'
[mongodb-org-6.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2/mongodb-org/6.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
EOF

# Install MongoDB
yum install -y mongodb-org

# Create data directory
mkdir -p /data/db
chown -R mongod:mongod /data/db

# Configure MongoDB for replica set
cat > /etc/mongod.conf <<'EOF'
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

storage:
  dbPath: /data/db
  journal:
    enabled: true

processManagement:
  fork: true
  pidFilePath: /var/run/mongodb/mongod.pid

net:
  port: 27017
  bindIp: 0.0.0.0

replication:
  replSetName: "rs0"

security:
  authorization: enabled
EOF

# Enable and start MongoDB
systemctl enable mongod
systemctl start mongod

# Wait for MongoDB to start
sleep 10

# Initialize replica set (only on first node)
# Note: This should be done manually after all nodes are up
# mongo --eval 'rs.initiate()'

echo "Database server setup complete!"
echo "To initialize replica set, run: mongosh --eval 'rs.initiate()'"
