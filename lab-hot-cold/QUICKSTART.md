# Quick Start Guide - Hot-Cold Data Separation

## 🚀 5-Minute Quick Start

### Step 1: Start the System (30 seconds)

```bash
cd /home/rk/Documents/labs/lab-hot-cold
docker-compose up -d
```

**What happens:**
- MongoDB starts (Port 27017) with optimized settings
- Django starts (Port 8000)
- FastAPI starts (Port 8001)
- Nginx starts (Port 80)

### Step 2: Create Indexes (30 seconds - First Time Only)

```bash
# Wait for MongoDB to be ready (check logs)
docker logs -f mongo
# Press Ctrl+C when you see "Waiting for connections"

# Create optimized indexes
docker exec -it fastapi python scripts/setup_mongodb_indexes.py
```

### Step 3: Verify System (30 seconds)

```bash
# Check all services are running
docker-compose ps

# Test FastAPI health
curl http://localhost:8001/health

# Expected response:
# {
#   "status": "ok",
#   "timestamp": "2024-12-02T...",
#   "router_stats": {"hot_hits": 0, "cold_hits": 0, ...}
# }
```

### Step 3: Create Test Data (1 minute)

```bash
# Create a user (goes to HOT storage)
curl -X POST http://localhost/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "status": "active"
  }'

# Create more users
curl -X POST http://localhost/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane@example.com",
    "status": "active"
  }'
```

### Step 4: Query Data (30 seconds)

```bash
# List all users (queries both hot and cold)
curl http://localhost/api/users

# Get specific user
curl http://localhost/api/users/USER_ID_HERE
```

### Step 5: View Metrics (1 minute)

```bash
# Storage metrics
curl http://localhost/api/metrics/storage | jq

# Data distribution
curl http://localhost/api/metrics/distribution | jq

# Router statistics
curl http://localhost/api/metrics/router-stats | jq
```

### Step 6: Test Migration (2 minutes)

```bash
# Enter FastAPI container
docker exec -it fastapi bash

# Analyze current data distribution
python scripts/analyze_data.py

# Dry run migration (see what would be migrated)
python scripts/migrate_cold_data.py --collection users --dry-run

# Actual migration (if you have old data)
python scripts/migrate_cold_data.py --collection users
```

---

## 📖 Common Operations

### View Logs

```bash
# FastAPI logs
docker logs -f fastapi

# Django logs
docker logs -f django

# MongoDB Hot logs
docker logs -f mongo_hot

# MongoDB Cold logs
docker logs -f mongo_cold
```

### Access MongoDB Directly

```bash
# Access Hot MongoDB
docker exec -it mongo_hot mongosh hot_cold_db_hot

# Access Cold MongoDB
docker exec -it mongo_cold mongosh hot_cold_db_cold

# Count documents
db.users.count()
db.users_archive.count()
```

### Stop/Restart System

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes all data)
docker-compose down -v

# Restart specific service
docker-compose restart fastapi
```

---

## 🎯 Understanding the Flow

### When You Create Data:
```
POST /api/users → FastAPI → Router → HOT Database
```
✅ All new data goes to HOT storage

### When You Query Data:
```
GET /api/users/123 → FastAPI → Router → Check HOT first → If not found, check COLD
```
✅ Fast queries (hot data) + Complete results (includes cold data)

### When Migration Runs:
```
Old data in HOT → Migrator → Move to COLD → Delete from HOT
```
✅ Keeps HOT database small and fast

---

## 🔧 Configuration Quick Reference

### Environment Variables (in docker-compose.yml)

```yaml
# How old before moving to cold?
HOT_THRESHOLD_DAYS=90        # Default: 90 days

# How many records to migrate at once?
MIGRATION_BATCH_SIZE=1000    # Default: 1000

# Delete from hot after migration?
DELETE_AFTER_MIGRATION=True  # Default: True

# Verify before deleting?
VERIFY_MIGRATION=True        # Default: True
```

### Collection Policies (in backend/data_separation/config.py)

```python
COLLECTIONS_CONFIG = {
    'users': {
        'enabled': True,
        'policy': 'access_based',    # Move if not accessed in 30 days
        'date_field': 'last_login',
        'access_field': 'last_accessed',
    },
    'orders': {
        'enabled': True,
        'policy': 'time_based',      # Move if older than 90 days
        'date_field': 'created_at',
    },
}
```

---

## 🐛 Troubleshooting

### Problem: Can't connect to MongoDB

```bash
# Check if MongoDB containers are running
docker ps | grep mongo

# Check MongoDB logs
docker logs mongo_hot
docker logs mongo_cold

# Restart MongoDB
docker-compose restart mongo_hot mongo_cold
```

### Problem: FastAPI not starting

```bash
# Check logs
docker logs fastapi

# Common issues:
# 1. MongoDB not ready - wait 10 seconds and restart
# 2. Port conflict - check if port 8001 is in use

# Rebuild and restart
docker-compose up -d --build fastapi
```

### Problem: Migration not working

```bash
# Enter container
docker exec -it fastapi bash

# Test connection
python -c "
from data_separation.migrator import DataMigrator
import asyncio
async def test():
    m = DataMigrator()
    await m.connect()
    print('✓ Connected successfully')
asyncio.run(test())
"

# Check configuration
python -c "
from data_separation.config import COLLECTIONS_CONFIG
print(COLLECTIONS_CONFIG)
"
```

---

## 📚 File Reference

### Need to change policies?
→ Edit `backend/data_separation/config.py`

### Need to add new collection?
→ Add to `COLLECTIONS_CONFIG` in `config.py`

### Need to run migration manually?
→ Use `backend/scripts/migrate_cold_data.py`

### Need to restore data?
→ Use `backend/scripts/restore_hot_data.py`

### Need to analyze data?
→ Use `backend/scripts/analyze_data.py`

---

## 🎓 Next Steps

1. **Add Real Data**: Import your existing data
2. **Configure Policies**: Adjust thresholds for your use case
3. **Set Up Monitoring**: Configure alerts for storage limits
4. **Schedule Migrations**: Set up Celery for automated migrations
5. **Production Deploy**: Update environment variables for production

---

## 📞 Quick Help

### View all API endpoints:
```bash
curl http://localhost/api/docs
# or visit: http://localhost:8001/docs
```

### Check system health:
```bash
curl http://localhost/health
```

### View current metrics:
```bash
curl http://localhost/api/metrics/storage | jq '.total'
```

---

**For detailed architecture:** See [ARCHITECTURE.md](ARCHITECTURE.md)
**For complete documentation:** See [README.md](README.md)
**For implementation details:** See walkthrough.md in artifacts
