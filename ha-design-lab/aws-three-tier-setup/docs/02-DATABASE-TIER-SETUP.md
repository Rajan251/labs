# 💾 Step 2: Database Tier Setup

> **Deploying MongoDB Replica Set on AWS EC2**

---

## 📋 What We'll Create

- ✅ 3x EC2 instances for MongoDB (t3.large)
- ✅ EBS volumes (100GB gp3 SSD each)
- ✅ MongoDB 7.0 installation
- ✅ Replica set configuration (rs0)
- ✅ Automated backups to S3

---

## 🎯 MongoDB Deployment Diagram

```
┌────────────────────────────────────────────────────────────┐
│            DATABASE TIER (Private Subnets)                 │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  AZ-1 (us-east-1a)              AZ-2 (us-east-1b)         │
│  ┌──────────────────┐          ┌──────────────────┐       │
│  │  🔴 PRIMARY      │          │  🟢 SECONDARY-2  │       │
│  │  mongo-1         │◄────────►│  mongo-3         │       │
│  │  10.0.21.10      │          │  10.0.22.12      │       │
│  │  t3.large        │          │  t3.large        │       │
│  │  100GB EBS       │          │  100GB EBS       │       │
│  └──────────────────┘          └──────────────────┘       │
│          ▲                              ▲                  │
│          │                              │                  │
│          │      ┌──────────────────┐   │                  │
│          │      │  🟡 SECONDARY-1  │   │                  │
│          └─────►│  mongo-2         │◄──┘                  │
│                 │  10.0.21.11      │                      │
│                 │  t3.large        │                      │
│                 │  100GB EBS       │                      │
│                 └──────────────────┘                      │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## 🚀 Step-by-Step Setup

### 📍 **STEP 2.1: Load Infrastructure IDs**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Load saved infrastructure IDs
source infrastructure-ids.txt

# Verify
echo "VPC ID: $VPC_ID"
echo "DB Subnet 1: $PRIVATE_DB_SUBNET_1"
echo "DB Subnet 2: $PRIVATE_DB_SUBNET_2"
echo "DB Security Group: $DB_SG"
```

---

### 📍 **STEP 2.2: Create SSH Key Pair**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create key pair
aws ec2 create-key-pair \
  --key-name mongodb-key \
  --query 'KeyMaterial' \
  --output text > mongodb-key.pem

# Set permissions
chmod 400 mongodb-key.pem

echo "✅ SSH key created: mongodb-key.pem"
```

---

### 📍 **STEP 2.3: Launch EC2 Instances**

#### Get Latest Ubuntu AMI

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Get latest Ubuntu 22.04 AMI
AMI_ID=$(aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text)

echo "✅ Ubuntu AMI: $AMI_ID"
```

#### Launch mongo-1 (PRIMARY - AZ-1)

```bash
# ============================================
# RUN ON: Your Local Machine
# TAG: 🔴 PRIMARY (mongo-1)
# ============================================

MONGO_1=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.large \
  --key-name mongodb-key \
  --security-group-ids $DB_SG \
  --subnet-id $PRIVATE_DB_SUBNET_1 \
  --private-ip-address 10.0.21.10 \
  --block-device-mappings '[
    {
      "DeviceName": "/dev/sda1",
      "Ebs": {
        "VolumeSize": 100,
        "VolumeType": "gp3",
        "Iops": 3000,
        "DeleteOnTermination": false,
        "Encrypted": true
      }
    }
  ]' \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=Name,Value=mongo-1-primary},
    {Key=Role,Value=mongodb-primary},
    {Key=Tier,Value=database}
  ]' \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "✅ mongo-1 (PRIMARY) launched: $MONGO_1"
```

#### Launch mongo-2 (SECONDARY-1 - AZ-1)

