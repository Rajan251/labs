# S3/Cloud Storage Setup Guide - MongoDB Hot + S3 Cold

## 🎯 Overview

This guide shows you how to use **MongoDB for hot data** and **S3/MinIO/GCS for cold data**.

**Architecture:**
```
Hot Data → MongoDB (fast queries, recent data)
Cold Data → S3/MinIO/GCS (cheap storage, archived data)
Metadata → MongoDB (for fast lookups)
```

## 📦 Supported Cloud Providers

| Provider | Backend | Cost | Setup Difficulty |
|----------|---------|------|------------------|
| **AWS S3** | `s3` | Low | Easy |
| **MinIO** | `minio` | Free (self-hosted) | Very Easy |
| **Google Cloud Storage** | `gcs` | Low | Medium |
| **Azure Blob** | `azure` | Low | Medium |

---

## 🚀 Quick Start with MinIO (Recommended for Testing)

MinIO is S3-compatible and runs locally - perfect for testing!

### Step 1: Add MinIO to docker-compose.yml

```yaml
version: '3.8'

services:
  # Existing MongoDB (hot data)
  mongo:
    # ... existing config

  # MinIO (S3-compatible cold storage)
  minio:
    image: minio/minio:latest
    container_name: minio
    ports:
      - "9000:9000"      # API
      - "9001:9001"      # Console
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    restart: unless-stopped

  # FastAPI with cloud storage enabled
  fastapi:
    # ... existing config
    environment:
      # MongoDB (hot)
      - HOT_MONGO_URI=mongodb://mongo:27017
      - HOT_DB_NAME=hot_cold_db
      
      # Cloud Storage (cold)
      - USE_CLOUD_COLD_STORAGE=True
      - CLOUD_BACKEND=minio
      - CLOUD_ENDPOINT=http://minio:9000
      - COLD_BUCKET=cold-data-archive
      - CLOUD_ACCESS_KEY=minioadmin
      - CLOUD_SECRET_KEY=minioadmin
      - CLOUD_REGION=us-east-1
    depends_on:
      - mongo
      - minio

volumes:
  minio_data:
```

### Step 2: Install Cloud Dependencies

```bash
# Update FastAPI requirements
docker exec -it fastapi pip install boto3
```

### Step 3: Create MinIO Bucket

```bash
# Access MinIO console
# Open browser: http://localhost:9001
# Login: minioadmin / minioadmin
# Create bucket: cold-data-archive
```

Or use CLI:
```bash
docker exec -it minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec -it minio mc mb local/cold-data-archive
```

### Step 4: Test Migration

```bash
# Migrate data to MinIO
docker exec -it fastapi python scripts/migrate_to_cloud.py --collection users --dry-run

# Actual migration
docker exec -it fastapi python scripts/migrate_to_cloud.py --collection users
```

---

## 🌐 AWS S3 Setup

### Step 1: Create S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://my-cold-data-archive --region us-east-1

# Set lifecycle policy (optional - auto-transition to Glacier)
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-cold-data-archive \
  --lifecycle-configuration file://lifecycle.json
```

**lifecycle.json:**
```json
{
  "Rules": [{
    "Id": "Archive old data to Glacier",
    "Status": "Enabled",
    "Transitions": [{
      "Days": 90,
      "StorageClass": "GLACIER"
    }]
  }]
}
```

### Step 2: Update docker-compose.yml

```yaml
fastapi:
  environment:
    - USE_CLOUD_COLD_STORAGE=True
    - CLOUD_BACKEND=s3
    - CLOUD_ENDPOINT=https://s3.amazonaws.com
    - COLD_BUCKET=my-cold-data-archive
    - CLOUD_ACCESS_KEY=YOUR_AWS_ACCESS_KEY
    - CLOUD_SECRET_KEY=YOUR_AWS_SECRET_KEY
    - CLOUD_REGION=us-east-1
```

### Step 3: Install Dependencies

```bash
docker exec -it fastapi pip install boto3
```

---

## 💡 How It Works

### Data Flow

**1. Migration (Hot → Cold):**
```
MongoDB (hot)
    ↓
1. Find old documents (>90 days)
2. Upload full document to S3
3. Create metadata stub in MongoDB
4. Delete from hot MongoDB
    ↓
S3 Bucket (cold)
```

**2. Retrieval (Cold → User):**
```
User Request
    ↓
1. Check MongoDB metadata
2. Get S3 key from metadata
3. Download from S3
4. Return to user
```

**3. Restore (Cold → Hot):**
```
S3 Bucket (cold)
    ↓
1. Download from S3
2. Insert into hot MongoDB
3. Delete metadata
4. Delete from S3
    ↓
