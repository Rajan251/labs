# Configuration Guide - Cold Storage & Read URLs

## 🎯 Overview

This guide explains how to configure different storage backends for cold data and use different URLs for reading hot vs cold data.

## 📦 Storage Backend Options

### Option 1: Same MongoDB Instance (DEFAULT)
**Best for:** Small to medium datasets, simple setup

```yaml
# docker-compose.yml
environment:
  - HOT_MONGO_URI=mongodb://mongo:27017
  - HOT_DB_NAME=hot_cold_db
  - COLD_MONGO_URI=mongodb://mongo:27017
  - COLD_DB_NAME=hot_cold_db
  - COLD_STORAGE_BACKEND=mongodb
```

**How it works:**
- Hot data: `hot_cold_db.users`
- Cold data: `hot_cold_db.users_archive`
- Same instance, different collections

---

### Option 2: Different MongoDB Instance
**Best for:** Large datasets, dedicated cold storage server

```yaml
# docker-compose.yml
environment:
  - HOT_MONGO_URI=mongodb://mongo-hot:27017
  - HOT_DB_NAME=hot_db
  - COLD_MONGO_URI=mongodb://mongo-cold:27017
  - COLD_DB_NAME=cold_db
  - COLD_STORAGE_BACKEND=mongodb
```

**Setup:**
```yaml
# Add to docker-compose.yml
services:
  mongo-cold:
    image: mongo:5.0
    container_name: mongo-cold
    volumes:
      - mongo_cold_data:/data/db
    ports:
      - "27018:27017"
    command: >
      mongod
      --wiredTigerCacheSizeGB 1
      --wiredTigerCollectionBlockCompressor zstd
      --storageEngine wiredTiger
```

**How it works:**
- Hot data: `mongo-hot:27017/hot_db.users`
- Cold data: `mongo-cold:27017/cold_db.users_archive`
- Separate instances, can use different hardware

---

### Option 3: Cloud Storage (S3/MinIO) for Cold Data
**Best for:** Very large datasets, cost optimization

```yaml
# docker-compose.yml
environment:
  - HOT_MONGO_URI=mongodb://mongo:27017
  - HOT_DB_NAME=hot_cold_db
  - USE_CLOUD_COLD_STORAGE=True
  - CLOUD_BACKEND=s3  # or 'minio'
  - CLOUD_ENDPOINT=https://s3.amazonaws.com
  - COLD_BUCKET=my-cold-data-archive
  - CLOUD_ACCESS_KEY=your_access_key
  - CLOUD_SECRET_KEY=your_secret_key
  - CLOUD_REGION=us-east-1
```

**How it works:**
- Hot data: MongoDB `hot_cold_db.users`
- Cold data: S3 bucket `my-cold-data-archive/users/`
- Metadata in MongoDB, actual data in S3

---

### Option 4: MongoDB Atlas (Cloud) for Cold Data
**Best for:** Managed solution, global distribution

```yaml
# docker-compose.yml
environment:
  - HOT_MONGO_URI=mongodb://mongo:27017
  - HOT_DB_NAME=hot_cold_db
  - COLD_MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net
  - COLD_DB_NAME=cold_archive_db
  - COLD_STORAGE_BACKEND=mongodb
```

**How it works:**
- Hot data: Local MongoDB
- Cold data: MongoDB Atlas cluster
- Automatic backups, global CDN

---

## 🌐 Different Read URLs Configuration

### Scenario 1: Same Service, Different Endpoints

```yaml
# docker-compose.yml
environment:
  - HOT_READ_URL=http://localhost:8001
  - COLD_READ_URL=http://localhost:8001
  - USE_DIFFERENT_COLD_URL=True
  - COLD_URL_PATTERN=/archive/{collection}/{id}
```

**URLs:**
- Hot: `GET http://localhost:8001/api/users/123`
- Cold: `GET http://localhost:8001/api/archive/users/123`

---

### Scenario 2: Separate Cold Data Service

```yaml
# docker-compose.yml
services:
  fastapi-hot:
    # ... hot data service on port 8001
    
  fastapi-cold:
    # ... cold data service on port 8002
    environment:
      - COLD_READ_URL=http://fastapi-cold:8002
      - USE_DIFFERENT_COLD_URL=True
```

**URLs:**
- Hot: `GET http://localhost:8001/api/users/123`
- Cold: `GET http://localhost:8002/api/users/123`

---

### Scenario 3: CDN for Cold Data

```yaml
# docker-compose.yml
environment:
  - HOT_READ_URL=http://localhost:8001
  - COLD_READ_URL=https://cdn.example.com/cold-data
  - USE_DIFFERENT_COLD_URL=True
```

**URLs:**
- Hot: `GET http://localhost:8001/api/users/123`
- Cold: `GET https://cdn.example.com/cold-data/users/123`

---

## 🔧 Step-by-Step Configuration

### Example: Different MongoDB Instance for Cold Data

**Step 1: Update docker-compose.yml**

