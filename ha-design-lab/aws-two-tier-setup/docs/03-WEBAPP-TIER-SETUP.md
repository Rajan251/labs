# 🌐 Step 3: Web/App Tier Setup - NGINX + Node.js

> **Deploying Web and Application Servers with Auto-Scaling**

---

## 📋 What We'll Create

- ✅ Launch template for web/app instances
- ✅ NGINX web server configuration
- ✅ Node.js application deployment
- ✅ Health check endpoint
- ✅ CloudWatch monitoring
- ✅ Auto-scaling group (configured in next step)

---

## 🎯 Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Application Load Balancer                              │
│  http://two-tier-alb-xxx.us-east-1.elb.amazonaws.com   │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                              │
        ▼                              ▼
┌─────────────────┐          ┌─────────────────┐
│  Web/App        │          │  Web/App        │
│  Instance 1     │          │  Instance 2     │
│  (AZ-1)         │          │  (AZ-2)         │
│                 │          │                 │
│  ┌───────────┐  │          │  ┌───────────┐  │
│  │  NGINX    │  │          │  │  NGINX    │  │
│  │  Port 80  │  │          │  │  Port 80  │  │
│  └─────┬─────┘  │          │  └─────┬─────┘  │
│        │        │          │        │        │
│  ┌─────▼─────┐  │          │  ┌─────▼─────┐  │
│  │  Node.js  │  │          │  │  Node.js  │  │
│  │  Port 3000│  │          │  │  Port 3000│  │
│  └─────┬─────┘  │          │  └─────┬─────┘  │
│        │        │          │        │        │
└────────┼────────┘          └────────┼────────┘
         │                            │
         └────────────┬───────────────┘
                      │
              ┌───────▼────────┐
              │  MongoDB       │
              │  Replica Set   │
              └────────────────┘
```

---

## 🚀 Step-by-Step Setup

### 📍 **STEP 3.1: Create Application Code**

Create a simple Node.js application:

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

mkdir -p app
cd app

# Create package.json
cat > package.json <<'EOF'
{
  "name": "two-tier-app",
  "version": "1.0.0",
  "description": "Two-tier application with MongoDB",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongodb": "^6.0.0"
  }
}
EOF

# Create server.js
cat > server.js <<'EOF'
const express = require('express');
const { MongoClient } = require('mongodb');

const app = express();
const PORT = process.env.PORT || 3000;

// MongoDB connection
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017';
let db;

// Connect to MongoDB
MongoClient.connect(MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
  .then(client => {
    console.log('✅ Connected to MongoDB');
    db = client.db('myapp');
  })
  .catch(err => {
    console.error('❌ MongoDB connection error:', err);
  });

// Middleware
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  const health = {
    status: 'UP',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    mongodb: db ? 'connected' : 'disconnected'
  };
  res.status(200).json(health);
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'Welcome to Two-Tier Application',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// Get all items
app.get('/api/items', async (req, res) => {
  try {
    const items = await db.collection('items').find().toArray();
    res.json({ success: true, count: items.length, data: items });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Create item
app.post('/api/items', async (req, res) => {
  try {
    const result = await db.collection('items').insertOne({
      ...req.body,
      createdAt: new Date()
    });
    res.status(201).json({ success: true, id: result.insertedId });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
EOF

# Create .env file
cat > .env <<'EOF'
PORT=3000
MONGO_URI=mongodb://appuser:AppPassword123!@MONGO_PRIMARY_IP:27017,MONGO_SECONDARY_IP:27017/myapp?replicaSet=rs0&readPreference=primaryPreferred
EOF

echo "✅ Application code created"
```

---

### 📍 **STEP 3.2: Create User Data Script**

Create `webapp-userdata.sh`:

