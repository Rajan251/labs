#!/bin/bash

# Update system
yum update -y

# Install MongoDB 6.0
cat > /etc/yum.repos.d/mongodb-org-6.0.repo <<'REPO'
[mongodb-org-6.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2/mongodb-org/6.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
REPO

yum install -y mongodb-org

# Create data directory
mkdir -p /data/db
chown -R mongod:mongod /data/db

# Configure MongoDB
cat > /etc/mongod.conf <<'MONGOD'
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

storage:
  dbPath: /data/db
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 2

processManagement:
  fork: true
  pidFilePath: /var/run/mongodb/mongod.pid

net:
  port: 27017
  bindIp: 0.0.0.0

security:
  authorization: enabled

replication:
  replSetName: rs0
MONGOD

# Start MongoDB
systemctl start mongod
systemctl enable mongod

# Wait for MongoDB to start
sleep 10

# Note: Replica set initialization must be done manually after deployment
# See documentation for replica set setup instructions

echo "MongoDB installation complete"
