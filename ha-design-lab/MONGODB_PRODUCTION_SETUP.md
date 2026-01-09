# MongoDB Community Edition - Production-Ready Replica Set Setup

> **Complete step-by-step guide for deploying a 3-node MongoDB replica set with authentication, TLS, monitoring, and backups**

---

## Table of Contents
1. [Connection String Examples](#connection-string-examples)
2. [Infrastructure Requirements](#infrastructure-requirements)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [Security Hardening](#security-hardening)
5. [Monitoring Setup](#monitoring-setup)
6. [Backup Configuration](#backup-configuration)
7. [Application Integration](#application-integration)
8. [Testing & Validation](#testing--validation)
9. [Maintenance Procedures](#maintenance-procedures)

---

## Connection String Examples

### Basic Connection String (Development)
```
mongodb://localhost:27017/mydb
```

### Production Connection String (Recommended)
```
mongodb://appuser:SecurePassword123!@mongo-1.example.com:27017,mongo-2.example.com:27017,mongo-3.example.com:27017/mydb?replicaSet=rs0&authSource=admin&retryWrites=true&w=majority&wtimeout=5000&readPreference=primary&maxPoolSize=100&minPoolSize=10
```

### Connection String Breakdown

```
mongodb://                                    # Protocol
appuser:SecurePassword123!@                   # Username:Password
mongo-1.example.com:27017,                    # PRIMARY or SECONDARY 1
mongo-2.example.com:27017,                    # SECONDARY 2
mongo-3.example.com:27017                     # SECONDARY 3
/mydb                                         # Database name
?replicaSet=rs0                               # Replica set name (REQUIRED)
&authSource=admin                             # Authentication database
&retryWrites=true                             # Auto-retry failed writes
&w=majority                                   # Write concern (data safety)
&wtimeout=5000                                # Write timeout (5 seconds)
&readPreference=primary                       # Read from PRIMARY only
&maxPoolSize=100                              # Max connections per app instance
&minPoolSize=10                               # Min connections to keep alive
```

### Connection String Variations

#### 1. Write-Heavy Application (Financial, E-commerce)
```
mongodb://appuser:password@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=admin&w=majority&wtimeout=5000&readPreference=primary&journal=true&retryWrites=true
```
- **w=majority**: Ensures data survives failover
- **journal=true**: Waits for journal commit (durability)
- **readPreference=primary**: Strong consistency

#### 2. Read-Heavy Application (Analytics, Reporting)
```
mongodb://appuser:password@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=admin&w=majority&readPreference=secondaryPreferred&maxStalenessSeconds=90&maxPoolSize=200
```
- **readPreference=secondaryPreferred**: Offload reads to secondaries
- **maxStalenessSeconds=90**: Limit stale reads to 90 seconds
- **maxPoolSize=200**: Higher pool for read scaling

#### 3. Multi-Region Application (Low Latency)
```
mongodb://appuser:password@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=admin&w=majority&readPreference=nearest&maxStalenessSeconds=120&localThresholdMS=15
```
- **readPreference=nearest**: Read from closest member
- **localThresholdMS=15**: Consider members within 15ms as "nearest"

#### 4. With TLS/SSL (Production Recommended)
```
mongodb://appuser:password@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=admin&tls=true&tlsCAFile=/path/to/ca.pem&tlsCertificateKeyFile=/path/to/client.pem&w=majority
```
- **tls=true**: Enable TLS encryption
- **tlsCAFile**: Certificate Authority file
- **tlsCertificateKeyFile**: Client certificate

#### 5. Connection String for Different Languages

**Python (PyMongo)**
```python
from pymongo import MongoClient

# Basic
client = MongoClient("mongodb://appuser:password@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=admin")

# With all options
client = MongoClient(
    "mongodb://mongo-1:27017,mongo-2:27017,mongo-3:27017/",
    username="appuser",
    password="password",
    authSource="admin",
    replicaSet="rs0",
    w="majority",
    wtimeout=5000,
    readPreference="primary",
    maxPoolSize=100,
    minPoolSize=10,
    retryWrites=True
)
```

**Node.js (MongoDB Driver)**
```javascript
const { MongoClient } = require('mongodb');

const uri = "mongodb://appuser:password@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=admin&w=majority";

const client = new MongoClient(uri, {
  maxPoolSize: 100,
  minPoolSize: 10,
  retryWrites: true,
  readPreference: 'primary'
});

await client.connect();
```

**Java (MongoDB Driver)**
```java
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoClient;
import com.mongodb.ConnectionString;

ConnectionString connString = new ConnectionString(
    "mongodb://appuser:password@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=admin&w=majority"
);

MongoClient mongoClient = MongoClients.create(connString);
```

**Go (mongo-go-driver)**
```go
import (
    "context"
    "go.mongodb.org/mongo-driver/mongo"
    "go.mongodb.org/mongo-driver/mongo/options"
)

uri := "mongodb://appuser:password@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=admin&w=majority"

client, err := mongo.Connect(context.TODO(), options.Client().ApplyURI(uri))
```

---

## Infrastructure Requirements

### Minimum Production Requirements

| Component | Specification | Reason |
|-----------|--------------|--------|
| **Servers** | 3 separate physical/virtual machines | Survive hardware failures |
| **CPU** | 4 cores per server | Handle concurrent operations |
| **RAM** | 8GB per server (16GB recommended) | WiredTiger cache + OS |
| **Disk** | 100GB SSD (NVMe preferred) | Fast I/O for oplog + data |
| **Network** | 1 Gbps between members | Low replication lag |
| **OS** | Ubuntu 22.04 LTS / RHEL 8+ | Long-term support |
| **MongoDB** | Community Edition 7.0+ | Latest stable version |

### Server Hostnames/IPs

For this guide, we'll use:
- **mongo-1**: 10.0.1.10 (will become PRIMARY)
- **mongo-2**: 10.0.1.11 (SECONDARY)
- **mongo-3**: 10.0.1.12 (SECONDARY)

---

## Step-by-Step Setup

### Phase 1: Server Preparation (All 3 Servers)

#### Step 1.1: Update System and Install Dependencies

```bash
# Run on mongo-1, mongo-2, mongo-3

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y wget curl gnupg2 software-properties-common apt-transport-https ca-certificates lsb-release

# Install NTP for time synchronization (CRITICAL for replica sets)
sudo apt install -y ntp
sudo systemctl enable ntp
sudo systemctl start ntp

# Verify time sync
timedatectl status
# Should show: "System clock synchronized: yes"
```

#### Step 1.2: Configure Firewall

```bash
# Allow MongoDB port (27017) only from replica set members
sudo ufw allow from 10.0.1.10 to any port 27017
sudo ufw allow from 10.0.1.11 to any port 27017
sudo ufw allow from 10.0.1.12 to any port 27017

# Allow SSH (if not already)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

#### Step 1.3: Configure /etc/hosts (for hostname resolution)

```bash
# Add to /etc/hosts on all 3 servers
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

#### Step 1.4: Disable Transparent Huge Pages (THP)

```bash
# MongoDB recommends disabling THP for better performance
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
# Should show: always madvise [never]
```

#### Step 1.5: Set System Limits

```bash
# Increase file descriptor limits for MongoDB
sudo tee -a /etc/security/limits.conf <<EOF
mongodb soft nofile 64000
mongodb hard nofile 64000
mongodb soft nproc 64000
mongodb hard nproc 64000
EOF

# Apply limits
sudo sysctl -w fs.file-max=64000
```

---

### Phase 2: MongoDB Installation (All 3 Servers)

#### Step 2.1: Import MongoDB GPG Key

```bash
# Import MongoDB 7.0 GPG key
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Verify key
gpg --show-keys /usr/share/keyrings/mongodb-server-7.0.gpg
```

#### Step 2.2: Add MongoDB Repository

```bash
# For Ubuntu 22.04
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update package list
sudo apt update
```

#### Step 2.3: Install MongoDB

```bash
# Install MongoDB Community Edition
sudo apt install -y mongodb-org

# Pin version to prevent accidental upgrades
echo "mongodb-org hold" | sudo dpkg --set-selections
echo "mongodb-org-database hold" | sudo dpkg --set-selections
echo "mongodb-org-server hold" | sudo dpkg --set-selections
echo "mongodb-mongosh hold" | sudo dpkg --set-selections
echo "mongodb-org-mongos hold" | sudo dpkg --set-selections
echo "mongodb-org-tools hold" | sudo dpkg --set-selections

# Verify installation
mongod --version
# Should show: db version v7.0.x
```

#### Step 2.4: Create Data and Log Directories

```bash
# Create directories
sudo mkdir -p /data/mongodb
sudo mkdir -p /var/log/mongodb

# Set ownership
sudo chown -R mongodb:mongodb /data/mongodb
sudo chown -R mongodb:mongodb /var/log/mongodb

# Set permissions
sudo chmod 755 /data/mongodb
sudo chmod 755 /var/log/mongodb
```

---

### Phase 3: Replica Set Configuration

#### Step 3.1: Generate Keyfile for Inter-Member Authentication

```bash
# Run ONLY on mongo-1
openssl rand -base64 756 > /tmp/mongodb-keyfile

# Set permissions
chmod 400 /tmp/mongodb-keyfile

# Copy to other members
scp /tmp/mongodb-keyfile mongo-2:/tmp/mongodb-keyfile
scp /tmp/mongodb-keyfile mongo-3:/tmp/mongodb-keyfile

# On ALL servers (mongo-1, mongo-2, mongo-3)
sudo mv /tmp/mongodb-keyfile /etc/mongodb-keyfile
sudo chown mongodb:mongodb /etc/mongodb-keyfile
sudo chmod 400 /etc/mongodb-keyfile

# Verify permissions
ls -l /etc/mongodb-keyfile
# Should show: -r-------- 1 mongodb mongodb
```

#### Step 3.2: Configure mongod.conf (All 3 Servers)

**On mongo-1 (10.0.1.10):**

```bash
sudo tee /etc/mongod.conf <<'EOF'
# mongod.conf - MongoDB Configuration File

# Storage settings
storage:
  dbPath: /data/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4  # 50% of RAM minus 1GB (for 8GB RAM server)
      journalCompressor: snappy
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true

# Logging
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
  logRotate: reopen
  verbosity: 0
  component:
    replication:
      verbosity: 1

# Network settings
net:
  port: 27017
  bindIp: 10.0.1.10,127.0.0.1  # Listen on private IP + localhost
  maxIncomingConnections: 65536
  compression:
    compressors: snappy,zstd

# Process management
processManagement:
  timeZoneInfo: /usr/share/zoneinfo
  fork: false  # systemd manages the process

# Security
security:
  authorization: enabled
  keyFile: /etc/mongodb-keyfile

# Replication
replication:
  replSetName: rs0
  oplogSizeMB: 10240  # 10GB oplog (adjust based on write volume)

# Operation profiling (optional, for performance monitoring)
operationProfiling:
  mode: slowOp
  slowOpThresholdMs: 100
EOF
```

**On mongo-2 (10.0.1.11):**

```bash
sudo tee /etc/mongod.conf <<'EOF'
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
    indexConfig:
      prefixCompression: true

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
  bindIp: 10.0.1.11,127.0.0.1  # Different IP
  maxIncomingConnections: 65536
  compression:
    compressors: snappy,zstd

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

**On mongo-3 (10.0.1.12):**

```bash
sudo tee /etc/mongod.conf <<'EOF'
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
    indexConfig:
      prefixCompression: true

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
  bindIp: 10.0.1.12,127.0.0.1  # Different IP
  maxIncomingConnections: 65536
  compression:
    compressors: snappy,zstd

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

#### Step 3.3: Start MongoDB (All 3 Servers)

```bash
# Enable and start MongoDB
sudo systemctl enable mongod
sudo systemctl start mongod

# Check status
sudo systemctl status mongod

# Verify MongoDB is listening
sudo netstat -tulpn | grep 27017
# Should show: tcp 0 0 10.0.1.10:27017 0.0.0.0:* LISTEN

# Check logs
sudo tail -f /var/log/mongodb/mongod.log
# Look for: "Waiting for connections"
```

---

### Phase 4: Initialize Replica Set

#### Step 4.1: Connect to mongo-1 and Initialize

```bash
# Connect to mongo-1 (no authentication yet)
mongosh --host 10.0.1.10 --port 27017
```

```javascript
// Initialize replica set
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo-1:27017", priority: 2 },  // Higher priority = preferred PRIMARY
    { _id: 1, host: "mongo-2:27017", priority: 1 },
    { _id: 2, host: "mongo-3:27017", priority: 1 }
  ]
})

// Expected output:
// { ok: 1 }

// Wait 10-15 seconds for election
// Prompt will change to: rs0 [direct: primary]

// Check status
rs.status()

// Look for:
// - members[0].stateStr: "PRIMARY"
// - members[1].stateStr: "SECONDARY"
// - members[2].stateStr: "SECONDARY"
// - All members health: 1
```

#### Step 4.2: Create Admin User (On PRIMARY)

```javascript
// Switch to admin database
use admin

// Create root user
db.createUser({
  user: "admin",
  pwd: "AdminSecurePassword123!",  // CHANGE THIS
  roles: [
    { role: "root", db: "admin" }
  ]
})

// Expected output:
// { ok: 1 }

// Exit mongosh
exit
```

#### Step 4.3: Reconnect with Authentication

```bash
# Reconnect with authentication
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/admin?replicaSet=rs0"
```

```javascript
// Verify you're authenticated
db.runCommand({ connectionStatus: 1 })

// Should show: authenticatedUsers: [ { user: 'admin', db: 'admin' } ]

// Check replica set status
rs.status()

// All members should be healthy
```

---

### Phase 5: Create Application Users and Databases

#### Step 5.1: Create Application Database and User

```javascript
// Create application database
use mydb

// Create application user with read/write access
db.createUser({
  user: "appuser",
  pwd: "AppSecurePassword123!",  // CHANGE THIS
  roles: [
    { role: "readWrite", db: "mydb" }
  ]
})

// Create read-only user (for analytics)
db.createUser({
  user: "readonly",
  pwd: "ReadOnlyPassword123!",  // CHANGE THIS
  roles: [
    { role: "read", db: "mydb" }
  ]
})

// Verify users
db.getUsers()
```

#### Step 5.2: Test Application User Connection

```bash
# Exit current session
exit

# Connect as application user
mongosh "mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb"
```

```javascript
// Test write with majority concern
db.test_collection.insertOne(
  { message: "Hello from replica set!", timestamp: new Date() },
  { writeConcern: { w: "majority", wtimeout: 5000 } }
)

// Expected output:
// {
//   acknowledged: true,
//   insertedId: ObjectId("...")
// }

// Verify replication
db.test_collection.find()

// Check replication status
rs.printSecondaryReplicationInfo()
// Should show: all secondaries < 1 second behind
```

---

## Security Hardening

### Step 6.1: Enable TLS/SSL Encryption

#### Generate Self-Signed Certificates (For Testing)

```bash
# On mongo-1, generate CA certificate
openssl req -newkey rsa:4096 -x509 -days 365 -nodes \
  -out /etc/ssl/mongodb-ca.crt \
  -keyout /etc/ssl/mongodb-ca.key \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=MongoDB-CA"

# Generate server certificates for each member
for host in mongo-1 mongo-2 mongo-3; do
  # Generate private key
  openssl genrsa -out /etc/ssl/${host}.key 4096
  
  # Generate certificate signing request
  openssl req -new -key /etc/ssl/${host}.key \
    -out /etc/ssl/${host}.csr \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=${host}"
  
  # Sign with CA
  openssl x509 -req -in /etc/ssl/${host}.csr \
    -CA /etc/ssl/mongodb-ca.crt \
    -CAkey /etc/ssl/mongodb-ca.key \
    -CAcreateserial -out /etc/ssl/${host}.crt \
    -days 365
  
  # Combine key and cert
  cat /etc/ssl/${host}.key /etc/ssl/${host}.crt > /etc/ssl/${host}.pem
  chmod 400 /etc/ssl/${host}.pem
  chown mongodb:mongodb /etc/ssl/${host}.pem
done

# Copy certificates to respective servers
scp /etc/ssl/mongo-2.pem mongo-2:/etc/ssl/mongodb.pem
scp /etc/ssl/mongo-3.pem mongo-3:/etc/ssl/mongodb.pem
scp /etc/ssl/mongodb-ca.crt mongo-2:/etc/ssl/mongodb-ca.crt
scp /etc/ssl/mongodb-ca.crt mongo-3:/etc/ssl/mongodb-ca.crt
```

#### Update mongod.conf (All Servers)

```yaml
# Add to /etc/mongod.conf
net:
  tls:
    mode: requireTLS
    certificateKeyFile: /etc/ssl/mongodb.pem
    CAFile: /etc/ssl/mongodb-ca.crt
    allowConnectionsWithoutCertificates: true  # Allow password auth
```

```bash
# Restart MongoDB on all servers
sudo systemctl restart mongod
```

#### Test TLS Connection

```bash
mongosh "mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&tls=true&tlsCAFile=/etc/ssl/mongodb-ca.crt"
```

### Step 6.2: Configure Audit Logging

```yaml
# Add to /etc/mongod.conf
auditLog:
  destination: file
  format: JSON
  path: /var/log/mongodb/audit.log
  filter: '{ atype: { $in: ["authenticate", "createUser", "dropUser", "dropDatabase", "shutdown"] } }'
```

```bash
# Restart MongoDB
sudo systemctl restart mongod

# Monitor audit log
sudo tail -f /var/log/mongodb/audit.log
```

### Step 6.3: Restrict Network Access

```bash
# Update firewall to allow only application servers
# Remove previous rules
sudo ufw delete allow from 10.0.1.10 to any port 27017
sudo ufw delete allow from 10.0.1.11 to any port 27017
sudo ufw delete allow from 10.0.1.12 to any port 27017

# Allow only replica set members + application servers
sudo ufw allow from 10.0.1.10 to any port 27017  # mongo-1
sudo ufw allow from 10.0.1.11 to any port 27017  # mongo-2
sudo ufw allow from 10.0.1.12 to any port 27017  # mongo-3
sudo ufw allow from 10.0.2.0/24 to any port 27017  # App server subnet

sudo ufw reload
```

---

## Monitoring Setup

### Step 7.1: Install MongoDB Exporter for Prometheus

```bash
# On a separate monitoring server (or mongo-1)
wget https://github.com/percona/mongodb_exporter/releases/download/v0.40.0/mongodb_exporter-0.40.0.linux-amd64.tar.gz
tar xvzf mongodb_exporter-0.40.0.linux-amd64.tar.gz
sudo mv mongodb_exporter /usr/local/bin/
sudo chmod +x /usr/local/bin/mongodb_exporter

# Create monitoring user in MongoDB
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0"
```

```javascript
use admin
db.createUser({
  user: "exporter",
  pwd: "ExporterPassword123!",
  roles: [
    { role: "clusterMonitor", db: "admin" },
    { role: "read", db: "local" }
  ]
})
```

```bash
# Create systemd service
sudo tee /etc/systemd/system/mongodb_exporter.service <<EOF
[Unit]
Description=MongoDB Exporter
After=network.target

[Service]
Type=simple
User=mongodb
Environment="MONGODB_URI=mongodb://exporter:ExporterPassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/?replicaSet=rs0&authSource=admin"
ExecStart=/usr/local/bin/mongodb_exporter
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mongodb_exporter
sudo systemctl start mongodb_exporter

# Verify
curl http://localhost:9216/metrics | grep mongodb_up
# Should show: mongodb_up 1
```

### Step 7.2: Create Monitoring Dashboard

**Key Metrics to Monitor:**

```javascript
// Connect to PRIMARY
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0"

// 1. Replication lag
rs.printSecondaryReplicationInfo()

// 2. Oplog window
use local
db.oplog.rs.stats()

// 3. Connection pool usage
db.serverStatus().connections

// 4. Write concern errors
db.serverStatus().metrics.repl

// 5. Slow queries
db.system.profile.find().sort({ ts: -1 }).limit(10)

// 6. Disk usage
db.stats()

// 7. Cache statistics
db.serverStatus().wiredTiger.cache
```

### Step 7.3: Set Up Alerts

**Create alert script:**

```bash
sudo tee /usr/local/bin/mongodb-health-check.sh <<'EOF'
#!/bin/bash

# MongoDB Health Check Script
MONGO_URI="mongodb://admin:AdminSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/admin?replicaSet=rs0"
ALERT_EMAIL="admin@example.com"

# Check replication lag
LAG=$(mongosh "$MONGO_URI" --quiet --eval "
  var lag = 0;
  rs.status().members.forEach(function(m) {
    if (m.stateStr == 'SECONDARY') {
      var lagSec = (rs.status().members[0].optimeDate - m.optimeDate) / 1000;
      if (lagSec > lag) lag = lagSec;
    }
  });
  print(lag);
")

if (( $(echo "$LAG > 10" | bc -l) )); then
  echo "ALERT: Replication lag is ${LAG} seconds" | mail -s "MongoDB Alert" $ALERT_EMAIL
fi

# Check member health
UNHEALTHY=$(mongosh "$MONGO_URI" --quiet --eval "
  var unhealthy = 0;
  rs.status().members.forEach(function(m) {
    if (m.health != 1) unhealthy++;
  });
  print(unhealthy);
")

if [ "$UNHEALTHY" -gt 0 ]; then
  echo "ALERT: $UNHEALTHY members are unhealthy" | mail -s "MongoDB Alert" $ALERT_EMAIL
fi
EOF

sudo chmod +x /usr/local/bin/mongodb-health-check.sh

# Add to crontab (run every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/mongodb-health-check.sh") | crontab -
```

---

## Backup Configuration

### Step 8.1: Automated Backup Script

```bash
sudo tee /usr/local/bin/mongodb-backup.sh <<'EOF'
#!/bin/bash

# MongoDB Backup Script
BACKUP_DIR="/backup/mongodb"
MONGO_URI="mongodb://admin:AdminSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/?replicaSet=rs0&authSource=admin&readPreference=secondary"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup (reads from SECONDARY to avoid PRIMARY load)
mongodump --uri="$MONGO_URI" --out="$BACKUP_DIR/backup_$DATE" --gzip

# Compress backup
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz -C $BACKUP_DIR backup_$DATE
rm -rf $BACKUP_DIR/backup_$DATE

# Remove old backups
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Verify backup
if [ -f "$BACKUP_DIR/backup_$DATE.tar.gz" ]; then
  echo "Backup successful: backup_$DATE.tar.gz"
else
  echo "Backup failed!" | mail -s "MongoDB Backup Failed" admin@example.com
fi
EOF

sudo chmod +x /usr/local/bin/mongodb-backup.sh

# Schedule daily backup at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/mongodb-backup.sh") | crontab -
```

### Step 8.2: Point-in-Time Recovery Setup

```bash
# Enable oplog backup (continuous)
sudo tee /usr/local/bin/mongodb-oplog-backup.sh <<'EOF'
#!/bin/bash

BACKUP_DIR="/backup/mongodb/oplog"
MONGO_URI="mongodb://admin:AdminSecurePassword123!@mongo-1:27017/?authSource=admin"

mkdir -p $BACKUP_DIR

# Backup oplog continuously
mongodump --uri="$MONGO_URI" --db=local --collection=oplog.rs \
  --out="$BACKUP_DIR/oplog_$(date +%Y%m%d_%H%M%S)" --gzip
EOF

sudo chmod +x /usr/local/bin/mongodb-oplog-backup.sh

# Run every hour
(crontab -l 2>/dev/null; echo "0 * * * * /usr/local/bin/mongodb-oplog-backup.sh") | crontab -
```

### Step 8.3: Restore Procedure

```bash
# Restore from backup
mongorestore --uri="mongodb://admin:AdminSecurePassword123!@mongo-1:27017/?authSource=admin" \
  --gzip --archive=/backup/mongodb/backup_20241223_020000.tar.gz \
  --drop  # Drop existing collections before restore

# Point-in-time restore (restore backup + replay oplog)
mongorestore --uri="mongodb://admin:AdminSecurePassword123!@mongo-1:27017/?authSource=admin" \
  --gzip --archive=/backup/mongodb/backup_20241223_020000.tar.gz

mongorestore --uri="mongodb://admin:AdminSecurePassword123!@mongo-1:27017/?authSource=admin" \
  --gzip --oplogReplay --oplogFile=/backup/mongodb/oplog/oplog_20241223_030000/local/oplog.rs.bson.gz
```

---

## Application Integration

### Step 9.1: Python Application Example

```python
# requirements.txt
pymongo==4.6.0

# app.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Production connection string
MONGO_URI = "mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority&wtimeout=5000&readPreference=primary&maxPoolSize=100&minPoolSize=10&retryWrites=true"

def get_mongo_client():
    """Create MongoDB client with production settings"""
    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        # Test connection
        client.admin.command('ping')
        logger.info("Connected to MongoDB replica set")
        return client
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

def insert_document(collection, document):
    """Insert document with majority write concern"""
    try:
        result = collection.insert_one(
            document,
            write_concern=WriteConcern(w="majority", wtimeout=5000)
        )
        logger.info(f"Inserted document: {result.inserted_id}")
        return result.inserted_id
    except OperationFailure as e:
        logger.error(f"Write failed: {e}")
        raise

# Usage
if __name__ == "__main__":
    client = get_mongo_client()
    db = client.mydb
    collection = db.users
    
    # Insert with automatic retry
    user_id = insert_document(collection, {
        "name": "John Doe",
        "email": "john@example.com",
        "created_at": datetime.utcnow()
    })
    
    # Read from PRIMARY (strong consistency)
    user = collection.find_one({"_id": user_id})
    print(f"User: {user}")
    
    client.close()
```

### Step 9.2: Node.js Application Example

```javascript
// package.json
{
  "dependencies": {
    "mongodb": "^6.3.0"
  }
}

// app.js
const { MongoClient } = require('mongodb');

const MONGO_URI = "mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority&wtimeout=5000&readPreference=primary&maxPoolSize=100&minPoolSize=10&retryWrites=true";

async function main() {
  const client = new MongoClient(MONGO_URI, {
    serverSelectionTimeoutMS: 5000,
    connectTimeoutMS: 10000,
    socketTimeoutMS: 10000
  });

  try {
    await client.connect();
    console.log("Connected to MongoDB replica set");

    const db = client.db('mydb');
    const collection = db.collection('users');

    // Insert with majority write concern
    const result = await collection.insertOne(
      {
        name: "Jane Doe",
        email: "jane@example.com",
        createdAt: new Date()
      },
      { writeConcern: { w: "majority", wtimeout: 5000 } }
    );

    console.log(`Inserted document: ${result.insertedId}`);

    // Read from PRIMARY
    const user = await collection.findOne({ _id: result.insertedId });
    console.log("User:", user);

  } catch (error) {
    console.error("Error:", error);
  } finally {
    await client.close();
  }
}

main();
```

---

## Testing & Validation

### Step 10.1: Functional Tests

```javascript
// Connect to replica set
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/admin?replicaSet=rs0"

// Test 1: Verify replica set status
rs.status()
// Expected: 1 PRIMARY, 2 SECONDARYs, all health: 1

// Test 2: Write with majority concern
use testdb
db.test.insertOne(
  { test: "data", timestamp: new Date() },
  { writeConcern: { w: "majority", wtimeout: 5000 } }
)
// Expected: acknowledged: true

// Test 3: Verify replication
rs.printSecondaryReplicationInfo()
// Expected: lag < 1 second

// Test 4: Read from SECONDARY
db.getMongo().setReadPref("secondary")
db.test.find()
// Expected: Document found

// Test 5: Connection pool
db.serverStatus().connections
// Expected: current < 100, available > 0
```

### Step 10.2: Failover Test

```javascript
// On PRIMARY, step down
rs.stepDown(60)

// Wait 10-15 seconds
// Check new PRIMARY
rs.status()
// Expected: New PRIMARY elected

// Test write to new PRIMARY
db.test.insertOne({ failover_test: true })
// Expected: Success

// Old PRIMARY should rejoin as SECONDARY
// Wait 1 minute, check status
rs.status()
// Expected: 3 members, all healthy
```

### Step 10.3: Performance Benchmark

```bash
# Install mongoperf
sudo apt install -y mongodb-org-tools

# Run write benchmark
mongosh "mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb" <<EOF
use benchmark
for (var i = 0; i < 10000; i++) {
  db.test.insertOne(
    { index: i, data: "x".repeat(100), timestamp: new Date() },
    { writeConcern: { w: "majority" } }
  );
}
EOF

# Measure time
# Expected: ~10-20 seconds for 10k documents (500-1000 writes/sec)
```

---

## Maintenance Procedures

### Step 11.1: Rolling Upgrade

```bash
# Upgrade MongoDB from 7.0 to 7.1 (example)

# 1. Upgrade SECONDARY 1 (mongo-2)
ssh mongo-2
sudo apt update
sudo apt install -y mongodb-org=7.1.0
sudo systemctl restart mongod

# Wait for it to catch up
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "rs.printSecondaryReplicationInfo()"

# 2. Upgrade SECONDARY 2 (mongo-3)
ssh mongo-3
sudo apt update
sudo apt install -y mongodb-org=7.1.0
sudo systemctl restart mongod

# 3. Step down PRIMARY and upgrade
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "rs.stepDown(60)"

ssh mongo-1
sudo apt update
sudo apt install -y mongodb-org=7.1.0
sudo systemctl restart mongod

# 4. Verify all members upgraded
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "db.version()"
```

### Step 11.2: Add New Member

```javascript
// Connect to PRIMARY
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0"

// Add new member (mongo-4)
rs.add({ host: "mongo-4:27017", priority: 1 })

// Verify
rs.status()
// Expected: 4 members, new member in STARTUP2 then SECONDARY
```

### Step 11.3: Remove Member

```javascript
// Remove member
rs.remove("mongo-4:27017")

// Verify
rs.status()
// Expected: 3 members
```

### Step 11.4: Resize Oplog

```javascript
// Check current oplog size
use local
db.oplog.rs.stats().maxSize / (1024 * 1024)  // Size in MB

// Resize to 20GB (20480 MB)
use admin
db.adminCommand({ replSetResizeOplog: 1, size: 20480 })

// Verify
use local
db.oplog.rs.stats().maxSize / (1024 * 1024)
// Expected: 20480
```

---

## Production Checklist

### Pre-Deployment

- [ ] 3+ servers with odd number of voting members
- [ ] NTP configured and synchronized
- [ ] Firewall rules configured
- [ ] THP disabled
- [ ] System limits increased
- [ ] MongoDB 7.0+ installed
- [ ] Keyfile generated and distributed
- [ ] mongod.conf configured on all members
- [ ] Replica set initialized
- [ ] Admin user created
- [ ] Application users created
- [ ] TLS/SSL enabled (optional but recommended)
- [ ] Audit logging configured

### Post-Deployment

- [ ] Replica set status verified (rs.status())
- [ ] Replication lag < 1 second
- [ ] Write concern tested (w: "majority")
- [ ] Failover tested
- [ ] Monitoring configured (Prometheus + Grafana)
- [ ] Alerts configured (lag, member down, disk space)
- [ ] Backup script configured and tested
- [ ] Restore procedure tested
- [ ] Application connection tested
- [ ] Performance benchmark completed
- [ ] Documentation updated with connection strings
- [ ] Runbook created for common issues

---

## Connection String Summary

**Final Production Connection String:**

```
mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority&wtimeout=5000&readPreference=primary&maxPoolSize=100&minPoolSize=10&retryWrites=true&tls=true&tlsCAFile=/etc/ssl/mongodb-ca.crt
```

**Environment Variables (Recommended):**

```bash
# .env file
MONGODB_URI=mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority&wtimeout=5000&readPreference=primary&maxPoolSize=100&minPoolSize=10&retryWrites=true
MONGODB_DATABASE=mydb
```

**Docker Compose Example:**

```yaml
version: '3.8'
services:
  app:
    image: myapp:latest
    environment:
      - MONGODB_URI=mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority&wtimeout=5000
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

---

## Troubleshooting Common Issues

| Issue | Solution |
|-------|----------|
| `no primary found in replica set` | Wait 10-15s for election, check `rs.status()` |
| `Authentication failed` | Verify username/password, check `authSource` |
| `connection refused` | Check firewall, verify mongod is running |
| `WriteConcernError: waiting for replication timed out` | Check replication lag with `rs.printSecondaryReplicationInfo()` |
| `MongoServerSelectionTimeoutError` | Verify `replicaSet=rs0` in connection string |
| Replication lag > 10 seconds | Check disk I/O, network, resource usage on SECONDARY |

---

**Congratulations!** You now have a production-ready MongoDB replica set with:
- ✅ High availability (survives 1 node failure)
- ✅ Data durability (w: "majority" write concern)
- ✅ Security (authentication + TLS)
- ✅ Monitoring (health checks + alerts)
- ✅ Backups (daily + point-in-time recovery)
- ✅ Tested failover procedures

**Next Steps:**
1. Test failover in staging environment
2. Load test with production-like traffic
3. Document connection strings for all applications
4. Train team on monitoring and maintenance procedures
5. Schedule regular backup restoration tests