```bash
cat > webapp-userdata.sh <<'EOF'
#!/bin/bash

# Update system
yum update -y

# Install Node.js 18
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs

# Install NGINX
amazon-linux-extras install nginx1 -y

# Install Git
yum install -y git

# Create application directory
mkdir -p /var/www/app
cd /var/www/app

# Clone or create application (replace with your repo)
cat > package.json <<'PKG'
{
  "name": "two-tier-app",
  "version": "1.0.0",
  "description": "Two-tier application with MongoDB",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongodb": "^6.0.0"
  }
}
PKG

cat > server.js <<'APP'
const express = require('express');
const { MongoClient } = require('mongodb');

const app = express();
const PORT = process.env.PORT || 3000;

const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017';
let db;

MongoClient.connect(MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
  .then(client => {
    console.log('✅ Connected to MongoDB');
    db = client.db('myapp');
  })
  .catch(err => {
    console.error('❌ MongoDB connection error:', err);
  });

app.use(express.json());

app.get('/health', (req, res) => {
  const health = {
    status: 'UP',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    mongodb: db ? 'connected' : 'disconnected',
    hostname: require('os').hostname()
  };
  res.status(200).json(health);
});

app.get('/', (req, res) => {
  res.json({
    message: 'Welcome to Two-Tier Application',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    hostname: require('os').hostname()
  });
});

app.get('/api/items', async (req, res) => {
  try {
    const items = await db.collection('items').find().toArray();
    res.json({ success: true, count: items.length, data: items });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/items', async (req, res) => {
  try {
    const result = await db.collection('items').insertOne({
      ...req.body,
      createdAt: new Date()
    });
    res.status(201).json({ success: true, id: result.insertedId });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
APP

# Get MongoDB IPs from parameter store or hardcode
# For now, we'll use environment variables
cat > .env <<'ENV'
PORT=3000
MONGO_URI=mongodb://appuser:AppPassword123!@MONGO_PRIMARY_IP:27017,MONGO_SECONDARY_IP:27017/myapp?replicaSet=rs0&readPreference=primaryPreferred
ENV

# Install dependencies
npm install

# Create systemd service
cat > /etc/systemd/system/webapp.service <<'SERVICE'
[Unit]
Description=Two-Tier Web Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/app
EnvironmentFile=/var/www/app/.env
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Start application
systemctl daemon-reload
systemctl start webapp
systemctl enable webapp

# Configure NGINX
cat > /etc/nginx/nginx.conf <<'NGINX'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 4096;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # Upstream for Node.js app
    upstream nodejs_backend {
        server 127.0.0.1:3000;
        keepalive 64;
    }

    server {
        listen       80 default_server;
        listen       [::]:80 default_server;
        server_name  _;

        # Health check endpoint
        location /health {
            proxy_pass http://nodejs_backend;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Proxy all requests to Node.js
        location / {
            proxy_pass http://nodejs_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }
    }
}
NGINX

# Start NGINX
systemctl start nginx
systemctl enable nginx

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json <<'CW'
{
  "metrics": {
    "namespace": "WebApp",
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
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "/aws/webapp/nginx-access",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/nginx/error.log",
            "log_group_name": "/aws/webapp/nginx-error",
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

echo "✅ Web/App setup complete"
EOF

chmod +x webapp-userdata.sh
```

---

### 📍 **STEP 3.3: Create Launch Template**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Load infrastructure IDs
source infrastructure-ids.txt

# Get AMI ID
AMI_ID=$(aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text)

# Update user data with actual MongoDB IPs
sed -i "s/MONGO_PRIMARY_IP/$MONGO_PRIMARY_IP/g" webapp-userdata.sh
sed -i "s/MONGO_SECONDARY_IP/$MONGO_SECONDARY_IP/g" webapp-userdata.sh

# Encode user data to base64
USER_DATA_BASE64=$(base64 -w 0 webapp-userdata.sh)

# Create launch template
LAUNCH_TEMPLATE_ID=$(aws ec2 create-launch-template \
  --launch-template-name webapp-launch-template \
  --version-description "Initial version" \
  --launch-template-data "{
    \"ImageId\": \"$AMI_ID\",
    \"InstanceType\": \"t3.medium\",
    \"KeyName\": \"mongodb-key\",
    \"SecurityGroupIds\": [\"$WEBAPP_SG\"],
    \"UserData\": \"$USER_DATA_BASE64\",
    \"BlockDeviceMappings\": [{
      \"DeviceName\": \"/dev/xvda\",
      \"Ebs\": {
        \"VolumeSize\": 30,
        \"VolumeType\": \"gp3\",
        \"Encrypted\": true,
        \"DeleteOnTermination\": true
      }
    }],
    \"TagSpecifications\": [{
      \"ResourceType\": \"instance\",
      \"Tags\": [
        {\"Key\": \"Name\", \"Value\": \"webapp-instance\"},
        {\"Key\": \"Tier\", \"Value\": \"webapp\"}
      ]
    }],
    \"IamInstanceProfile\": {
      \"Name\": \"EC2CloudWatchRole\"
    },
    \"Monitoring\": {
      \"Enabled\": true
    }
  }" \
  --query 'LaunchTemplate.LaunchTemplateId' \
  --output text)

