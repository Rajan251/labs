# MongoDB Replica Set Setup - Complete Guide

## 📚 Documentation Overview

This repository contains a complete, production-ready MongoDB replica set setup guide with step-by-step instructions, code examples, and testing procedures.

---

## 📁 Files in This Repository

### 1. **MONGODB_HA_GUIDE.md** (52 KB)
**Expert guide for MongoDB High Availability**
- System prompts and AI assistant guidelines
- 8 categories of user questions with response templates
- Write concern strategy (w:1, w:majority, w:3)
- Read preference strategy (primary, secondary, nearest)
- Quick references and troubleshooting
- Communication guidelines

**Use this for**: Understanding MongoDB HA concepts, decision-making, and best practices

---

### 2. **MONGODB_PRODUCTION_SETUP.md** (35 KB)
**Complete production setup guide**
- Connection string examples for different use cases
- Infrastructure requirements
- Step-by-step setup (11 phases)
- Security hardening (TLS, audit logging)
- Monitoring setup (Prometheus exporter)
- Backup configuration
- Application integration examples
- Maintenance procedures

**Use this for**: Understanding the complete production setup process

---

### 3. **MONGODB_SERVER_BY_SERVER_SETUP.md** (42 KB) ⭐ **START HERE**
**Server-by-server installation guide with clear labels**
- **PRIMARY (mongo-1)**: Complete setup steps
- **SECONDARY-1 (mongo-2)**: Complete setup steps
- **SECONDARY-2 (mongo-3)**: Complete setup steps
- Replica set initialization
- Code-level implementation (Python & Node.js)
- Complete testing guide
- Troubleshooting

**Use this for**: Following exact steps for each server during installation

---

### 4. **test-mongodb-setup.sh** (7 KB)
**Automated test suite**
- Tests MongoDB service status on all servers
- Verifies replica set configuration
- Checks replication lag
- Tests write concern
- Verifies data replication
- Performance benchmark
- Connection pool check

**Use this for**: Validating your MongoDB setup after installation

```bash
# Make executable
chmod +x test-mongodb-setup.sh

# Run tests
./test-mongodb-setup.sh
```

---

### 5. **QUICK_REFERENCE.md** (7 KB)
**Quick reference card**
- Server information table
- Connection strings (production, admin, read-heavy)
- Quick commands (status, lag, failover)
- Python code template
- Node.js code template
- Testing commands
- Troubleshooting guide
- Monitoring metrics
- Emergency procedures

**Use this for**: Quick lookups during development and operations

---

## 🚀 Quick Start Guide

### Step 1: Read the Server-by-Server Guide
Start with **MONGODB_SERVER_BY_SERVER_SETUP.md** - it has clear labels for each server:
- 🔴 PRIMARY (mongo-1 / 10.0.1.10)
- 🟢 SECONDARY-1 (mongo-2 / 10.0.1.11)
- 🟡 SECONDARY-2 (mongo-3 / 10.0.1.12)

### Step 2: Follow Installation Steps
Execute commands on each server as labeled:
```bash
# ============================================
# RUN ON: PRIMARY (mongo-1)
# ============================================
```

### Step 3: Initialize Replica Set
After all servers are ready, initialize on PRIMARY only:
```javascript
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo-1:27017", priority: 2 },
    { _id: 1, host: "mongo-2:27017", priority: 1 },
    { _id: 2, host: "mongo-3:27017", priority: 1 }
  ]
})
```

### Step 4: Create Users
Create admin and application users on PRIMARY:
```javascript
use admin
db.createUser({
  user: "admin",
  pwd: "AdminSecurePassword123!",
  roles: [{ role: "root", db: "admin" }]
})

use mydb
db.createUser({
  user: "appuser",
  pwd: "AppSecurePassword123!",
  roles: [{ role: "readWrite", db: "mydb" }]
})
```

### Step 5: Run Test Suite
```bash
./test-mongodb-setup.sh
```

### Step 6: Integrate with Your Application
Use the connection string:
```
mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority&wtimeout=5000&readPreference=primary&maxPoolSize=100&minPoolSize=10&retryWrites=true
```

---

## 🎯 Server Configuration Summary

| Server | Hostname | IP | Role | Priority | Votes |
|--------|----------|-----|------|----------|-------|
| **mongo-1** | mongo-1 | 10.0.1.10 | PRIMARY | 2 | 1 |
| **mongo-2** | mongo-2 | 10.0.1.11 | SECONDARY-1 | 1 | 1 |
| **mongo-3** | mongo-3 | 10.0.1.12 | SECONDARY-2 | 1 | 1 |

---

## 🔗 Connection Strings

### Production (Recommended)
```
mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority&wtimeout=5000&readPreference=primary&maxPoolSize=100&minPoolSize=10&retryWrites=true
```

### Admin Connection
```
mongodb://admin:AdminSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/admin?replicaSet=rs0
```

### Read-Heavy (Analytics)
```
mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&readPreference=secondaryPreferred&maxStalenessSeconds=90
```

---

## 🐍 Python Example

```python
from pymongo import MongoClient
from pymongo.write_concern import WriteConcern

MONGO_URI = "mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority"

client = MongoClient(MONGO_URI)
db = client.mydb

# Insert with majority write concern
result = db.users.insert_one(
    {"name": "John", "email": "john@example.com"},
    write_concern=WriteConcern(w="majority", wtimeout=5000)
)

print(f"Inserted: {result.inserted_id}")
client.close()
```