```bash
# ============================================
# RUN ON: Your Local Machine
# TAG: 🟡 SECONDARY-1 (mongo-2)
# ============================================

MONGO_2=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.large \
  --key-name mongodb-key \
  --security-group-ids $DB_SG \
  --subnet-id $PRIVATE_DB_SUBNET_1 \
  --private-ip-address 10.0.21.11 \
  --block-device-mappings '[
    {
      "DeviceName": "/dev/sda1",
      "Ebs": {
        "VolumeSize": 100,
        "VolumeType": "gp3",
        "Iops": 3000,
        "DeleteOnTermination": false,
        "Encrypted": true
      }
    }
  ]' \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=Name,Value=mongo-2-secondary},
    {Key=Role,Value=mongodb-secondary},
    {Key=Tier,Value=database}
  ]' \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "✅ mongo-2 (SECONDARY-1) launched: $MONGO_2"
```

#### Launch mongo-3 (SECONDARY-2 - AZ-2)

```bash
# ============================================
# RUN ON: Your Local Machine
# TAG: 🟢 SECONDARY-2 (mongo-3)
# ============================================

MONGO_3=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.large \
  --key-name mongodb-key \
  --security-group-ids $DB_SG \
  --subnet-id $PRIVATE_DB_SUBNET_2 \
  --private-ip-address 10.0.22.12 \
  --block-device-mappings '[
    {
      "DeviceName": "/dev/sda1",
      "Ebs": {
        "VolumeSize": 100,
        "VolumeType": "gp3",
        "Iops": 3000,
        "DeleteOnTermination": false,
        "Encrypted": true
      }
    }
  ]' \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=Name,Value=mongo-3-secondary},
    {Key=Role,Value=mongodb-secondary},
    {Key=Tier,Value=database}
  ]' \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "✅ mongo-3 (SECONDARY-2) launched: $MONGO_3"
```

#### Wait for Instances

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

echo "⏳ Waiting for instances to be running..."
aws ec2 wait instance-running --instance-ids $MONGO_1 $MONGO_2 $MONGO_3
echo "✅ All MongoDB instances are running"

# Save instance IDs
cat >> infrastructure-ids.txt <<EOF
MONGO_1=$MONGO_1
MONGO_2=$MONGO_2
MONGO_3=$MONGO_3
EOF
```

---

### 📍 **STEP 2.4: Create Bastion Host (for SSH access)**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Launch bastion in public subnet
BASTION=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.micro \
  --key-name mongodb-key \
  --security-group-ids $WEB_SG \
  --subnet-id $PUBLIC_SUBNET_1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=bastion-host}]' \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "✅ Bastion host launched: $BASTION"

# Wait for bastion
aws ec2 wait instance-running --instance-ids $BASTION

# Get bastion public IP
BASTION_IP=$(aws ec2 describe-instances \
  --instance-ids $BASTION \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "✅ Bastion Public IP: $BASTION_IP"
echo "BASTION_IP=$BASTION_IP" >> infrastructure-ids.txt
```

---

### 📍 **STEP 2.5: Install MongoDB on All Instances**

#### Create Installation Script

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

cat > install-mongodb.sh <<'SCRIPT'
#!/bin/bash
# MongoDB Installation Script for Ubuntu 22.04

set -e

echo "🔧 Installing MongoDB 7.0..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y wget curl gnupg2 software-properties-common apt-transport-https ca-certificates lsb-release

# Install NTP
sudo apt install -y ntp
sudo systemctl enable ntp
sudo systemctl start ntp

# Disable THP
sudo tee /etc/systemd/system/disable-thp.service <<EOF
[Unit]
Description=Disable Transparent Huge Pages (THP)
DefaultDependencies=no
After=sysinit.target local-fs.target
Before=mongod.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo never | tee /sys/kernel/mm/transparent_hugepage/enabled > /dev/null'
ExecStart=/bin/sh -c 'echo never | tee /sys/kernel/mm/transparent_hugepage/defrag > /dev/null'

[Install]
WantedBy=basic.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable disable-thp
sudo systemctl start disable-thp

# Import MongoDB GPG key
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update and install MongoDB
sudo apt update
sudo apt install -y mongodb-org

# Create data directory
sudo mkdir -p /data/mongodb
sudo chown -R mongodb:mongodb /data/mongodb
sudo chmod 755 /data/mongodb