echo "✅ Launch Template Created: $LAUNCH_TEMPLATE_ID"

# Save to file
echo "LAUNCH_TEMPLATE_ID=$LAUNCH_TEMPLATE_ID" >> infrastructure-ids.txt
```

---

### 📍 **STEP 3.4: Create IAM Role for CloudWatch**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create trust policy
cat > ec2-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
  --role-name EC2CloudWatchRole \
  --assume-role-policy-document file://ec2-trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name EC2CloudWatchRole \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy

aws iam attach-role-policy \
  --role-name EC2CloudWatchRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name EC2CloudWatchRole

# Add role to instance profile
aws iam add-role-to-instance-profile \
  --instance-profile-name EC2CloudWatchRole \
  --role-name EC2CloudWatchRole

echo "✅ IAM Role created: EC2CloudWatchRole"
```

---

### 📍 **STEP 3.5: Launch Test Instance**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Launch instance from template
TEST_INSTANCE=$(aws ec2 run-instances \
  --launch-template LaunchTemplateId=$LAUNCH_TEMPLATE_ID \
  --subnet-id $PUBLIC_SUBNET_1 \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "✅ Test instance launched: $TEST_INSTANCE"

# Wait for instance to be running
echo "⏳ Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $TEST_INSTANCE

# Get public IP
TEST_INSTANCE_IP=$(aws ec2 describe-instances \
  --instance-ids $TEST_INSTANCE \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "✅ Test instance IP: $TEST_INSTANCE_IP"

# Wait for user data to complete (5 minutes)
echo "⏳ Waiting for application to start (5 minutes)..."
sleep 300

# Test health endpoint
echo "Testing health endpoint..."
curl http://$TEST_INSTANCE_IP/health

# Test root endpoint
echo "Testing root endpoint..."
curl http://$TEST_INSTANCE_IP/
```

---

### 📍 **STEP 3.6: Register Instance with Target Group**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Register instance with target group
aws elbv2 register-targets \
  --target-group-arn $TG_ARN \
  --targets Id=$TEST_INSTANCE

echo "✅ Instance registered with target group"

# Wait for health check to pass
echo "⏳ Waiting for health check to pass..."
sleep 60

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN

# Test via ALB
echo "Testing via ALB..."
curl http://$ALB_DNS/health
curl http://$ALB_DNS/
```

---

## ✅ Verification

### Check Application Status

```bash
# SSH to instance
ssh -i mongodb-key.pem ec2-user@$TEST_INSTANCE_IP

# Check Node.js service
sudo systemctl status webapp

# Check NGINX
sudo systemctl status nginx

# Check logs
sudo journalctl -u webapp -f
sudo tail -f /var/log/nginx/access.log
```

### Test Endpoints

```bash
# Health check
curl http://$ALB_DNS/health

# Root endpoint
curl http://$ALB_DNS/

# Create item
curl -X POST http://$ALB_DNS/api/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Item","description":"Created via API"}'

# Get items
curl http://$ALB_DNS/api/items
```

---

## 📊 Configuration Summary

| Component | Configuration |
|-----------|---------------|
| **Instance Type** | t3.medium |
| **Web Server** | NGINX (Port 80) |
| **Application** | Node.js (Port 3000) |
| **Storage** | 30GB EBS (gp3, encrypted) |
| **Monitoring** | CloudWatch Agent |
| **Health Check** | /health endpoint |

---

## 🎯 Next Steps

✅ **Web/App tier is ready!**

Now proceed to:
1. **[Auto-Scaling Setup](./04-AUTOSCALING-SETUP.md)** - Configure auto-scaling group
2. **[Testing & Verification](./06-TESTING-VERIFICATION.md)** - Load testing and validation

---

**Web/App tier setup complete! 🎉**
