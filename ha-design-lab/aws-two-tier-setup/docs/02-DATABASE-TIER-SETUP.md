# 🗄️ Step 2: Database Tier Setup - MongoDB Replica Set

> **Deploying MongoDB Replica Set in Private Subnets with High Availability**

---

## 📋 What We'll Create

- ✅ 2 MongoDB instances (1 Primary + 1 Secondary)
- ✅ MongoDB replica set configuration
- ✅ Automated backups
- ✅ Security hardening
- ✅ Monitoring setup

---

## 🎯 Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Private Subnets (No Internet Access)                   │
│                                                           │
│  ┌──────────────────────┐    ┌──────────────────────┐  │
│  │  AZ-1 (us-east-1a)   │    │  AZ-2 (us-east-1b)   │  │
│  │  10.0.11.0/24        │    │  10.0.12.0/24        │  │
│  │                       │    │                       │  │
│  │  ┌────────────────┐  │    │  ┌────────────────┐  │  │
│  │  │  MongoDB       │  │    │  │  MongoDB       │  │  │
│  │  │  PRIMARY       │◄─┼────┼─►│  SECONDARY     │  │  │
│  │  │                │  │    │  │                │  │  │
│  │  │  Port: 27017   │  │    │  │  Port: 27017   │  │  │
│  │  │  Instance Type:│  │    │  │  Instance Type:│  │  │
│  │  │  t3.large      │  │    │  │  t3.large      │  │  │
│  │  │  EBS: 100GB    │  │    │  │  EBS: 100GB    │  │  │
│  │  └────────────────┘  │    │  └────────────────┘  │  │
│  │                       │    │                       │  │
│  └──────────────────────┘    └──────────────────────┘  │
│                                                           │
│  Replica Set: rs0                                        │
│  Read Preference: primaryPreferred                       │
│  Write Concern: majority                                 │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## 🚀 Step-by-Step Setup

### 📍 **STEP 2.1: Launch MongoDB Instances**

First, load the infrastructure IDs:

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Load infrastructure IDs
source infrastructure-ids.txt

# Verify variables are loaded
echo "VPC_ID: $VPC_ID"
echo "DB_SG: $DB_SG"
echo "PRIVATE_DB_SUBNET_1: $PRIVATE_DB_SUBNET_1"
echo "PRIVATE_DB_SUBNET_2: $PRIVATE_DB_SUBNET_2"
```

Create a key pair for SSH access:

```bash
# Create key pair
aws ec2 create-key-pair \
  --key-name mongodb-key \
  --query 'KeyMaterial' \
  --output text > mongodb-key.pem

chmod 400 mongodb-key.pem

echo "✅ Key pair created: mongodb-key.pem"
```

Launch MongoDB instances:

```bash
# ============================================
# Get Amazon Linux 2 AMI ID
# ============================================

AMI_ID=$(aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text)

echo "✅ Using AMI: $AMI_ID"

# ============================================
# Launch MongoDB Primary (AZ-1)
# ============================================

MONGO_PRIMARY=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.large \
  --key-name mongodb-key \
  --security-group-ids $DB_SG \
  --subnet-id $PRIVATE_DB_SUBNET_1 \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":100,"VolumeType":"gp3","Encrypted":true}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=mongodb-primary},{Key=Role,Value=database},{Key=Tier,Value=database}]' \
  --user-data file://mongodb-userdata.sh \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "✅ MongoDB Primary launched: $MONGO_PRIMARY"

# ============================================
# Launch MongoDB Secondary (AZ-2)
# ============================================

MONGO_SECONDARY=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.large \
  --key-name mongodb-key \
  --security-group-ids $DB_SG \
  --subnet-id $PRIVATE_DB_SUBNET_2 \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":100,"VolumeType":"gp3","Encrypted":true}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=mongodb-secondary},{Key=Role,Value=database},{Key=Tier,Value=database}]' \
  --user-data file://mongodb-userdata.sh \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "✅ MongoDB Secondary launched: $MONGO_SECONDARY"

