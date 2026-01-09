# Environment Variables Guide for MongoDB Replica Set

## 📋 Overview

This guide explains how to use environment variables (`.env` files) to configure your MongoDB replica set connection in different environments.

---

## 📁 Available .env Files

| File | Purpose | Use Case |
|------|---------|----------|
| `.env.example` | Template with all options | Copy and customize for your needs |
| `.env.local` | Local development | Single MongoDB instance on localhost |
| `.env.development` | Development environment | 3-node replica set for dev team |
| `.env.staging` | Staging environment | Pre-production testing |
| `.env.production` | Production environment | Live production deployment |

---

## 🚀 Quick Start

### Step 1: Choose Your Environment File

```bash
# For local development (single node)
cp .env.local .env

# For development with replica set
cp .env.development .env

# For staging
cp .env.staging .env

# For production
cp .env.production .env
```

### Step 2: Update Values

Edit `.env` and replace placeholders:

```bash
# Replace these values
MONGODB_USERNAME=appuser              # Your MongoDB username
MONGODB_PASSWORD=YourStrongPassword!  # Your MongoDB password
MONGODB_HOSTS=mongo-1:27017,mongo-2:27017,mongo-3:27017  # Your server hostnames
MONGODB_DATABASE=mydb                 # Your database name
```

### Step 3: Install Dependencies

**Python:**
```bash
pip install python-dotenv pymongo
```

**Node.js:**
```bash
npm install dotenv mongodb
```

### Step 4: Use in Your Application

**Python:**
```python
from dotenv import load_dotenv
load_dotenv()  # Load .env file

# Now use the example code
from python_env_example import MongoDBConnection
mongo = MongoDBConnection()
db = mongo.connect()
```

**Node.js:**
```javascript
require('dotenv').config();  // Load .env file

// Now use the example code
const { MongoDBConnection } = require('./nodejs_env_example');
const mongo = new MongoDBConnection();
await mongo.connect();
```

---

## 🔑 Key Environment Variables Explained

### Connection String (RECOMMENDED)

```bash
# Full connection string - easiest option
MONGODB_URI=mongodb://username:password@host1:27017,host2:27017,host3:27017/database?replicaSet=rs0&w=majority
```

**Format:**
```
mongodb://[username:password@]host1[:port1][,host2[:port2],...]/[database][?options]
```

### Individual Components (Alternative)

```bash
MONGODB_USERNAME=appuser
MONGODB_PASSWORD=SecurePassword123!
MONGODB_HOSTS=mongo-1:27017,mongo-2:27017,mongo-3:27017
MONGODB_DATABASE=mydb
MONGODB_REPLICA_SET=rs0
MONGODB_AUTH_SOURCE=admin
```

### Write Concern (Data Safety)

```bash
# Options:
# 1 = Fast but risky (data loss possible)
# "majority" = Balanced (RECOMMENDED for production)
# 2 or 3 = Safest but slower

MONGODB_WRITE_CONCERN=majority
MONGODB_WRITE_TIMEOUT_MS=5000
MONGODB_JOURNAL=true
```

### Read Preference (Performance)

```bash
# Options:
# primary = Read from PRIMARY only (strong consistency)
# secondary = Read from SECONDARY only (scale reads)
# secondaryPreferred = Prefer SECONDARY, fallback to PRIMARY
# nearest = Read from closest member (low latency)

MONGODB_READ_PREFERENCE=primary
MONGODB_MAX_STALENESS_SECONDS=90
```

### Connection Pool (Concurrency)

```bash
# Max connections per application instance
MONGODB_MAX_POOL_SIZE=100

# Min connections to keep alive
MONGODB_MIN_POOL_SIZE=10

# Max idle time before closing connection
MONGODB_MAX_IDLE_TIME_MS=30000
```

### TLS/SSL (Security)

```bash
# Enable TLS encryption
MONGODB_TLS_ENABLED=true

# Path to CA certificate
MONGODB_TLS_CA_FILE=/etc/ssl/mongodb-ca.crt

# Path to client certificate
MONGODB_TLS_CERT_FILE=/etc/ssl/mongodb-client.pem
```

---

## 📊 Environment-Specific Configurations

### Local Development (.env.local)

```bash
# Simple, single-node MongoDB
MONGODB_URI=mongodb://localhost:27017/mydb
MONGODB_WRITE_CONCERN=1  # Fast for development
MONGODB_MAX_POOL_SIZE=10  # Small pool
```

**Use when:**
- Developing on your laptop
- No replica set needed
- Fast iteration

### Development (.env.development)

```bash
# 3-node replica set for team
MONGODB_URI=mongodb://appuser:password@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&w=majority
MONGODB_MAX_POOL_SIZE=100
MONGODB_READ_PREFERENCE=primary
```

**Use when:**
- Shared development environment
- Testing replica set features
- Team collaboration

### Staging (.env.staging)

```bash
# Pre-production testing
MONGODB_URI=mongodb://appuser:password@mongo-1.staging.com:27017,mongo-2.staging.com:27017,mongo-3.staging.com:27017/staging_db?replicaSet=rs0&w=majority
MONGODB_MAX_POOL_SIZE=50
MONGODB_TLS_ENABLED=false  # Optional TLS
```

**Use when:**
- Testing before production
- QA environment
- Performance testing

### Production (.env.production)

