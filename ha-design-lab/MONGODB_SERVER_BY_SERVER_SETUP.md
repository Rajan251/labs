# MongoDB Replica Set - Server-by-Server Installation Guide

> **Complete step-by-step guide with clear labels: PRIMARY, SECONDARY-1, SECONDARY-2**  
> **Includes: Installation → Configuration → Code Implementation → Testing**

---

## 📋 Table of Contents

1. [Infrastructure Overview](#infrastructure-overview)
2. [Server-by-Server Installation](#server-by-server-installation)
3. [Replica Set Initialization](#replica-set-initialization)
4. [Code-Level Implementation](#code-level-implementation)
5. [Complete Testing Guide](#complete-testing-guide)
6. [Troubleshooting](#troubleshooting)

---

## Infrastructure Overview

### Server Roles

```
┌─────────────────────────────────────────────────────────────┐
│                    REPLICA SET: rs0                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  │    PRIMARY       │  │   SECONDARY-1    │  │   SECONDARY-2    │
│  │    mongo-1       │  │    mongo-2       │  │    mongo-3       │
│  │   10.0.1.10      │  │   10.0.1.11      │  │   10.0.1.12      │
│  │   Port: 27017    │  │   Port: 27017    │  │   Port: 27017    │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘
│         │                      │                      │          │
│         └──────────────────────┴──────────────────────┘          │
│                     Oplog Replication                           │
└─────────────────────────────────────────────────────────────────┘
```

### Server Specifications

| Server | Hostname | IP Address | Role | Priority | Votes |
|--------|----------|------------|------|----------|-------|
| **mongo-1** | mongo-1 | 10.0.1.10 | PRIMARY | 2 | 1 |
| **mongo-2** | mongo-2 | 10.0.1.11 | SECONDARY-1 | 1 | 1 |
| **mongo-3** | mongo-3 | 10.0.1.12 | SECONDARY-2 | 1 | 1 |

---

## Server-by-Server Installation

### 🔴 STEP 1: PRIMARY Server (mongo-1 / 10.0.1.10)

#### 1.1 System Preparation

```bash
# ============================================
# RUN ON: PRIMARY (mongo-1)
# ============================================

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y wget curl gnupg2 software-properties-common \
  apt-transport-https ca-certificates lsb-release

# Install NTP for time synchronization
sudo apt install -y ntp
sudo systemctl enable ntp
sudo systemctl start ntp

# Verify time sync
timedatectl status
# ✅ Expected: "System clock synchronized: yes"
```

#### 1.2 Configure Firewall

```bash
# ============================================
# RUN ON: PRIMARY (mongo-1)
# ============================================

# Allow MongoDB port from replica set members
sudo ufw allow from 10.0.1.10 to any port 27017  # Self
sudo ufw allow from 10.0.1.11 to any port 27017  # SECONDARY-1
sudo ufw allow from 10.0.1.12 to any port 27017  # SECONDARY-2

# Allow SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
sudo ufw status

# ✅ Expected output:
# To                         Action      From
# --                         ------      ----
# 27017                      ALLOW       10.0.1.10
# 27017                      ALLOW       10.0.1.11
# 27017                      ALLOW       10.0.1.12
# 22/tcp                     ALLOW       Anywhere
```

#### 1.3 Configure Hosts File

```bash
# ============================================
# RUN ON: PRIMARY (mongo-1)
# ============================================

sudo tee -a /etc/hosts <<EOF
10.0.1.10 mongo-1
10.0.1.11 mongo-2
10.0.1.12 mongo-3
EOF

# Test connectivity
ping -c 3 mongo-1  # Should succeed
ping -c 3 mongo-2  # Should succeed
ping -c 3 mongo-3  # Should succeed

# ✅ Expected: 0% packet loss for all
```

#### 1.4 Disable Transparent Huge Pages

```bash
# ============================================
# RUN ON: PRIMARY (mongo-1)
# ============================================

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

# Verify
cat /sys/kernel/mm/transparent_hugepage/enabled
# ✅ Expected: always madvise [never]
```

#### 1.5 Install MongoDB

```bash
# ============================================
# RUN ON: PRIMARY (mongo-1)
# ============================================

# Import MongoDB GPG key
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Add MongoDB repository (Ubuntu 22.04)
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update package list
sudo apt update

# Install MongoDB
sudo apt install -y mongodb-org

# Verify installation
mongod --version
# ✅ Expected: db version v7.0.x
```

#### 1.6 Create Data Directories

```bash
# ============================================
# RUN ON: PRIMARY (mongo-1)
# ============================================

# Create directories
sudo mkdir -p /data/mongodb
sudo mkdir -p /var/log/mongodb

# Set ownership
sudo chown -R mongodb:mongodb /data/mongodb
sudo chown -R mongodb:mongodb /var/log/mongodb

# Set permissions
sudo chmod 755 /data/mongodb
sudo chmod 755 /var/log/mongodb

# Verify
ls -ld /data/mongodb
# ✅ Expected: drwxr-xr-x 2 mongodb mongodb
```

#### 1.7 Generate Keyfile (ONLY on PRIMARY)

```bash
# ============================================
# RUN ON: PRIMARY (mongo-1) ONLY
# ============================================

# Generate keyfile for replica set authentication
openssl rand -base64 756 > /tmp/mongodb-keyfile

# Set permissions
chmod 400 /tmp/mongodb-keyfile

# Move to final location
sudo mv /tmp/mongodb-keyfile /etc/mongodb-keyfile
sudo chown mongodb:mongodb /etc/mongodb-keyfile
sudo chmod 400 /etc/mongodb-keyfile

# Verify
ls -l /etc/mongodb-keyfile
# ✅ Expected: -r-------- 1 mongodb mongodb 1024 ... /etc/mongodb-keyfile

# Display keyfile (you'll copy this to other servers)
cat /etc/mongodb-keyfile
# ⚠️ SAVE THIS OUTPUT - You'll need it for SECONDARY-1 and SECONDARY-2
```

#### 1.8 Configure mongod.conf

```bash
# ============================================
# RUN ON: PRIMARY (mongo-1)
# ============================================

sudo tee /etc/mongod.conf <<'EOF'
# MongoDB Configuration - PRIMARY (mongo-1)

storage:
  dbPath: /data/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4  # Adjust: 50% of RAM minus 1GB
      journalCompressor: snappy
    collectionConfig:
      blockCompressor: snappy

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
  logRotate: reopen
  verbosity: 0
  component:
    replication:
      verbosity: 1

net:
  port: 27017
  bindIp: 10.0.1.10,127.0.0.1  # PRIMARY IP
  maxIncomingConnections: 65536

processManagement:
  timeZoneInfo: /usr/share/zoneinfo
  fork: false

security:
  authorization: enabled
  keyFile: /etc/mongodb-keyfile

replication:
  replSetName: rs0
  oplogSizeMB: 10240  # 10GB

operationProfiling:
  mode: slowOp
  slowOpThresholdMs: 100
EOF

# Verify configuration
sudo cat /etc/mongod.conf
```

#### 1.9 Start MongoDB (Don't Initialize Yet)

```bash
# ============================================
# RUN ON: PRIMARY (mongo-1)
# ============================================

# Enable MongoDB service
sudo systemctl enable mongod

# Start MongoDB
sudo systemctl start mongod

# Check status
sudo systemctl status mongod
# ✅ Expected: active (running)

# Verify MongoDB is listening
sudo netstat -tulpn | grep 27017
# ✅ Expected: tcp 0 0 10.0.1.10:27017 0.0.0.0:* LISTEN

# Check logs
sudo tail -f /var/log/mongodb/mongod.log
# ✅ Expected: "Waiting for connections"
# Press Ctrl+C to exit
```

---

### 🟢 STEP 2: SECONDARY-1 Server (mongo-2 / 10.0.1.11)

#### 2.1 System Preparation

```bash
# ============================================
# RUN ON: SECONDARY-1 (mongo-2)
# ============================================

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y wget curl gnupg2 software-properties-common \
  apt-transport-https ca-certificates lsb-release

# Install NTP
sudo apt install -y ntp
sudo systemctl enable ntp
sudo systemctl start ntp

# Verify time sync
timedatectl status
# ✅ Expected: "System clock synchronized: yes"
```

#### 2.2 Configure Firewall

```bash
# ============================================
# RUN ON: SECONDARY-1 (mongo-2)
# ============================================

# Allow MongoDB port from replica set members
sudo ufw allow from 10.0.1.10 to any port 27017  # PRIMARY
sudo ufw allow from 10.0.1.11 to any port 27017  # Self
sudo ufw allow from 10.0.1.12 to any port 27017  # SECONDARY-2

# Allow SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

#### 2.3 Configure Hosts File

```bash
# ============================================
# RUN ON: SECONDARY-1 (mongo-2)
# ============================================

sudo tee -a /etc/hosts <<EOF
10.0.1.10 mongo-1
10.0.1.11 mongo-2
10.0.1.12 mongo-3
EOF

# Test connectivity
ping -c 3 mongo-1
ping -c 3 mongo-2
ping -c 3 mongo-3
```

#### 2.4 Disable Transparent Huge Pages

```bash
# ============================================
# RUN ON: SECONDARY-1 (mongo-2)
# ============================================

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

# Verify
cat /sys/kernel/mm/transparent_hugepage/enabled
# ✅ Expected: always madvise [never]
```

#### 2.5 Install MongoDB

```bash
# ============================================
# RUN ON: SECONDARY-1 (mongo-2)
# ============================================

# Import MongoDB GPG key
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update and install
sudo apt update
sudo apt install -y mongodb-org

# Verify
mongod --version
# ✅ Expected: db version v7.0.x
```

#### 2.6 Create Data Directories

```bash
# ============================================
# RUN ON: SECONDARY-1 (mongo-2)
# ============================================

sudo mkdir -p /data/mongodb
sudo mkdir -p /var/log/mongodb
sudo chown -R mongodb:mongodb /data/mongodb
sudo chown -R mongodb:mongodb /var/log/mongodb
sudo chmod 755 /data/mongodb
sudo chmod 755 /var/log/mongodb
```

#### 2.7 Copy Keyfile from PRIMARY

```bash
# ============================================
# RUN ON: SECONDARY-1 (mongo-2)
# ============================================

# Method 1: Copy from PRIMARY using SCP
# (Run this from mongo-2, or copy the keyfile content manually)
scp root@mongo-1:/etc/mongodb-keyfile /tmp/mongodb-keyfile

# OR Method 2: Create keyfile manually
# Copy the keyfile content from PRIMARY and paste it:
sudo nano /tmp/mongodb-keyfile
# Paste the keyfile content from mongo-1
# Save and exit (Ctrl+X, Y, Enter)

# Set permissions
sudo chmod 400 /tmp/mongodb-keyfile
sudo mv /tmp/mongodb-keyfile /etc/mongodb-keyfile
sudo chown mongodb:mongodb /etc/mongodb-keyfile
sudo chmod 400 /etc/mongodb-keyfile

# Verify
ls -l /etc/mongodb-keyfile
# ✅ Expected: -r-------- 1 mongodb mongodb

# Verify keyfile matches PRIMARY
md5sum /etc/mongodb-keyfile
# Compare with: ssh root@mongo-1 "md5sum /etc/mongodb-keyfile"
# ✅ MD5 hashes MUST match
```

#### 2.8 Configure mongod.conf

```bash
# ============================================
# RUN ON: SECONDARY-1 (mongo-2)
# ============================================

sudo tee /etc/mongod.conf <<'EOF'
# MongoDB Configuration - SECONDARY-1 (mongo-2)

storage:
  dbPath: /data/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4
      journalCompressor: snappy
    collectionConfig:
      blockCompressor: snappy

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
  logRotate: reopen
  verbosity: 0
  component:
    replication:
      verbosity: 1

net:
  port: 27017
  bindIp: 10.0.1.11,127.0.0.1  # SECONDARY-1 IP
  maxIncomingConnections: 65536

processManagement:
  timeZoneInfo: /usr/share/zoneinfo
  fork: false

security:
  authorization: enabled
  keyFile: /etc/mongodb-keyfile

replication:
  replSetName: rs0
  oplogSizeMB: 10240

operationProfiling:
  mode: slowOp
  slowOpThresholdMs: 100
EOF
```

#### 2.9 Start MongoDB

```bash
# ============================================
# RUN ON: SECONDARY-1 (mongo-2)
# ============================================

sudo systemctl enable mongod
sudo systemctl start mongod
sudo systemctl status mongod
# ✅ Expected: active (running)

# Verify listening
sudo netstat -tulpn | grep 27017
# ✅ Expected: tcp 0 0 10.0.1.11:27017
```

---

### 🟡 STEP 3: SECONDARY-2 Server (mongo-3 / 10.0.1.12)

#### 3.1 System Preparation

```bash
# ============================================
# RUN ON: SECONDARY-2 (mongo-3)
# ============================================

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y wget curl gnupg2 software-properties-common \
  apt-transport-https ca-certificates lsb-release

# Install NTP
sudo apt install -y ntp
sudo systemctl enable ntp
sudo systemctl start ntp

# Verify time sync
timedatectl status
# ✅ Expected: "System clock synchronized: yes"
```

#### 3.2 Configure Firewall

```bash
# ============================================
# RUN ON: SECONDARY-2 (mongo-3)
# ============================================

sudo ufw allow from 10.0.1.10 to any port 27017  # PRIMARY
sudo ufw allow from 10.0.1.11 to any port 27017  # SECONDARY-1
sudo ufw allow from 10.0.1.12 to any port 27017  # Self
sudo ufw allow 22/tcp
sudo ufw enable
sudo ufw status
```

#### 3.3 Configure Hosts File

```bash
# ============================================
# RUN ON: SECONDARY-2 (mongo-3)
# ============================================

sudo tee -a /etc/hosts <<EOF
10.0.1.10 mongo-1
10.0.1.11 mongo-2
10.0.1.12 mongo-3
EOF

ping -c 3 mongo-1
ping -c 3 mongo-2
ping -c 3 mongo-3
```

#### 3.4 Disable Transparent Huge Pages

```bash
# ============================================
# RUN ON: SECONDARY-2 (mongo-3)
# ============================================

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

cat /sys/kernel/mm/transparent_hugepage/enabled
# ✅ Expected: always madvise [never]
```

#### 3.5 Install MongoDB

```bash
# ============================================
# RUN ON: SECONDARY-2 (mongo-3)
# ============================================

curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

sudo apt update
sudo apt install -y mongodb-org

mongod --version
# ✅ Expected: db version v7.0.x
```

#### 3.6 Create Data Directories

```bash
# ============================================
# RUN ON: SECONDARY-2 (mongo-3)
# ============================================

sudo mkdir -p /data/mongodb
sudo mkdir -p /var/log/mongodb
sudo chown -R mongodb:mongodb /data/mongodb
sudo chown -R mongodb:mongodb /var/log/mongodb
sudo chmod 755 /data/mongodb
sudo chmod 755 /var/log/mongodb
```

#### 3.7 Copy Keyfile from PRIMARY

```bash
# ============================================
# RUN ON: SECONDARY-2 (mongo-3)
# ============================================

# Copy from PRIMARY
scp root@mongo-1:/etc/mongodb-keyfile /tmp/mongodb-keyfile

# OR create manually and paste content
# sudo nano /tmp/mongodb-keyfile

# Set permissions
sudo chmod 400 /tmp/mongodb-keyfile
sudo mv /tmp/mongodb-keyfile /etc/mongodb-keyfile
sudo chown mongodb:mongodb /etc/mongodb-keyfile
sudo chmod 400 /etc/mongodb-keyfile

# Verify
ls -l /etc/mongodb-keyfile
md5sum /etc/mongodb-keyfile
# ✅ MD5 must match PRIMARY
```

#### 3.8 Configure mongod.conf

```bash
# ============================================
# RUN ON: SECONDARY-2 (mongo-3)
# ============================================

sudo tee /etc/mongod.conf <<'EOF'
# MongoDB Configuration - SECONDARY-2 (mongo-3)

storage:
  dbPath: /data/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4
      journalCompressor: snappy
    collectionConfig:
      blockCompressor: snappy

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
  logRotate: reopen
  verbosity: 0
  component:
    replication:
      verbosity: 1

net:
  port: 27017
  bindIp: 10.0.1.12,127.0.0.1  # SECONDARY-2 IP
  maxIncomingConnections: 65536

processManagement:
  timeZoneInfo: /usr/share/zoneinfo
  fork: false

security:
  authorization: enabled
  keyFile: /etc/mongodb-keyfile

replication:
  replSetName: rs0
  oplogSizeMB: 10240

operationProfiling:
  mode: slowOp
  slowOpThresholdMs: 100
EOF
```

#### 3.9 Start MongoDB

```bash
# ============================================
# RUN ON: SECONDARY-2 (mongo-3)
# ============================================

sudo systemctl enable mongod
sudo systemctl start mongod
sudo systemctl status mongod
# ✅ Expected: active (running)

sudo netstat -tulpn | grep 27017
# ✅ Expected: tcp 0 0 10.0.1.12:27017
```

---

## Replica Set Initialization

### 🔴 STEP 4: Initialize Replica Set (PRIMARY ONLY)

```bash
# ============================================
# RUN ON: PRIMARY (mongo-1) ONLY
# ============================================

# Connect to MongoDB (no authentication yet)
mongosh --host 10.0.1.10 --port 27017
```

```javascript
// ============================================
// RUN IN MONGOSH ON PRIMARY (mongo-1)
// ============================================

// Initialize replica set
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo-1:27017", priority: 2 },  // PRIMARY (higher priority)
    { _id: 1, host: "mongo-2:27017", priority: 1 },  // SECONDARY-1
    { _id: 2, host: "mongo-3:27017", priority: 1 }   // SECONDARY-2
  ]
})

// ✅ Expected output:
// { ok: 1 }

// Wait 10-15 seconds for election
// Your prompt will change to: rs0 [direct: primary]

// Check replica set status
rs.status()

// ✅ Expected output:
// members[0]: { name: "mongo-1:27017", stateStr: "PRIMARY", health: 1 }
// members[1]: { name: "mongo-2:27017", stateStr: "SECONDARY", health: 1 }
// members[2]: { name: "mongo-3:27017", stateStr: "SECONDARY", health: 1 }
```

### 🔴 STEP 5: Create Admin User (PRIMARY ONLY)

```javascript
// ============================================
// RUN IN MONGOSH ON PRIMARY (mongo-1)
// ============================================

// Switch to admin database
use admin

// Create root user
db.createUser({
  user: "admin",
  pwd: "AdminSecurePassword123!",  // ⚠️ CHANGE THIS IN PRODUCTION
  roles: [
    { role: "root", db: "admin" }
  ]
})

// ✅ Expected output:
// { ok: 1 }

// Exit mongosh
exit
```

### 🔴 STEP 6: Reconnect with Authentication (PRIMARY)

```bash
# ============================================
# RUN ON: PRIMARY (mongo-1)
# ============================================

# Reconnect with authentication
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/admin?replicaSet=rs0"
```

```javascript
// ============================================
// RUN IN MONGOSH ON PRIMARY
// ============================================

// Verify authentication
db.runCommand({ connectionStatus: 1 })

// ✅ Expected: authenticatedUsers: [ { user: 'admin', db: 'admin' } ]

// Check replica set status
rs.status()

// ✅ All members should be healthy

// Check replication lag
rs.printSecondaryReplicationInfo()

// ✅ Expected: Both secondaries < 1 second behind
```

### 🔴 STEP 7: Create Application Users (PRIMARY ONLY)

```javascript
// ============================================
// RUN IN MONGOSH ON PRIMARY (mongo-1)
// ============================================

// Create application database
use mydb

// Create application user (read/write)
db.createUser({
  user: "appuser",
  pwd: "AppSecurePassword123!",  // ⚠️ CHANGE THIS
  roles: [
    { role: "readWrite", db: "mydb" }
  ]
})

// ✅ Expected: { ok: 1 }

// Create read-only user (for analytics)
db.createUser({
  user: "readonly",
  pwd: "ReadOnlyPassword123!",  // ⚠️ CHANGE THIS
  roles: [
    { role: "read", db: "mydb" }
  ]
})

// ✅ Expected: { ok: 1 }

// Verify users
db.getUsers()

// Exit
exit
```

---

## Code-Level Implementation

### Python Application Example

#### 1. Install Dependencies

```bash
# On your application server (not MongoDB servers)
pip install pymongo==4.6.0
```

#### 2. Create Database Connection Module

```python
# File: database.py
# ============================================
# MongoDB Connection Module
# ============================================

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from pymongo.write_concern import WriteConcern
from pymongo.read_preference import ReadPreference
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection string for replica set
MONGO_URI = "mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority&wtimeout=5000&readPreference=primary&maxPoolSize=100&minPoolSize=10&retryWrites=true"

class MongoDBConnection:
    """MongoDB Replica Set Connection Manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
    
    def connect(self):
        """Establish connection to MongoDB replica set"""
        try:
            self.client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database
            self.db = self.client.mydb
            
            logger.info("✅ Connected to MongoDB replica set")
            logger.info(f"✅ Connected to: {self.client.address}")
            
            # Check replica set status
            status = self.client.admin.command('replSetGetStatus')
            primary = [m for m in status['members'] if m['stateStr'] == 'PRIMARY'][0]
            logger.info(f"✅ PRIMARY: {primary['name']}")
            
            return self.db
            
        except ConnectionFailure as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB connection closed")
    
    def insert_document(self, collection_name, document):
        """Insert document with majority write concern"""
        try:
            collection = self.db[collection_name]
            
            # Insert with majority write concern
            result = collection.insert_one(
                document,
                write_concern=WriteConcern(w="majority", wtimeout=5000)
            )
            
            logger.info(f"✅ Inserted document ID: {result.inserted_id}")
            return result.inserted_id
            
        except OperationFailure as e:
            logger.error(f"❌ Write failed: {e}")
            raise
    
    def find_documents(self, collection_name, query=None, read_from_secondary=False):
        """Find documents with configurable read preference"""
        try:
            collection = self.db[collection_name]
            
            # Configure read preference
            if read_from_secondary:
                collection = collection.with_options(
                    read_preference=ReadPreference.SECONDARY_PREFERRED
                )
            
            documents = list(collection.find(query or {}))
            logger.info(f"✅ Found {len(documents)} documents")
            return documents
            
        except OperationFailure as e:
            logger.error(f"❌ Read failed: {e}")
            raise
    
    def update_document(self, collection_name, query, update):
        """Update document with majority write concern"""
        try:
            collection = self.db[collection_name]
            
            result = collection.update_one(
                query,
                update,
                write_concern=WriteConcern(w="majority", wtimeout=5000)
            )
            
            logger.info(f"✅ Updated {result.modified_count} document(s)")
            return result.modified_count
            
        except OperationFailure as e:
            logger.error(f"❌ Update failed: {e}")
            raise
    
    def delete_document(self, collection_name, query):
        """Delete document with majority write concern"""
        try:
            collection = self.db[collection_name]
            
            result = collection.delete_one(
                query,
                write_concern=WriteConcern(w="majority", wtimeout=5000)
            )
            
            logger.info(f"✅ Deleted {result.deleted_count} document(s)")
            return result.deleted_count
            
        except OperationFailure as e:
            logger.error(f"❌ Delete failed: {e}")
            raise

# Usage example
if __name__ == "__main__":
    # Create connection
    mongo = MongoDBConnection()
    db = mongo.connect()
    
    # Insert document
    user_id = mongo.insert_document("users", {
        "name": "John Doe",
        "email": "john@example.com",
        "created_at": datetime.utcnow()
    })
    
    # Find documents
    users = mongo.find_documents("users", {"email": "john@example.com"})
    print(f"Found user: {users[0]}")
    
    # Update document
    mongo.update_document(
        "users",
        {"_id": user_id},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Close connection
    mongo.close()
```

#### 3. Create Application

```python
# File: app.py
# ============================================
# Main Application
# ============================================

from database import MongoDBConnection
from datetime import datetime
import time

def main():
    # Initialize database connection
    mongo = MongoDBConnection()
    db = mongo.connect()
    
    print("\n" + "="*60)
    print("MongoDB Replica Set - Application Demo")
    print("="*60 + "\n")
    
    # Test 1: Insert documents
    print("📝 Test 1: Inserting documents...")
    for i in range(5):
        user_id = mongo.insert_document("users", {
            "name": f"User {i+1}",
            "email": f"user{i+1}@example.com",
            "age": 20 + i,
            "created_at": datetime.utcnow()
        })
        print(f"   ✅ Inserted user {i+1}: {user_id}")
    
    # Test 2: Read from PRIMARY
    print("\n📖 Test 2: Reading from PRIMARY...")
    users = mongo.find_documents("users", read_from_secondary=False)
    print(f"   ✅ Found {len(users)} users from PRIMARY")
    
    # Test 3: Read from SECONDARY
    print("\n📖 Test 3: Reading from SECONDARY (if available)...")
    users = mongo.find_documents("users", read_from_secondary=True)
    print(f"   ✅ Found {len(users)} users from SECONDARY")
    
    # Test 4: Update document
    print("\n✏️  Test 4: Updating document...")
    count = mongo.update_document(
        "users",
        {"email": "user1@example.com"},
        {"$set": {"status": "active", "updated_at": datetime.utcnow()}}
    )
    print(f"   ✅ Updated {count} document(s)")
    
    # Test 5: Delete document
    print("\n🗑️  Test 5: Deleting document...")
    count = mongo.delete_document("users", {"email": "user5@example.com"})
    print(f"   ✅ Deleted {count} document(s)")
    
    # Test 6: Verify final count
    print("\n📊 Test 6: Final count...")
    users = mongo.find_documents("users")
    print(f"   ✅ Total users: {len(users)}")
    
    # Close connection
    mongo.close()
    
    print("\n" + "="*60)
    print("✅ All tests completed successfully!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
```

#### 4. Run Application

```bash
# Run the application
python app.py

# ✅ Expected output:
# ============================================================
# MongoDB Replica Set - Application Demo
# ============================================================
# 
# ✅ Connected to MongoDB replica set
# ✅ Connected to: ('mongo-1', 27017)
# ✅ PRIMARY: mongo-1:27017
# 
# 📝 Test 1: Inserting documents...
#    ✅ Inserted user 1: 6589...
#    ✅ Inserted user 2: 6589...
#    ...
# 
# ✅ All tests completed successfully!
```

### Node.js Application Example

```javascript
// File: database.js
// ============================================
// MongoDB Connection Module (Node.js)
// ============================================

const { MongoClient } = require('mongodb');

const MONGO_URI = "mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority&wtimeout=5000&readPreference=primary&maxPoolSize=100&minPoolSize=10&retryWrites=true";

class MongoDBConnection {
  constructor() {
    this.client = null;
    this.db = null;
  }

  async connect() {
    try {
      this.client = new MongoClient(MONGO_URI, {
        serverSelectionTimeoutMS: 5000,
        connectTimeoutMS: 10000,
        socketTimeoutMS: 10000
      });

      await this.client.connect();
      console.log("✅ Connected to MongoDB replica set");

      this.db = this.client.db('mydb');

      // Check replica set status
      const admin = this.client.db('admin');
      const status = await admin.command({ replSetGetStatus: 1 });
      const primary = status.members.find(m => m.stateStr === 'PRIMARY');
      console.log(`✅ PRIMARY: ${primary.name}`);

      return this.db;
    } catch (error) {
      console.error("❌ Failed to connect:", error);
      throw error;
    }
  }

  async insertDocument(collectionName, document) {
    try {
      const collection = this.db.collection(collectionName);
      const result = await collection.insertOne(document, {
        writeConcern: { w: "majority", wtimeout: 5000 }
      });
      console.log(`✅ Inserted document ID: ${result.insertedId}`);
      return result.insertedId;
    } catch (error) {
      console.error("❌ Insert failed:", error);
      throw error;
    }
  }

  async findDocuments(collectionName, query = {}) {
    try {
      const collection = this.db.collection(collectionName);
      const documents = await collection.find(query).toArray();
      console.log(`✅ Found ${documents.length} documents`);
      return documents;
    } catch (error) {
      console.error("❌ Find failed:", error);
      throw error;
    }
  }

  async close() {
    if (this.client) {
      await this.client.close();
      console.log("✅ MongoDB connection closed");
    }
  }
}

module.exports = MongoDBConnection;
```

```javascript
// File: app.js
// ============================================
// Main Application (Node.js)
// ============================================

const MongoDBConnection = require('./database');

async function main() {
  const mongo = new MongoDBConnection();
  
  try {
    await mongo.connect();

    console.log("\n" + "=".repeat(60));
    console.log("MongoDB Replica Set - Node.js Demo");
    console.log("=".repeat(60) + "\n");

    // Insert documents
    console.log("📝 Inserting documents...");
    for (let i = 0; i < 5; i++) {
      await mongo.insertDocument("users", {
        name: `User ${i + 1}`,
        email: `user${i + 1}@example.com`,
        createdAt: new Date()
      });
    }

    // Read documents
    console.log("\n📖 Reading documents...");
    const users = await mongo.findDocuments("users");
    console.log(`   Total users: ${users.length}`);

    console.log("\n✅ All tests completed!");

  } catch (error) {
    console.error("❌ Error:", error);
  } finally {
    await mongo.close();
  }
}

main();
```

---

## Complete Testing Guide

### Test 1: Verify Replica Set Status

```bash
# ============================================
# RUN ON: PRIMARY (mongo-1)
# ============================================

mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/admin?replicaSet=rs0"
```

```javascript
// Check replica set status
rs.status()

// ✅ Verify:
// - members[0].stateStr: "PRIMARY" (mongo-1)
// - members[1].stateStr: "SECONDARY" (mongo-2)
// - members[2].stateStr: "SECONDARY" (mongo-3)
// - All members health: 1

// Check configuration
rs.conf()

// ✅ Verify:
// - members[0].priority: 2 (mongo-1)
// - members[1].priority: 1 (mongo-2)
// - members[2].priority: 1 (mongo-3)
```

### Test 2: Verify Replication

```javascript
// ============================================
// RUN IN MONGOSH ON PRIMARY
// ============================================

// Insert test document
use testdb
db.test.insertOne(
  { message: "Test replication", timestamp: new Date() },
  { writeConcern: { w: "majority", wtimeout: 5000 } }
)

// ✅ Expected: acknowledged: true

// Check replication lag
rs.printSecondaryReplicationInfo()

// ✅ Expected output:
// source: mongo-2:27017
//   syncedTo: ... (0 secs behind)
// source: mongo-3:27017
//   syncedTo: ... (0 secs behind)
```

### Test 3: Verify Read from SECONDARY

```bash
# ============================================
# RUN ON: SECONDARY-1 (mongo-2)
# ============================================

mongosh "mongodb://admin:AdminSecurePassword123!@mongo-2:27017/admin"
```

```javascript
// Allow reads on SECONDARY
rs.secondaryOk()

// Read test document
use testdb
db.test.find()

// ✅ Expected: Document found (replicated from PRIMARY)
```

### Test 4: Failover Test

```javascript
// ============================================
// RUN IN MONGOSH ON PRIMARY (mongo-1)
// ============================================

// Step down PRIMARY (simulate failure)
rs.stepDown(60)

// ✅ Expected: Connection will drop, reconnect

// Wait 10-15 seconds
// Reconnect
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/admin?replicaSet=rs0"

// Check new PRIMARY
rs.status()

// ✅ Expected: mongo-2 or mongo-3 is now PRIMARY

// Insert document to new PRIMARY
use testdb
db.test.insertOne({ failover_test: true, timestamp: new Date() })

// ✅ Expected: Success

// Wait 60 seconds for mongo-1 to rejoin
// Check status again
rs.status()

// ✅ Expected: mongo-1 is now SECONDARY, all 3 members healthy
```

### Test 5: Application Connection Test

```bash
# ============================================
# RUN ON: Application Server
# ============================================

# Test Python application
python app.py

# ✅ Expected output:
# ✅ Connected to MongoDB replica set
# ✅ Connected to: ('mongo-1', 27017)
# ✅ PRIMARY: mongo-1:27017
# 📝 Test 1: Inserting documents...
#    ✅ Inserted user 1: ...
# ...
# ✅ All tests completed successfully!
```

### Test 6: Performance Test

```javascript
// ============================================
// RUN IN MONGOSH ON PRIMARY
// ============================================

use benchmark

// Insert 10,000 documents
var startTime = new Date();
for (var i = 0; i < 10000; i++) {
  db.test.insertOne(
    { index: i, data: "x".repeat(100), timestamp: new Date() },
    { writeConcern: { w: "majority" } }
  );
}
var endTime = new Date();

print("Time taken: " + (endTime - startTime) / 1000 + " seconds");
print("Writes per second: " + (10000 / ((endTime - startTime) / 1000)));

// ✅ Expected: 500-1000 writes/second (depends on hardware)
```

### Test 7: Connection Pool Test

```javascript
// ============================================
// RUN IN MONGOSH ON PRIMARY
// ============================================

// Check connection pool usage
db.serverStatus().connections

// ✅ Expected output:
// {
//   current: 10,        // Current connections
//   available: 65526,   // Available connections
//   totalCreated: 15    // Total created since start
// }

// ✅ Verify: current < maxIncomingConnections (65536)
```

### Test 8: Write Concern Test

```javascript
// ============================================
// RUN IN MONGOSH ON PRIMARY
// ============================================

use testdb

// Test 1: w: 1 (fast, risky)
var start = new Date();
db.test_w1.insertOne({ test: "w1" }, { writeConcern: { w: 1 } });
var time_w1 = new Date() - start;
print("w:1 time: " + time_w1 + "ms");

// Test 2: w: "majority" (balanced, recommended)
start = new Date();
db.test_wmajority.insertOne({ test: "wmajority" }, { writeConcern: { w: "majority" } });
var time_wmajority = new Date() - start;
print("w:majority time: " + time_wmajority + "ms");

// Test 3: w: 3 (safest, slowest)
start = new Date();
db.test_w3.insertOne({ test: "w3" }, { writeConcern: { w: 3 } });
var time_w3 = new Date() - start;
print("w:3 time: " + time_w3 + "ms");

// ✅ Expected:
// w:1 time: 1-5ms
// w:majority time: 10-50ms
// w:3 time: 20-100ms
```

---

## Troubleshooting

### Issue 1: "no primary found in replica set"

```bash
# Check status on each server
mongosh --host mongo-1 --port 27017 --eval "rs.status()"
mongosh --host mongo-2 --port 27017 --eval "rs.status()"
mongosh --host mongo-3 --port 27017 --eval "rs.status()"

# Solution: Wait 10-15 seconds for election
# If still no PRIMARY, check logs:
sudo tail -f /var/log/mongodb/mongod.log
```

### Issue 2: "Authentication failed"

```bash
# Verify keyfile is identical on all servers
md5sum /etc/mongodb-keyfile  # Run on all 3 servers

# Verify keyfile permissions
ls -l /etc/mongodb-keyfile
# ✅ Must be: -r-------- 1 mongodb mongodb

# Verify user exists
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "db.getUsers()"
```

### Issue 3: Replication lag

```javascript
// Check lag
rs.printSecondaryReplicationInfo()

// Check oplog size
use local
db.oplog.rs.stats()

// Solution: Resize oplog if too small
use admin
db.adminCommand({ replSetResizeOplog: 1, size: 20480 })  // 20GB
```

### Issue 4: Connection refused

```bash
# Check MongoDB is running
sudo systemctl status mongod

# Check firewall
sudo ufw status

# Check listening port
sudo netstat -tulpn | grep 27017

# Test connectivity from other servers
telnet mongo-1 27017
telnet mongo-2 27017
telnet mongo-3 27017
```

---

## Production Checklist

### Pre-Deployment

- [ ] All 3 servers have MongoDB installed
- [ ] Keyfile is identical on all servers (verify with md5sum)
- [ ] Firewall rules configured on all servers
- [ ] NTP synchronized on all servers
- [ ] THP disabled on all servers
- [ ] mongod.conf configured with correct IPs
- [ ] MongoDB service started on all servers

### Post-Initialization

- [ ] Replica set initialized (rs.status() shows 1 PRIMARY, 2 SECONDARYs)
- [ ] Admin user created
- [ ] Application users created
- [ ] Replication lag < 1 second
- [ ] Failover tested successfully
- [ ] Application can connect and perform CRUD operations
- [ ] Connection pool configured (maxPoolSize, minPoolSize)
- [ ] Write concern set to "majority"
- [ ] Monitoring configured
- [ ] Backups configured

---

## Summary

You now have a complete, production-ready MongoDB replica set with:

✅ **3 servers**: PRIMARY (mongo-1), SECONDARY-1 (mongo-2), SECONDARY-2 (mongo-3)  
✅ **High availability**: Survives 1 node failure  
✅ **Data durability**: w: "majority" write concern  
✅ **Security**: Authentication with keyfile  
✅ **Code examples**: Python and Node.js  
✅ **Comprehensive tests**: Replication, failover, performance  

**Connection String for Applications:**
```
mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority&wtimeout=5000&readPreference=primary&maxPoolSize=100&minPoolSize=10&retryWrites=true
```

**Next Steps:**
1. Run all tests to verify setup
2. Deploy your application
3. Set up monitoring (Prometheus + Grafana)
4. Configure automated backups
5. Document your connection strings