# Wait for instances to be running
echo "⏳ Waiting for instances to be running..."
aws ec2 wait instance-running --instance-ids $MONGO_PRIMARY $MONGO_SECONDARY
echo "✅ Instances are running"
```

---

### 📍 **STEP 2.2: Create User Data Script**

Create `mongodb-userdata.sh`:

```bash
cat > mongodb-userdata.sh <<'EOF'
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
  timeZoneInfo: /usr/share/zoneinfo

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

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json <<'CW'
{
  "metrics": {
    "namespace": "MongoDB",
    "metrics_collected": {
      "mem": {
        "measurement": [
          {"name": "mem_used_percent", "rename": "MemoryUtilization", "unit": "Percent"}
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          {"name": "used_percent", "rename": "DiskUtilization", "unit": "Percent"}
        ],
        "metrics_collection_interval": 60,
        "resources": ["*"]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/mongodb/mongod.log",
            "log_group_name": "/aws/mongodb/mongod",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
CW

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json

echo "✅ MongoDB installation complete"
EOF

chmod +x mongodb-userdata.sh
```

---

### 📍 **STEP 2.3: Get Private IPs**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Get private IPs
MONGO_PRIMARY_IP=$(aws ec2 describe-instances \
  --instance-ids $MONGO_PRIMARY \
  --query 'Reservations[0].Instances[0].PrivateIpAddress' \
  --output text)

MONGO_SECONDARY_IP=$(aws ec2 describe-instances \
  --instance-ids $MONGO_SECONDARY \
  --query 'Reservations[0].Instances[0].PrivateIpAddress' \
  --output text)

echo "MongoDB Primary IP: $MONGO_PRIMARY_IP"
echo "MongoDB Secondary IP: $MONGO_SECONDARY_IP"

# Save to file
cat >> infrastructure-ids.txt <<EOF
MONGO_PRIMARY=$MONGO_PRIMARY
MONGO_SECONDARY=$MONGO_SECONDARY
MONGO_PRIMARY_IP=$MONGO_PRIMARY_IP
MONGO_SECONDARY_IP=$MONGO_SECONDARY_IP
EOF
```

---

### 📍 **STEP 2.4: Configure Replica Set**

Since MongoDB instances are in private subnets, you'll need a bastion host or use AWS Systems Manager Session Manager. Here's using a bastion:

```bash
# ============================================
# Create a bastion host in public subnet
# ============================================

BASTION=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.micro \
  --key-name mongodb-key \
  --security-group-ids $WEBAPP_SG \
  --subnet-id $PUBLIC_SUBNET_1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=bastion-host}]' \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "✅ Bastion host created: $BASTION"

# Wait for bastion to be running
aws ec2 wait instance-running --instance-ids $BASTION

# Get bastion public IP
BASTION_IP=$(aws ec2 describe-instances \
  --instance-ids $BASTION \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "✅ Bastion IP: $BASTION_IP"
```

Connect to MongoDB primary via bastion:

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# SSH to bastion
ssh -i mongodb-key.pem ec2-user@$BASTION_IP

# From bastion, connect to MongoDB primary
ssh -i mongodb-key.pem ec2-user@$MONGO_PRIMARY_IP
```

On MongoDB Primary, initialize replica set:

```bash
# ============================================
# RUN ON: MongoDB Primary Instance
# ============================================

# Connect to MongoDB
mongosh

# Create admin user
use admin
db.createUser({
  user: "admin",
  pwd: "YourSecurePassword123!",  // CHANGE THIS
  roles: [
    { role: "root", db: "admin" }
  ]
})

# Authenticate
db.auth("admin", "YourSecurePassword123!")

# Initialize replica set
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "MONGO_PRIMARY_IP:27017", priority: 2 },
    { _id: 1, host: "MONGO_SECONDARY_IP:27017", priority: 1 }
  ]
})

# Check status
rs.status()

# Create application user
use myapp
db.createUser({
  user: "appuser",
  pwd: "AppPassword123!",  // CHANGE THIS
  roles: [
    { role: "readWrite", db: "myapp" }
  ]
})

exit
```

**Replace `MONGO_PRIMARY_IP` and `MONGO_SECONDARY_IP` with actual IPs from STEP 2.3**

---

### 📍 **STEP 2.5: Verify Replica Set**

```bash
# ============================================
# RUN ON: MongoDB Primary Instance
# ============================================