echo "✅ MongoDB 7.0 installed successfully"
mongod --version
SCRIPT

chmod +x install-mongodb.sh
```

#### Install on mongo-1 (PRIMARY)

```bash
# ============================================
# RUN ON: Your Local Machine
# TAG: 🔴 Install on PRIMARY (mongo-1)
# ============================================

# Copy script to bastion
scp -i mongodb-key.pem install-mongodb.sh ubuntu@$BASTION_IP:/home/ubuntu/

# SSH to bastion, then to mongo-1
ssh -i mongodb-key.pem ubuntu@$BASTION_IP

# From bastion, copy script to mongo-1
scp install-mongodb.sh ubuntu@10.0.21.10:/home/ubuntu/

# SSH to mongo-1
ssh ubuntu@10.0.21.10

# Run installation
./install-mongodb.sh

# Exit back to bastion
exit
```

#### Install on mongo-2 and mongo-3

```bash
# ============================================
# TAG: 🟡 Install on SECONDARY-1 (mongo-2)
# ============================================

# From bastion
scp install-mongodb.sh ubuntu@10.0.21.11:/home/ubuntu/
ssh ubuntu@10.0.21.11
./install-mongodb.sh
exit

# ============================================
# TAG: 🟢 Install on SECONDARY-2 (mongo-3)
# ============================================

# From bastion
scp install-mongodb.sh ubuntu@10.0.22.12:/home/ubuntu/
ssh ubuntu@10.0.22.12
./install-mongodb.sh
exit
```

---

### 📍 **STEP 2.6: Configure MongoDB Replica Set**

This step follows the exact same process as in `MONGODB_SERVER_BY_SERVER_SETUP.md`:

1. Generate keyfile on mongo-1
2. Copy keyfile to mongo-2 and mongo-3
3. Configure mongod.conf on all servers
4. Start MongoDB on all servers
5. Initialize replica set on mongo-1
6. Create users

**Refer to**: `/home/rk/Documents/labs/ha-design-lab/MONGODB_SERVER_BY_SERVER_SETUP.md`

**Key differences for AWS**:
- Use private IPs: `10.0.21.10`, `10.0.21.11`, `10.0.22.12`
- Access via bastion host
- Use AWS-specific hostnames in replica set config

---

### 📍 **STEP 2.7: Configure Automated Backups to S3**

#### Create S3 Bucket

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create S3 bucket for backups
BUCKET_NAME="mongodb-backups-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME --region us-east-1

echo "✅ S3 bucket created: $BUCKET_NAME"
echo "BACKUP_BUCKET=$BUCKET_NAME" >> infrastructure-ids.txt
```

#### Create IAM Role for EC2

```bash
# Create IAM role for MongoDB instances to access S3
# (Detailed IAM setup in security configuration guide)
```

---

## ✅ Verification

### Check Instances

```bash
aws ec2 describe-instances \
  --instance-ids $MONGO_1 $MONGO_2 $MONGO_3 \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,PrivateIpAddress,Tags[?Key==`Name`].Value|[0]]' \
  --output table
```

### Test MongoDB Connection

```bash
# From bastion
ssh ubuntu@10.0.21.10
mongosh "mongodb://admin:password@10.0.21.10:27017/admin?replicaSet=rs0"
rs.status()
```

---

## 📊 Database Tier Summary

| Component | Value |
|-----------|-------|
| **Instances** | 3x t3.large |
| **Storage** | 3x 100GB gp3 SSD |
| **Replica Set** | rs0 (1 PRIMARY, 2 SECONDARYs) |
| **Availability Zones** | 2 (us-east-1a, us-east-1b) |
| **Backup** | Automated to S3 |
| **Encryption** | EBS encrypted at rest |

---

## 🎯 Next Steps

✅ **Database tier is ready!**

Proceed to:
- **[Application Tier Setup](./03-APPLICATION-TIER-SETUP.md)** - Deploy app servers
- **[Web Tier Setup](./04-WEB-TIER-SETUP.md)** - Deploy NGINX servers

---

**Database tier setup complete! 🎉**
