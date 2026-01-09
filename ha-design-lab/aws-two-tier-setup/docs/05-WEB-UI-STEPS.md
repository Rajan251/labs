# 🖥️ Step 5: Web UI Setup Steps - AWS Console Guide

> **Complete Step-by-Step Guide Using AWS Management Console**

---

## 📋 Overview

This guide walks you through setting up the entire two-tier architecture using the AWS Management Console (Web UI). Perfect for visual learners and those new to AWS.

**Estimated Time**: 60-90 minutes

---

## 🎯 What You'll Create

1. VPC and Networking
2. Security Groups
3. Application Load Balancer
4. MongoDB Database Instances
5. Web/App Instances
6. Auto-Scaling Group
7. CloudWatch Monitoring

---

## 🚀 Step-by-Step Instructions

### 📍 **SECTION 1: VPC and Networking**

#### Step 1.1: Create VPC

1. **Navigate to VPC Dashboard**
   - Open AWS Console: https://console.aws.amazon.com
   - Search for "VPC" in the search bar
   - Click "VPC"

2. **Create VPC**
   - Click "Create VPC" button
   - Select "VPC only"
   - **Name tag**: `two-tier-vpc`
   - **IPv4 CIDR block**: `10.0.0.0/16`
   - **IPv6 CIDR block**: No IPv6 CIDR block
   - **Tenancy**: Default
   - Click "Create VPC"

3. **Enable DNS Settings**
   - Select your VPC
   - Click "Actions" → "Edit VPC settings"
   - ✅ Enable DNS resolution
   - ✅ Enable DNS hostnames
   - Click "Save"

#### Step 1.2: Create Internet Gateway

1. **Create Internet Gateway**
   - In VPC Dashboard, click "Internet Gateways"
   - Click "Create internet gateway"
   - **Name tag**: `two-tier-igw`
   - Click "Create internet gateway"

2. **Attach to VPC**
   - Select the internet gateway
   - Click "Actions" → "Attach to VPC"
   - Select `two-tier-vpc`
   - Click "Attach internet gateway"

#### Step 1.3: Create Subnets

**Public Subnet 1 (Web/App - AZ-1)**

1. Click "Subnets" in left menu
2. Click "Create subnet"
3. **VPC**: Select `two-tier-vpc`
4. **Subnet name**: `public-webapp-subnet-1`
5. **Availability Zone**: `us-east-1a`
6. **IPv4 CIDR block**: `10.0.1.0/24`
7. Click "Create subnet"

**Public Subnet 2 (Web/App - AZ-2)**

1. Click "Create subnet"
2. **VPC**: Select `two-tier-vpc`
3. **Subnet name**: `public-webapp-subnet-2`
4. **Availability Zone**: `us-east-1b`
5. **IPv4 CIDR block**: `10.0.2.0/24`
6. Click "Create subnet"

**Private Subnet 1 (Database - AZ-1)**

1. Click "Create subnet"
2. **VPC**: Select `two-tier-vpc`
3. **Subnet name**: `private-db-subnet-1`
4. **Availability Zone**: `us-east-1a`
5. **IPv4 CIDR block**: `10.0.11.0/24`
6. Click "Create subnet"

**Private Subnet 2 (Database - AZ-2)**

1. Click "Create subnet"
2. **VPC**: Select `two-tier-vpc`
3. **Subnet name**: `private-db-subnet-2`
4. **Availability Zone**: `us-east-1b`
5. **IPv4 CIDR block**: `10.0.12.0/24`
6. Click "Create subnet"

**Enable Auto-assign Public IP for Public Subnets**

1. Select `public-webapp-subnet-1`
2. Click "Actions" → "Edit subnet settings"
3. ✅ Enable "Auto-assign public IPv4 address"
4. Click "Save"
5. Repeat for `public-webapp-subnet-2`

#### Step 1.4: Create Route Tables

**Public Route Table**

1. Click "Route Tables" in left menu
2. Click "Create route table"
3. **Name**: `public-rt`
4. **VPC**: Select `two-tier-vpc`
5. Click "Create route table"

6. **Add Internet Route**
   - Select `public-rt`
   - Click "Routes" tab
   - Click "Edit routes"
   - Click "Add route"
   - **Destination**: `0.0.0.0/0`
   - **Target**: Select "Internet Gateway" → `two-tier-igw`
   - Click "Save changes"

7. **Associate Subnets**
   - Click "Subnet associations" tab
   - Click "Edit subnet associations"
   - ✅ Select `public-webapp-subnet-1`
   - ✅ Select `public-webapp-subnet-2`
   - Click "Save associations"

**Private Route Table**

1. Click "Create route table"
2. **Name**: `private-db-rt`
3. **VPC**: Select `two-tier-vpc`
4. Click "Create route table"