mongosh -u admin -p YourSecurePassword123! --authenticationDatabase admin

# Check replica set status
rs.status()

# Check configuration
rs.conf()

# Test replication
use test
db.testCollection.insertOne({ test: "data", timestamp: new Date() })

# Exit and connect to secondary
exit
```

Connect to secondary and verify:

```bash
# ============================================
# RUN ON: MongoDB Secondary Instance
# ============================================

mongosh -u admin -p YourSecurePassword123! --authenticationDatabase admin

# Allow reads from secondary
rs.secondaryOk()

# Verify data replicated
use test
db.testCollection.find()

exit
```

---

### 📍 **STEP 2.6: Configure Automated Backups**

Create backup script on primary:

```bash
# ============================================
# RUN ON: MongoDB Primary Instance
# ============================================

sudo cat > /usr/local/bin/mongodb-backup.sh <<'EOF'
#!/bin/bash

BACKUP_DIR="/backup/mongodb"
DATE=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="your-backup-bucket"  # CHANGE THIS

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
mongodump \
  --uri="mongodb://admin:YourSecurePassword123!@localhost:27017/?authSource=admin" \
  --out=$BACKUP_DIR/$DATE

# Compress backup
tar -czf $BACKUP_DIR/mongodb-backup-$DATE.tar.gz -C $BACKUP_DIR $DATE

# Upload to S3
aws s3 cp $BACKUP_DIR/mongodb-backup-$DATE.tar.gz s3://$S3_BUCKET/mongodb-backups/

# Clean up local backups older than 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} +

echo "✅ Backup completed: mongodb-backup-$DATE.tar.gz"
EOF

sudo chmod +x /usr/local/bin/mongodb-backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/mongodb-backup.sh >> /var/log/mongodb-backup.log 2>&1") | crontab -
```

---

## ✅ Verification

### Check MongoDB Status

```bash
# On MongoDB instance
sudo systemctl status mongod
```

### Check Replica Set Status

```bash
mongosh -u admin -p YourSecurePassword123! --authenticationDatabase admin

rs.status()
rs.isMaster()
```

### Test Connection from Application Tier

```bash
# From web/app instance
mongosh "mongodb://MONGO_PRIMARY_IP:27017,MONGO_SECONDARY_IP:27017/?replicaSet=rs0" \
  -u appuser -p AppPassword123! --authenticationDatabase myapp
```

---

## 📊 MongoDB Configuration Summary

| Parameter | Value |
|-----------|-------|
| **Replica Set Name** | rs0 |
| **Primary** | AZ-1 (10.0.11.0/24) |
| **Secondary** | AZ-2 (10.0.12.0/24) |
| **Port** | 27017 |
| **Instance Type** | t3.large |
| **Storage** | 100GB EBS (gp3, encrypted) |
| **Cache Size** | 2GB |
| **Authentication** | Enabled |
| **Backup** | Daily at 2 AM |

---

## 🎯 Connection String

For your application:

```javascript
mongodb://appuser:AppPassword123!@MONGO_PRIMARY_IP:27017,MONGO_SECONDARY_IP:27017/myapp?replicaSet=rs0&readPreference=primaryPreferred&w=majority
```

---

## 🔧 Troubleshooting

### Issue: "Replica set not initializing"
**Solution**: Check network connectivity between instances, verify security group rules

### Issue: "Authentication failed"
**Solution**: Verify user credentials, check authentication database

### Issue: "Secondary not syncing"
**Solution**: Check oplog size, verify network connectivity, check MongoDB logs

### Issue: "Connection timeout"
**Solution**: Verify security group allows port 27017, check MongoDB is listening on 0.0.0.0

---

## 🎯 Next Steps

✅ **Database tier is ready!**

Now proceed to:
1. **[Web/App Tier Setup](./03-WEBAPP-TIER-SETUP.md)** - Deploy application servers
2. **[Auto-Scaling Setup](./04-AUTOSCALING-SETUP.md)** - Configure auto-scaling

---

**Database setup complete! 🎉**