```bash
# Production with all security features
MONGODB_URI=mongodb://appuser:STRONG_PASSWORD@mongo-1.prod.com:27017,mongo-2.prod.com:27017,mongo-3.prod.com:27017/prod_db?replicaSet=rs0&w=majority&tls=true&tlsCAFile=/etc/ssl/ca.crt
MONGODB_MAX_POOL_SIZE=200  # Higher pool for production
MONGODB_TLS_ENABLED=true  # REQUIRED
MONGODB_MONITORING_ENABLED=true
BACKUP_ENABLED=true
```

**Use when:**
- Live production deployment
- Customer-facing application
- Maximum security and performance

---

## 🔒 Security Best Practices

### 1. Never Commit .env Files

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "!.env.example" >> .gitignore
```

### 2. Use Strong Passwords

```bash
# ❌ BAD
MONGODB_PASSWORD=password123

# ✅ GOOD
MONGODB_PASSWORD=Xy9$mK2!pL8@nQ4#vR7
```

### 3. Rotate Credentials Regularly

```bash
# Update passwords every 90 days
# Use different passwords for each environment
```

### 4. Use Secrets Management in Production

```bash
# Instead of .env files, use:
# - AWS Secrets Manager
# - HashiCorp Vault
# - Kubernetes Secrets
# - Azure Key Vault
```

---

## 🧪 Testing Your Configuration

### Test Connection

**Python:**
```bash
python examples/python_env_example.py
```

**Node.js:**
```bash
node examples/nodejs_env_example.js
```

### Expected Output

```
Connecting to MongoDB (development)...
App Name: MyApplication
✅ Connected to MongoDB successfully
MongoDB Version: 7.0.x
Replica Set: rs0
Primary: mongo-1:27017
Write Concern: majority
Read Preference: primary
Connection Pool: 10-100

============================================================
MongoDB Connection Test
============================================================

📝 Inserting test document...
   Document ID: 6589abc123def456789...

📖 Reading documents...
   - Hello from .env configuration! (development)

============================================================
✅ Test completed successfully!
============================================================
```

---

## 🔧 Troubleshooting

### Issue: "Cannot find module 'dotenv'"

**Solution:**
```bash
# Python
pip install python-dotenv

# Node.js
npm install dotenv
```

### Issue: "Authentication failed"

**Solution:**
```bash
# Check credentials in .env
MONGODB_USERNAME=appuser  # Correct username
MONGODB_PASSWORD=YourPassword  # Correct password
MONGODB_AUTH_SOURCE=admin  # Correct auth database
```

### Issue: "No primary found in replica set"

**Solution:**
```bash
# Check replica set name
MONGODB_REPLICA_SET=rs0  # Must match your replica set name

# Verify replica set is running
mongosh "mongodb://admin:password@mongo-1:27017/admin" --eval "rs.status()"
```

### Issue: "Connection timeout"

**Solution:**
```bash
# Check hostnames are correct
MONGODB_HOSTS=mongo-1:27017,mongo-2:27017,mongo-3:27017

# Verify network connectivity
ping mongo-1
telnet mongo-1 27017

# Increase timeout
MONGODB_CONNECT_TIMEOUT_MS=30000
```

---

## 📝 Complete Example

### 1. Create .env file

```bash
cp .env.development .env
```

### 2. Edit .env

```bash
MONGODB_URI=mongodb://appuser:AppSecurePassword123!@mongo-1:27017,mongo-2:27017,mongo-3:27017/mydb?replicaSet=rs0&authSource=mydb&w=majority&wtimeout=5000&readPreference=primary&maxPoolSize=100&minPoolSize=10&retryWrites=true

MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10
MONGODB_WRITE_CONCERN=majority
MONGODB_READ_PREFERENCE=primary

APP_NAME=MyApplication
APP_ENV=development
APP_PORT=3000
```

### 3. Use in Python

```python
# app.py
from dotenv import load_dotenv
from python_env_example import MongoDBConnection

load_dotenv()

mongo = MongoDBConnection()
db = mongo.connect()

# Your application code here
result = mongo.insert_document("users", {"name": "John"})
users = mongo.find_documents("users")

mongo.close()
```

### 4. Use in Node.js

```javascript
// app.js
require('dotenv').config();
const { MongoDBConnection } = require('./nodejs_env_example');

async function main() {
  const mongo = new MongoDBConnection();
  await mongo.connect();
  
  // Your application code here
  await mongo.insertDocument('users', { name: 'John' });
  const users = await mongo.findDocuments('users');
  
  await mongo.close();
}

main();
```

---

## 📚 Additional Resources

- **MongoDB Connection String Documentation**: https://docs.mongodb.com/manual/reference/connection-string/
- **Write Concern**: https://docs.mongodb.com/manual/reference/write-concern/
- **Read Preference**: https://docs.mongodb.com/manual/core/read-preference/
- **python-dotenv**: https://pypi.org/project/python-dotenv/
- **dotenv (Node.js)**: https://www.npmjs.com/package/dotenv

---

## ✅ Checklist

- [ ] Copied appropriate .env file (local, development, staging, production)
- [ ] Updated MongoDB credentials (username, password)
- [ ] Updated MongoDB hosts (mongo-1, mongo-2, mongo-3)
- [ ] Updated database name
- [ ] Verified replica set name matches
- [ ] Set appropriate write concern (majority for production)
- [ ] Set appropriate read preference (primary for consistency)
- [ ] Configured connection pool size
- [ ] Enabled TLS for production
- [ ] Added .env to .gitignore
- [ ] Tested connection with example code
- [ ] Verified application can connect and perform CRUD operations

---

**Your MongoDB connection is now configured with environment variables! 🎉**