5. **Associate Subnets**
   - Select `private-db-rt`
   - Click "Subnet associations" tab
   - Click "Edit subnet associations"
   - ✅ Select `private-db-subnet-1`
   - ✅ Select `private-db-subnet-2`
   - Click "Save associations"

---

### 📍 **SECTION 2: Security Groups**

#### Step 2.1: Create ALB Security Group

1. **Navigate to Security Groups**
   - In VPC Dashboard, click "Security Groups"
   - Click "Create security group"

2. **Basic Details**
   - **Security group name**: `alb-sg`
   - **Description**: `Security group for Application Load Balancer`
   - **VPC**: Select `two-tier-vpc`

3. **Inbound Rules**
   - Click "Add rule"
   - **Type**: HTTP
   - **Source**: Anywhere-IPv4 (0.0.0.0/0)
   
   - Click "Add rule"
   - **Type**: HTTPS
   - **Source**: Anywhere-IPv4 (0.0.0.0/0)

4. **Outbound Rules** (default allows all)
   - Leave as is

5. Click "Create security group"

#### Step 2.2: Create Web/App Security Group

1. Click "Create security group"

2. **Basic Details**
   - **Security group name**: `webapp-tier-sg`
   - **Description**: `Security group for web/application tier`
   - **VPC**: Select `two-tier-vpc`

3. **Inbound Rules**
   - Click "Add rule"
   - **Type**: HTTP
   - **Source**: Custom → Select `alb-sg`
   
   - Click "Add rule"
   - **Type**: HTTPS
   - **Source**: Custom → Select `alb-sg`
   
   - Click "Add rule"
   - **Type**: Custom TCP
   - **Port**: 3000
   - **Source**: Custom → Select `alb-sg`
   
   - Click "Add rule"
   - **Type**: SSH
   - **Source**: My IP (automatically detects your IP)

4. Click "Create security group"

#### Step 2.3: Create Database Security Group

1. Click "Create security group"

2. **Basic Details**
   - **Security group name**: `db-tier-sg`
   - **Description**: `Security group for database tier`
   - **VPC**: Select `two-tier-vpc`

3. **Inbound Rules**
   - Click "Add rule"
   - **Type**: Custom TCP
   - **Port**: 27017
   - **Source**: Custom → Select `webapp-tier-sg`
   - **Description**: MongoDB from app tier
   
   - Click "Add rule"
   - **Type**: Custom TCP
   - **Port**: 27017
   - **Source**: Custom → Select `db-tier-sg` (itself)
   - **Description**: MongoDB replication
   
   - Click "Add rule"
   - **Type**: SSH
   - **Source**: My IP
   - **Description**: SSH access

4. Click "Create security group"

---

### 📍 **SECTION 3: Application Load Balancer**

#### Step 3.1: Create Target Group

1. **Navigate to Target Groups**
   - Search for "EC2" in AWS Console
   - Click "Target Groups" in left menu
   - Click "Create target group"

2. **Choose Target Type**
   - Select "Instances"
   - Click "Next"

3. **Configure Target Group**
   - **Target group name**: `webapp-target-group`
   - **Protocol**: HTTP
   - **Port**: 80
   - **VPC**: Select `two-tier-vpc`
   
4. **Health Checks**
   - **Health check protocol**: HTTP
   - **Health check path**: `/health`
   - **Advanced health check settings**:
     - **Healthy threshold**: 2
     - **Unhealthy threshold**: 3
     - **Timeout**: 5 seconds
     - **Interval**: 30 seconds
     - **Success codes**: 200