---

## 🟢 Node.js Example

```javascript
const { MongoClient } = require('mongodb');

const MONGO_URI = "mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority";

async function main() {
  const client = new MongoClient(MONGO_URI);
  await client.connect();
  
  const db = client.db('mydb');
  const result = await db.collection('users').insertOne(
    { name: "John", email: "john@example.com" },
    { writeConcern: { w: "majority", wtimeout: 5000 } }
  );
  
  console.log(`Inserted: ${result.insertedId}`);
  await client.close();
}

main();
```

---

## 🧪 Testing

### Automated Test Suite
```bash
./test-mongodb-setup.sh
```

**Tests include:**
- ✅ MongoDB service status on all servers
- ✅ Replica set status (1 PRIMARY, 2 SECONDARYs)
- ✅ Replication lag (< 10 seconds)
- ✅ Write with majority concern
- ✅ Data replication to secondaries
- ✅ Connection pool
- ✅ Performance benchmark (1000 writes)
- ✅ Oplog size
- ✅ Authentication

### Manual Tests

```javascript
// Connect to replica set
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/admin?replicaSet=rs0"

// Check status
rs.status()

// Check replication lag
rs.printSecondaryReplicationInfo()

// Test write
use testdb
db.test.insertOne(
  { message: "test", timestamp: new Date() },
  { writeConcern: { w: "majority", wtimeout: 5000 } }
)

// Test failover
rs.stepDown(60)
```

---

## 🔧 Troubleshooting

### No PRIMARY found
```bash
# Check status on each server
mongosh --host mongo-1 --port 27017 --eval "rs.status()"
mongosh --host mongo-2 --port 27017 --eval "rs.status()"
mongosh --host mongo-3 --port 27017 --eval "rs.status()"

# Wait 10-15 seconds for election
```

### Authentication failed
```bash
# Verify keyfile MD5 on all servers
ssh root@mongo-1 "md5sum /etc/mongodb-keyfile"
ssh root@mongo-2 "md5sum /etc/mongodb-keyfile"
ssh root@mongo-3 "md5sum /etc/mongodb-keyfile"
# All MD5 hashes MUST match

# Check permissions
ls -l /etc/mongodb-keyfile
# Must be: -r-------- 1 mongodb mongodb
```

### Replication lag
```bash
# Check lag
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "rs.printSecondaryReplicationInfo()"

# Check disk I/O
ssh root@mongo-2 "iostat -x 1 5"

# Resize oplog if needed
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "db.adminCommand({ replSetResizeOplog: 1, size: 20480 })"
```

---

## 📊 Monitoring

### Key Metrics to Monitor

| Metric | Command | Healthy Value |
|--------|---------|---------------|
| Replication Lag | `rs.printSecondaryReplicationInfo()` | < 1 second |
| Member Health | `rs.status().members[].health` | 1 (all) |
| Oplog Window | `db.oplog.rs.stats()` | 24-48 hours |
| Connection Pool | `db.serverStatus().connections` | < 80% max |

### Quick Status Check
```bash
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "rs.status()"
```

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All 3 servers have MongoDB installed
- [ ] Keyfile identical on all servers (verify MD5)
- [ ] Firewall configured on all servers
- [ ] NTP synchronized
- [ ] THP disabled
- [ ] mongod.conf configured with correct IPs
- [ ] MongoDB service started on all servers

### Post-Deployment
- [ ] Replica set initialized
- [ ] Admin user created
- [ ] Application users created
- [ ] Replication lag < 1 second
- [ ] Failover tested
- [ ] Application connected successfully
- [ ] Test suite passed (`./test-mongodb-setup.sh`)
- [ ] Monitoring configured
- [ ] Backups configured

---

## 📞 Support & Next Steps

### Immediate Next Steps
1. ✅ Read **MONGODB_SERVER_BY_SERVER_SETUP.md**
2. ✅ Follow installation steps for each server
3. ✅ Initialize replica set
4. ✅ Run test suite: `./test-mongodb-setup.sh`
5. 🔄 Deploy your application
6. 🔄 Set up monitoring (Prometheus + Grafana)
7. 🔄 Configure automated backups
8. 🔄 Test failover manually
9. 🔄 Load test with production traffic

### Additional Resources
- **MongoDB Documentation**: https://docs.mongodb.com/manual/replication/
- **Production Notes**: https://docs.mongodb.com/manual/administration/production-notes/
- **Security Checklist**: https://docs.mongodb.com/manual/administration/security-checklist/

---

## 📝 Summary

You now have:
- ✅ **5 comprehensive guides** covering all aspects of MongoDB HA
- ✅ **Server-by-server instructions** with clear PRIMARY/SECONDARY labels
- ✅ **Automated test suite** to validate your setup
- ✅ **Code examples** in Python and Node.js
- ✅ **Quick reference card** for daily operations
- ✅ **Production-ready configuration** with security and monitoring

**Your MongoDB replica set is ready for production! 🎉**

---

**Created**: 2025-12-23  
**MongoDB Version**: 7.0 Community Edition  
**Tested On**: Ubuntu 22.04 LTS
