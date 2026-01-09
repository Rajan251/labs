# MongoDB Replica Set - Quick Reference Card

## 🎯 Server Information

| Server | Hostname | IP | Role | Priority |
|--------|----------|-----|------|----------|
| **mongo-1** | mongo-1 | 10.0.1.10 | PRIMARY | 2 |
| **mongo-2** | mongo-2 | 10.0.1.11 | SECONDARY-1 | 1 |
| **mongo-3** | mongo-3 | 10.0.1.12 | SECONDARY-2 | 1 |

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

## 📝 Quick Commands

### Check Replica Set Status
```bash
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "rs.status()"
```

### Check Replication Lag
```bash
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "rs.printSecondaryReplicationInfo()"
```

### Check Connection Pool
```bash
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "db.serverStatus().connections"
```

### Manual Failover
```bash
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "rs.stepDown(60)"
```

### Check Oplog Size
```bash
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "db.getSiblingDB('local').oplog.rs.stats()"
```

---

## 🐍 Python Code Template

```python
from pymongo import MongoClient
from pymongo.write_concern import WriteConcern

# Connection
MONGO_URI = "mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority"
client = MongoClient(MONGO_URI)
db = client.mydb

# Insert with majority write concern
result = db.users.insert_one(
    {"name": "John", "email": "john@example.com"},
    write_concern=WriteConcern(w="majority", wtimeout=5000)
)

# Read from PRIMARY
user = db.users.find_one({"email": "john@example.com"})

# Close connection
client.close()
```

---

## 🟢 Node.js Code Template

```javascript
const { MongoClient } = require('mongodb');

const MONGO_URI = "mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority";

async function main() {
  const client = new MongoClient(MONGO_URI);
  await client.connect();
  
  const db = client.db('mydb');
  
  // Insert with majority write concern
  await db.collection('users').insertOne(
    { name: "John", email: "john@example.com" },
    { writeConcern: { w: "majority", wtimeout: 5000 } }
  );
  
  // Read from PRIMARY
  const user = await db.collection('users').findOne({ email: "john@example.com" });
  
  await client.close();
}

main();
```

---

## 🧪 Testing Commands

### Run Complete Test Suite
```bash
./test-mongodb-setup.sh
```

### Manual Tests
```javascript
// Test 1: Insert with majority concern
use testdb
db.test.insertOne(
  { message: "test", timestamp: new Date() },
  { writeConcern: { w: "majority", wtimeout: 5000 } }
)

// Test 2: Check replication
rs.printSecondaryReplicationInfo()

// Test 3: Read from SECONDARY
db.getMongo().setReadPref("secondary")
db.test.find()

// Test 4: Performance test (1000 writes)
var start = new Date();
for (var i = 0; i < 1000; i++) {
  db.benchmark.insertOne({ index: i }, { writeConcern: { w: "majority" } });
}
print("Time: " + (new Date() - start) / 1000 + "s");
```

---

## 🔧 Troubleshooting

### Issue: No PRIMARY found
```bash
# Check status on each server
mongosh --host mongo-1 --port 27017 --eval "rs.status()"
mongosh --host mongo-2 --port 27017 --eval "rs.status()"
mongosh --host mongo-3 --port 27017 --eval "rs.status()"

# Wait 10-15 seconds for election
```

### Issue: Authentication failed
```bash
# Verify keyfile MD5 matches on all servers
ssh root@mongo-1 "md5sum /etc/mongodb-keyfile"
ssh root@mongo-2 "md5sum /etc/mongodb-keyfile"
ssh root@mongo-3 "md5sum /etc/mongodb-keyfile"

# Check keyfile permissions
ssh root@mongo-1 "ls -l /etc/mongodb-keyfile"
# Must be: -r-------- 1 mongodb mongodb
```

### Issue: Replication lag
```bash
# Check lag
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "rs.printSecondaryReplicationInfo()"

# Check disk I/O on SECONDARY
ssh root@mongo-2 "iostat -x 1 5"

# Resize oplog if needed
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "db.adminCommand({ replSetResizeOplog: 1, size: 20480 })"
```

### Issue: Connection refused
```bash
# Check MongoDB service
ssh root@mongo-1 "systemctl status mongod"

# Check firewall
ssh root@mongo-1 "sudo ufw status"

# Test connectivity
telnet mongo-1 27017
telnet mongo-2 27017
telnet mongo-3 27017
```

---

## 📊 Monitoring Metrics

| Metric | Command | Healthy Value |
|--------|---------|---------------|
| Replication Lag | `rs.printSecondaryReplicationInfo()` | < 1 second |
| Member Health | `rs.status().members[].health` | 1 (all members) |
| Oplog Window | `db.oplog.rs.stats()` | 24-48 hours |
| Connection Pool | `db.serverStatus().connections` | < 80% max |
| Write Concern Errors | `db.serverStatus().metrics.repl` | 0 errors |

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All 3 servers have MongoDB installed
- [ ] Keyfile identical on all servers (verify MD5)
- [ ] Firewall configured on all servers
- [ ] NTP synchronized
- [ ] THP disabled
- [ ] mongod.conf configured
- [ ] MongoDB service started

### Post-Deployment
- [ ] Replica set initialized
- [ ] Admin user created
- [ ] Application users created
- [ ] Replication lag < 1 second
- [ ] Failover tested
- [ ] Application connected successfully
- [ ] Test suite passed (./test-mongodb-setup.sh)

---

## 📞 Emergency Procedures

### PRIMARY Crashed
```bash
# 1. Check status
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-2:27017/admin" --eval "rs.status()"

# 2. Wait for automatic failover (10-15 seconds)

# 3. Verify new PRIMARY elected
# One of mongo-2 or mongo-3 should be PRIMARY

# 4. Applications will auto-reconnect (if using replica set connection string)
```

### All SECONDARYs Down
```bash
# 1. PRIMARY will continue accepting writes with w:1
# 2. Writes with w:"majority" will timeout
# 3. Restart SECONDARY servers ASAP

ssh root@mongo-2 "sudo systemctl restart mongod"
ssh root@mongo-3 "sudo systemctl restart mongod"

# 4. Wait for them to catch up
mongosh "mongodb://admin:AdminSecurePassword123!@mongo-1:27017/admin?replicaSet=rs0" --eval "rs.printSecondaryReplicationInfo()"
```

---

## 📚 Documentation Files

1. **MONGODB_HA_GUIDE.md** - Expert guide with strategies
2. **MONGODB_PRODUCTION_SETUP.md** - Complete production setup
3. **MONGODB_SERVER_BY_SERVER_SETUP.md** - Step-by-step server installation
4. **test-mongodb-setup.sh** - Automated test suite
5. **QUICK_REFERENCE.md** - This file

---

## 🎓 Next Steps

1. ✅ Complete server setup (PRIMARY, SECONDARY-1, SECONDARY-2)
2. ✅ Initialize replica set
3. ✅ Create users
4. ✅ Run test suite: `./test-mongodb-setup.sh`
5. 🔄 Deploy application with connection string
6. 🔄 Set up monitoring (Prometheus + Grafana)
7. 🔄 Configure automated backups
8. 🔄 Test failover manually
9. 🔄 Load test with production traffic
10. 🔄 Document runbooks for your team