5. Click "Next"
6. Skip "Register targets" (we'll do this later)
7. Click "Create target group"

#### Step 3.2: Create Load Balancer

1. **Navigate to Load Balancers**
   - Click "Load Balancers" in left menu
   - Click "Create load balancer"

2. **Select Load Balancer Type**
   - Click "Create" under "Application Load Balancer"

3. **Basic Configuration**
   - **Load balancer name**: `two-tier-alb`
   - **Scheme**: Internet-facing
   - **IP address type**: IPv4

4. **Network Mapping**
   - **VPC**: Select `two-tier-vpc`
   - **Mappings**:
     - ✅ us-east-1a → Select `public-webapp-subnet-1`
     - ✅ us-east-1b → Select `public-webapp-subnet-2`

5. **Security Groups**
   - Remove default security group
   - ✅ Select `alb-sg`

6. **Listeners and Routing**
   - **Protocol**: HTTP
   - **Port**: 80
   - **Default action**: Forward to `webapp-target-group`

7. Click "Create load balancer"

8. **Note the DNS Name**
   - After creation, copy the DNS name (e.g., `two-tier-alb-xxx.us-east-1.elb.amazonaws.com`)

---

### 📍 **SECTION 4: Database Instances (MongoDB)**

#### Step 4.1: Create Key Pair

1. **Navigate to Key Pairs**
   - In EC2 Dashboard, click "Key Pairs"
   - Click "Create key pair"

2. **Create Key Pair**
   - **Name**: `mongodb-key`
   - **Key pair type**: RSA
   - **Private key file format**: .pem
   - Click "Create key pair"
   - **Save the downloaded file securely**

#### Step 4.2: Launch MongoDB Primary Instance

1. **Navigate to EC2 Instances**
   - Click "Instances" in left menu
   - Click "Launch instances"

2. **Name and Tags**
   - **Name**: `mongodb-primary`

3. **Application and OS Images**
   - Select "Amazon Linux 2 AMI (HVM)"
   - Architecture: 64-bit (x86)

4. **Instance Type**
   - Select `t3.large`

5. **Key Pair**
   - Select `mongodb-key`

6. **Network Settings**
   - Click "Edit"
   - **VPC**: Select `two-tier-vpc`
   - **Subnet**: Select `private-db-subnet-1`
   - **Auto-assign public IP**: Disable
   - **Firewall (security groups)**: Select existing → `db-tier-sg`

7. **Configure Storage**
   - **Size**: 100 GiB
   - **Volume type**: gp3
   - ✅ Encrypted

8. **Advanced Details**
   - Scroll down to "User data"
   - Copy and paste the MongoDB installation script (see below)

9. Click "Launch instance"

**MongoDB User Data Script:**

```bash
#!/bin/bash
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

mkdir -p /data/db
chown -R mongod:mongod /data/db

cat > /etc/mongod.conf <<'MONGOD'
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
storage:
  dbPath: /data/db
  journal:
    enabled: true
net:
  port: 27017
  bindIp: 0.0.0.0
security:
  authorization: enabled
replication:
  replSetName: rs0
MONGOD

systemctl start mongod
systemctl enable mongod
```

#### Step 4.3: Launch MongoDB Secondary Instance

1. Repeat Step 4.2 with these changes:
   - **Name**: `mongodb-secondary`
   - **Subnet**: Select `private-db-subnet-2` (AZ-2)
   - Use the same user data script

2. Click "Launch instance"

#### Step 4.4: Note Private IPs

1. Go to "Instances"
2. Select `mongodb-primary`
3. Copy the "Private IPv4 address" (e.g., 10.0.11.x)
4. Select `mongodb-secondary`
5. Copy the "Private IPv4 address" (e.g., 10.0.12.x)

**Save these IPs - you'll need them later!**

---

### 📍 **SECTION 5: Web/App Instances**

#### Step 5.1: Create Launch Template

1. **Navigate to Launch Templates**
   - In EC2 Dashboard, click "Launch Templates"
   - Click "Create launch template"

2. **Launch Template Name**
   - **Name**: `webapp-launch-template`
   - **Description**: Launch template for web/app tier

3. **Application and OS Images**
   - Select "Amazon Linux 2 AMI (HVM)"

4. **Instance Type**
   - Select `t3.medium`

5. **Key Pair**
   - Select `mongodb-key`

6. **Network Settings**
   - **Security groups**: Select `webapp-tier-sg`
   - (Don't select subnet - we'll do this in ASG)

7. **Storage**
   - **Size**: 30 GiB
   - **Volume type**: gp3
   - ✅ Encrypted

8. **Advanced Details**
   - **IAM instance profile**: (Create one if needed - see Step 5.2)
   - **User data**: Copy and paste the web/app installation script (see below)

9. Click "Create launch template"

**Web/App User Data Script:**

Replace `MONGO_PRIMARY_IP` and `MONGO_SECONDARY_IP` with actual IPs from Step 4.4

```bash
#!/bin/bash
yum update -y

# Install Node.js
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs

# Install NGINX
amazon-linux-extras install nginx1 -y

# Create application
mkdir -p /var/www/app
cd /var/www/app

cat > package.json <<'EOF'
{
  "name": "two-tier-app",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.2",
    "mongodb": "^6.0.0"
  }
}
EOF

cat > server.js <<'EOF'
const express = require('express');
const app = express();
const PORT = 3000;

app.get('/health', (req, res) => {
  res.json({ status: 'UP', timestamp: new Date() });
});

app.get('/', (req, res) => {
  res.json({ message: 'Welcome to Two-Tier App', hostname: require('os').hostname() });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
EOF

npm install

# Create systemd service
cat > /etc/systemd/system/webapp.service <<'EOF'
[Unit]
Description=Web Application
After=network.target

[Service]
Type=simple
WorkingDirectory=/var/www/app
ExecStart=/usr/bin/node server.js
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl start webapp
systemctl enable webapp

# Configure NGINX
cat > /etc/nginx/nginx.conf <<'EOF'
user nginx;
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    upstream nodejs_backend {
        server 127.0.0.1:3000;
    }

    server {
        listen 80;
        
        location / {
            proxy_pass http://nodejs_backend;
            proxy_set_header Host $host;
        }
    }
}
EOF

systemctl start nginx
systemctl enable nginx
```

#### Step 5.2: Create IAM Role (If Needed)

1. **Navigate to IAM**
   - Search for "IAM" in AWS Console
   - Click "Roles" in left menu
   - Click "Create role"

2. **Select Trusted Entity**
   - Select "AWS service"
   - Use case: EC2
   - Click "Next"

3. **Add Permissions**
   - Search and select:
     - `CloudWatchAgentServerPolicy`
     - `AmazonSSMManagedInstanceCore`
   - Click "Next"

4. **Name and Create**
   - **Role name**: `EC2CloudWatchRole`
   - Click "Create role"

---

### 📍 **SECTION 6: Auto-Scaling Group**

#### Step 6.1: Create Auto-Scaling Group

1. **Navigate to Auto Scaling Groups**
   - In EC2 Dashboard, click "Auto Scaling Groups"
   - Click "Create Auto Scaling group"

2. **Choose Launch Template**
   - **Name**: `webapp-asg`
   - **Launch template**: Select `webapp-launch-template`
   - Click "Next"

3. **Choose Instance Launch Options**
   - **VPC**: Select `two-tier-vpc`
   - **Availability Zones and subnets**:
     - ✅ `public-webapp-subnet-1`
     - ✅ `public-webapp-subnet-2`
   - Click "Next"

4. **Configure Advanced Options**
   - **Load balancing**: Attach to an existing load balancer
   - **Choose from your load balancer target groups**:
     - Select `webapp-target-group`
   - **Health checks**:
     - ✅ ELB health checks
     - **Health check grace period**: 300 seconds
   - Click "Next"

5. **Configure Group Size and Scaling**
   - **Desired capacity**: 2
   - **Minimum capacity**: 2
   - **Maximum capacity**: 10
   
   - **Scaling policies**: Target tracking scaling policy
   - **Metric type**: Average CPU utilization
   - **Target value**: 70
   - Click "Next"

6. **Add Notifications** (Optional)
   - Skip for now
   - Click "Next"

7. **Add Tags**
   - Click "Add tag"
   - **Key**: `Name`
   - **Value**: `webapp-asg-instance`
   - Click "Next"

8. **Review and Create**
   - Review all settings
   - Click "Create Auto Scaling group"

---

### 📍 **SECTION 7: CloudWatch Monitoring**

#### Step 7.1: Create Dashboard

1. **Navigate to CloudWatch**
   - Search for "CloudWatch" in AWS Console
   - Click "Dashboards" in left menu
   - Click "Create dashboard"

2. **Dashboard Name**
   - **Name**: `two-tier-dashboard`
   - Click "Create dashboard"

3. **Add Widgets**
   - Click "Add widget"
   - Select "Line" chart
   - Click "Next"

4. **Configure Widget**
   - **Metrics**: Select "EC2" → "By Auto Scaling Group"
   - ✅ CPUUtilization for `webapp-asg`
   - Click "Create widget"

5. **Add More Widgets**
   - Repeat for:
     - ALB Request Count
     - Target Response Time
     - Healthy/Unhealthy Host Count

6. Click "Save dashboard"

---

## ✅ Verification Steps

### 1. Test Load Balancer

1. Copy ALB DNS name
2. Open in browser: `http://your-alb-dns-name`
3. Should see: `{"message":"Welcome to Two-Tier App",...}`

### 2. Test Health Endpoint

1. Open: `http://your-alb-dns-name/health`
2. Should see: `{"status":"UP",...}`

### 3. Check Auto-Scaling

1. Go to Auto Scaling Groups
2. Select `webapp-asg`
3. Verify:
   - Desired: 2
   - Current: 2
   - Instances are "InService"

### 4. Check Target Group

1. Go to Target Groups
2. Select `webapp-target-group`
3. Click "Targets" tab
4. Verify both instances are "healthy"

---

## 📊 Summary

You've successfully created:

- ✅ VPC with 4 subnets (2 public, 2 private)
- ✅ Internet Gateway and Route Tables
- ✅ 3 Security Groups (ALB, Web/App, Database)
- ✅ Application Load Balancer
- ✅ 2 MongoDB instances (Primary + Secondary)
- ✅ Auto-Scaling Group (2-10 instances)
- ✅ CloudWatch Dashboard

---

## 🎯 Next Steps

1. **[Configure MongoDB Replica Set](./02-DATABASE-TIER-SETUP.md#step-24-configure-replica-set)**
2. **[Test Auto-Scaling](./04-AUTOSCALING-SETUP.md#testing-auto-scaling)**
3. **[Run Load Tests](./06-TESTING-VERIFICATION.md)**

---

**Web UI setup complete! 🎉**