```yaml
version: '3.8'

services:
  # Hot MongoDB
  mongo-hot:
    image: mongo:5.0
    container_name: mongo-hot
    volumes:
      - mongo_hot_data:/data/db
    ports:
      - "27017:27017"
    command: >
      mongod
      --wiredTigerCacheSizeGB 2
      --wiredTigerCollectionBlockCompressor snappy

  # Cold MongoDB (cheaper storage, lower performance)
  mongo-cold:
    image: mongo:5.0
    container_name: mongo-cold
    volumes:
      - mongo_cold_data:/data/db
    ports:
      - "27018:27017"
    command: >
      mongod
      --wiredTigerCacheSizeGB 0.5
      --wiredTigerCollectionBlockCompressor zstd
      --storageEngine wiredTiger

  fastapi:
    # ... other config
    environment:
      - HOT_MONGO_URI=mongodb://mongo-hot:27017
      - HOT_DB_NAME=hot_db
      - COLD_MONGO_URI=mongodb://mongo-cold:27017
      - COLD_DB_NAME=cold_db
      - COLD_STORAGE_BACKEND=mongodb

volumes:
  mongo_hot_data:
  mongo_cold_data:
```

**Step 2: Restart services**

```bash
docker-compose down
docker-compose up -d
```

**Step 3: Verify connections**

```bash
# Check hot MongoDB
docker exec -it mongo-hot mongosh --eval "db.adminCommand('ping')"

# Check cold MongoDB
docker exec -it mongo-cold mongosh --eval "db.adminCommand('ping')"
```

---

### Example: Different Read URLs

**Step 1: Update docker-compose.yml**

```yaml
fastapi:
  environment:
    - HOT_READ_URL=http://localhost:8001
    - COLD_READ_URL=http://localhost:8001
    - USE_DIFFERENT_COLD_URL=True
    - COLD_URL_PATTERN=/api/archive/{collection}/{id}
```

**Step 2: Update FastAPI routes**

The router automatically handles different URLs based on configuration.

**Step 3: Test**

```bash
# Hot data (fast)
curl http://localhost:8001/api/users/123

# Cold data (different endpoint)
curl http://localhost:8001/api/archive/users/456
```

---

## 📊 Comparison Table

| Option | Cost | Performance | Complexity | Best For |
|--------|------|-------------|------------|----------|
| **Same MongoDB** | Low | Good | Simple | < 100GB data |
| **Different MongoDB** | Medium | Excellent | Medium | 100GB - 1TB |
| **Cloud Storage (S3)** | Very Low | Slow | Complex | > 1TB, archival |
| **MongoDB Atlas** | Medium | Good | Simple | Managed solution |

---

## 🎯 Recommended Configurations

### Small Project (< 100GB)
```yaml
HOT_MONGO_URI=mongodb://mongo:27017
COLD_MONGO_URI=mongodb://mongo:27017
COLD_STORAGE_BACKEND=mongodb
```

### Medium Project (100GB - 1TB)
```yaml
HOT_MONGO_URI=mongodb://mongo-hot:27017
COLD_MONGO_URI=mongodb://mongo-cold:27017
COLD_STORAGE_BACKEND=mongodb
```

### Large Project (> 1TB)
```yaml
HOT_MONGO_URI=mongodb://mongo:27017
USE_CLOUD_COLD_STORAGE=True
CLOUD_BACKEND=s3
COLD_BUCKET=my-archive-bucket
```

---

## 🔍 How to Change Configuration

### 1. Edit docker-compose.yml

```yaml
environment:
  # Change these values
  - COLD_MONGO_URI=mongodb://your-cold-server:27017
  - COLD_DB_NAME=your_cold_db
  - COLD_READ_URL=http://your-cold-service:8002
```

### 2. Edit config.py (optional)

```python
# backend/data_separation/config.py

# For per-collection storage backend
COLLECTIONS_CONFIG = {
    'users': {
        'cold_storage': 'mongodb',  # or 's3', 'minio'
    },
    'media': {
        'cold_storage': 's3',  # Large files to S3
    },
}
```

### 3. Restart services

```bash
docker-compose restart fastapi
```

---

## 🧪 Testing Different Configurations

```bash
# Test hot data access
curl http://localhost:8001/api/users/123

# Test cold data access
curl http://localhost:8001/api/archive/users/456

# Check where data is stored
docker exec -it fastapi python -c "
from data_separation.config import get_cold_storage_backend
print('Users cold storage:', get_cold_storage_backend('users'))
print('Media cold storage:', get_cold_storage_backend('media'))
"
```

---

## 📝 Summary

**To change cold storage:**
1. Set `COLD_MONGO_URI` environment variable
2. Optionally set `COLD_STORAGE_BACKEND` (mongodb/s3/minio)
3. Restart services

**To change read URLs:**
1. Set `COLD_READ_URL` environment variable
2. Set `USE_DIFFERENT_COLD_URL=True`
3. Optionally customize `COLD_URL_PATTERN`
4. Restart services

**All changes are in:**
- `docker-compose.yml` (environment variables)
- `backend/data_separation/config.py` (per-collection overrides)

No code changes needed - just configuration!