MongoDB (hot)
```

### Storage Structure

**MongoDB (Hot):**
```json
{
  "_id": "user123",
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2024-12-01"
}
```

**S3 (Cold):**
```
Bucket: cold-data-archive
Key: users/2024/11/user123.json
Content: {full document as JSON}
```

**MongoDB (Cold Metadata):**
```json
{
  "_id": "user123",
  "_storage_location": "cloud",
  "_storage_backend": "s3",
  "_storage_key": "users/2024/11/user123.json",
  "_migrated_at": "2024-12-01T10:00:00",
  "created_at": "2024-11-01",
  "email": "john@example.com"  // Searchable fields
}
```

---

## 🔧 Configuration Options

### Environment Variables

```yaml
# Enable cloud storage
USE_CLOUD_COLD_STORAGE=True

# Backend type
CLOUD_BACKEND=s3  # or 'minio', 'gcs', 'azure'

# S3/MinIO settings
CLOUD_ENDPOINT=http://minio:9000
COLD_BUCKET=cold-data-archive
CLOUD_ACCESS_KEY=your_access_key
CLOUD_SECRET_KEY=your_secret_key
CLOUD_REGION=us-east-1

# Migration settings
COLD_THRESHOLD_DAYS=90  # Migrate data older than 90 days
```

### Per-Collection Configuration

Edit `backend/data_separation/config.py`:

```python
COLLECTIONS_CONFIG = {
    'users': {
        'enabled': True,
        'cold_storage': 'mongodb',  # Keep in MongoDB
    },
    'media': {
        'enabled': True,
        'cold_storage': 's3',  # Large files to S3
    },
    'logs': {
        'enabled': True,
        'cold_storage': 's3',  # Logs to S3
    },
}
```

---

## 📊 Cost Comparison

### MongoDB vs S3 (1TB data)

| Storage | MongoDB | S3 Standard | S3 Glacier | Savings |
|---------|---------|-------------|------------|---------|
| **Cost/month** | $200 | $23 | $4 | 80-98% |
| **Retrieval** | Instant | Instant | Minutes | - |
| **Best For** | Hot data | Warm data | Cold data | - |

### Example: 10TB Archive

- **MongoDB only:** $2,000/month
- **MongoDB (1TB hot) + S3 (9TB cold):** $200 + $207 = **$407/month**
- **Savings:** $1,593/month (80% reduction)

---

## 🧪 Testing

### 1. Create Test Data

```bash
# Create users in hot MongoDB
curl -X POST http://localhost/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}'
```

### 2. Migrate to Cloud

```bash
# Dry run
docker exec -it fastapi python scripts/migrate_to_cloud.py \
  --collection users --dry-run

# Actual migration
docker exec -it fastapi python scripts/migrate_to_cloud.py \
  --collection users
```

### 3. Verify in S3/MinIO

```bash
# List objects in MinIO
docker exec -it minio mc ls local/cold-data-archive/users/

# Download object
docker exec -it minio mc cat local/cold-data-archive/users/2024/12/user123.json
```

### 4. Retrieve from Cloud

```bash
# Get user from cloud (via API)
curl http://localhost/api/archive/users/user123
```

---

## 🔍 Monitoring

### Check Storage Usage

```bash
# MongoDB size
docker exec -it mongo mongosh hot_cold_db --eval "db.stats(1024*1024)"

# S3 size (AWS CLI)
aws s3 ls s3://my-cold-data-archive --recursive --summarize

# MinIO size
docker exec -it minio mc du local/cold-data-archive
```

### Check Migration Status

```bash
# View metadata
docker exec -it mongo mongosh hot_cold_db --eval "
  db.users_archive.find({_storage_location: 'cloud'}).count()
"
```

---

## 🐛 Troubleshooting

### Issue: boto3 not installed

```bash
docker exec -it fastapi pip install boto3
# Or rebuild container
docker-compose up -d --build fastapi
```

### Issue: MinIO connection refused

```bash
# Check MinIO is running
docker ps | grep minio

# Check MinIO logs
docker logs minio

# Restart MinIO
docker-compose restart minio
```

### Issue: S3 access denied

```bash
# Verify credentials
docker exec -it fastapi python -c "
import boto3
s3 = boto3.client('s3',
    aws_access_key_id='YOUR_KEY',
    aws_secret_access_key='YOUR_SECRET'
)
print(s3.list_buckets())
"
```

---

## 📝 Summary

**Setup Steps:**
1. ✅ Add MinIO/S3 to docker-compose.yml
2. ✅ Set environment variables
3. ✅ Install boto3
4. ✅ Create bucket
5. ✅ Run migration

**Files Created:**
- `cloud_storage.py` - S3/MinIO/GCS adapters
- `hybrid_migrator.py` - MongoDB + Cloud migrator
- `migrate_to_cloud.py` - Migration script
- `requirements-cloud.txt` - Cloud dependencies

**Benefits:**
- 💰 80-98% cost savings
- 📦 Unlimited cold storage
- 🚀 Fast hot data queries
- 🔍 Metadata for quick lookups

---

**Next Steps:**
1. Test with MinIO locally
2. Migrate to production S3
3. Set up lifecycle policies
4. Monitor storage costs
