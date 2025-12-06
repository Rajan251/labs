# Hot-Cold Data Separation - Django + FastAPI + MongoDB

A production-ready implementation of hot-cold data separation using Django, FastAPI, and MongoDB with intelligent query routing and automated data migration.

## 🎯 Overview

This project implements a sophisticated hot-cold data separation architecture where:
- **Hot Data**: Frequently accessed, recent data stored in high-performance MongoDB instance
- **Cold Data**: Rarely accessed, archived data stored in cost-optimized MongoDB instance
- **Intelligent Routing**: Automatic query routing with fallback mechanism
- **Automated Migration**: Scheduled data migration based on configurable policies

## 📋 Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Data Migration](#data-migration)
- [Monitoring](#monitoring)
- [Production Deployment](#production-deployment)

## 🏗️ Architecture

```
┌─────────────┐
│   Nginx     │  (Port 80)
└──────┬──────┘
       │
       ├──────────────┐
       │              │
┌──────▼──────┐  ┌───▼────────┐
│   Django    │  │  FastAPI   │
│  (Port 8000)│  │ (Port 8001)│
└──────┬──────┘  └─────┬──────┘
       │               │
       │    ┌──────────┴──────────┐
       │    │   Query Router      │
       │    │  (Intelligent)      │
       │    └──────────┬──────────┘
       │               │
       └───────────────┼───────────────┐
                       │               │
              ┌────────▼────────┐  ┌───▼──────────┐
              │    MongoDB      │  │  Monitoring  │
              │ Community Ed.   │  │   Metrics    │
              │  (Port 27017)   │  │              │
              │                 │  └──────────────┘
              │ ┌─────────────┐ │
              │ │Hot Collections│
              │ │- users      │ │
              │ │- orders     │ │
              │ │- logs       │ │
              │ └─────────────┘ │
              │ ┌─────────────┐ │
              │ │Cold Collections│
              │ │- users_archive│
              │ │- orders_archive│
              │ │- logs_archive │
              │ └─────────────┘ │
              └─────────────────┘
```

> **Note:** Optimized for MongoDB Community Edition using a single instance with collection-level separation. See [MONGODB_COMMUNITY_SETUP.md](MONGODB_COMMUNITY_SETUP.md) for details.


## ✨ Features

### 1. **Multiple Separation Strategies**
- **Time-based**: Separate by data age (e.g., >90 days → cold)
- **Access-based**: Separate by access frequency (e.g., not accessed in 30 days → cold)
- **Hybrid**: Combine age and access patterns

### 2. **Intelligent Query Routing**
- Automatic hot DB check first
- Seamless fallback to cold DB
- Optional promotion of cold data to hot on access
- Access timestamp tracking

### 3. **Automated Migration**
- Batch processing for efficiency
- Dry-run mode for testing
- Data integrity verification
- Celery-based scheduling

### 4. **Comprehensive Monitoring**
- Storage usage metrics
- Query performance tracking
- Migration history
- Distribution analytics

## 📁 Directory Structure

```
lab-hot-cold/
├── backend/
│   ├── django_app/              # Django application
│   │   ├── core/                # Settings & config
│   │   ├── users/               # User app
│   │   └── manage.py
│   ├── fastapi_app/             # FastAPI application
│   │   └── main.py              # Main app with router integration
│   ├── data_separation/         # Hot-cold separation logic
│   │   ├── config.py            # Configuration & policies
│   │   ├── migrator.py          # Data migration logic
│   │   ├── router.py            # Query routing logic
│   │   └── scheduler.py         # Automated scheduling
│   ├── scripts/                 # Management scripts
│   │   ├── migrate_cold_data.py # Manual migration
│   │   ├── restore_hot_data.py  # Restore from cold
│   │   └── analyze_data.py      # Data analysis
│   └── monitoring/              # Monitoring & metrics
│       └── data_metrics.py      # Metrics tracking
├── docker/                      # Docker configurations
│   ├── django/
│   ├── fastapi/
│   └── nginx/
├── docker-compose.yml           # Docker Compose setup
└── README.md                    # This file
```

## 🚀 Installation

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- 4GB+ RAM (for both MongoDB instances)

### Step 1: Clone and Setup

```bash
cd /home/rk/Documents/labs/lab-hot-cold

# Verify directory structure
ls -la
```

### Step 2: Build and Start Services

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### Step 3: Verify Connections

```bash
# Check MongoDB
docker exec -it mongo mongosh --eval "db.adminCommand('ping')"

# Check FastAPI
curl http://localhost:8001/health
```

### Step 4: Create Indexes (First Time Only)

```bash
# Create optimized indexes for better performance
docker exec -it fastapi python scripts/setup_mongodb_indexes.py
```


## ⚙️ Configuration

### Environment Variables

Edit `docker-compose.yml` to configure:

```yaml
environment:
  # Database connections
  - HOT_MONGO_URI=mongodb://mongo_hot:27017
  - COLD_MONGO_URI=mongodb://mongo_cold:27017
  
  # Separation policies
  - HOT_THRESHOLD_DAYS=90        # Data newer than 90 days stays hot
  - COLD_THRESHOLD_DAYS=90       # Data older than 90 days → cold
  - HOT_ACCESS_DAYS=30           # Accessed in last 30 days → hot
  
  # Migration settings
  - MIGRATION_BATCH_SIZE=1000    # Records per batch
  - DELETE_AFTER_MIGRATION=True  # Remove from hot after migration
  - VERIFY_MIGRATION=True        # Verify before deleting
```

### Collection Configuration

Edit `backend/data_separation/config.py`:

```python
COLLECTIONS_CONFIG = {
    'users': {
        'enabled': True,
        'hot_collection': 'users',
        'cold_collection': 'users_archive',
        'policy': 'access_based',     # or 'time_based', 'hybrid'
        'date_field': 'last_login',
        'access_field': 'last_accessed',
    },
    # Add more collections...
}
```

## 📖 Usage

### Using the FastAPI Application

The FastAPI app automatically uses the query router for all operations:

```python
# GET /api/users/123
# Automatically checks hot DB first, then cold

# POST /api/users
# Always creates in hot storage

# GET /api/users?limit=10
# Queries both hot and cold, merges results
```

### Manual Data Migration

```bash
# Enter FastAPI container
docker exec -it fastapi bash

# Dry run (see what would be migrated)
python scripts/migrate_cold_data.py --collection users --dry-run

# Actual migration
python scripts/migrate_cold_data.py --collection users

# Migrate all collections
python scripts/migrate_cold_data.py --all
```

### Restore Data from Cold to Hot

```bash
# Restore specific user
python scripts/restore_hot_data.py --collection users --query '{"_id": "user123"}'

# Restore recently accessed data
python scripts/restore_hot_data.py --collection users --query '{"last_accessed": {"$gte": "2024-11-01"}}'
```

### Analyze Data Distribution

```bash
# Analyze all collections
python scripts/analyze_data.py

# Analyze specific collection
python scripts/analyze_data.py --collection users
```

## 🔌 API Endpoints

### User Endpoints

```bash
# Get user (checks hot → cold)
curl http://localhost/api/users/123

# List users (merges hot + cold)
curl http://localhost/api/users?limit=10&skip=0

# Create user (always in hot)
curl -X POST http://localhost/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

### Metrics Endpoints

```bash
# Storage metrics
curl http://localhost/api/metrics/storage

# Data distribution
curl http://localhost/api/metrics/distribution

# Router statistics
curl http://localhost/api/metrics/router-stats

# Migration history
curl http://localhost/api/metrics/migration-history?days=7
```

### Admin Endpoints

```bash
# Trigger migration (dry run)
curl -X POST "http://localhost/api/admin/migrate/users?dry_run=true"

# Trigger actual migration
curl -X POST "http://localhost/api/admin/migrate/users?dry_run=false"
```

## 📊 Monitoring

### View Storage Metrics

```bash
curl http://localhost/api/metrics/storage | jq
```

Response:
```json
{
  "timestamp": "2024-12-02T17:30:00",
  "hot": {
    "users": {
      "size_mb": 125.5,
      "document_count": 50000
    }
  },
  "cold": {
    "users_archive": {
      "size_mb": 450.2,
      "document_count": 200000
    }
  },
  "total": {
    "hot_size_gb": 0.12,
    "cold_size_gb": 0.44,
    "total_documents": 250000
  }
}
```

### View Router Statistics

```bash
curl http://localhost/api/metrics/router-stats | jq
```

Response:
```json
{
  "stats": {
    "hot_hits": 8500,
    "cold_hits": 150,
    "cache_hits": 0,
    "misses": 10
  },
  "timestamp": "2024-12-02T17:30:00"
}
```

## 🏭 Production Deployment

### Step 1: Update Environment Variables

Create `.env.production`:

```bash
# Security
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=False

# Database
HOT_MONGO_URI=mongodb://prod-mongo-hot:27017
COLD_MONGO_URI=mongodb://prod-mongo-cold:27017

# Policies
HOT_THRESHOLD_DAYS=60
MIGRATION_BATCH_SIZE=5000

# Monitoring
MONITORING_ENABLED=True
ALERT_THRESHOLD_GB=500
```

### Step 2: Configure Automated Migration

Set up Celery for scheduled migrations:

```bash
# Install Celery
pip install celery redis

# Start Celery worker
celery -A data_separation.scheduler worker --loglevel=info

# Start Celery beat (scheduler)
celery -A data_separation.scheduler beat --loglevel=info
```

### Step 3: Set Up Monitoring Alerts

Configure alerts in `backend/data_separation/config.py`:

```python
MONITORING_CONFIG = {
    'alert_threshold_gb': 500,  # Alert when hot storage exceeds 500GB
    'notification_email': 'ops@example.com',
}
```

### Step 4: Backup Strategy

```bash
# Backup hot MongoDB
docker exec mongo_hot mongodump --out=/backup/hot

# Backup cold MongoDB
docker exec mongo_cold mongodump --out=/backup/cold
```

## 🔧 Troubleshooting

### Issue: Migration Not Working

```bash
# Check MongoDB connections
docker exec -it fastapi python -c "
from data_separation.migrator import DataMigrator
import asyncio
async def test():
    m = DataMigrator()
    await m.connect()
    print('Connected!')
asyncio.run(test())
"
```

### Issue: Query Router Not Finding Data

```bash
# Check router stats
curl http://localhost/api/metrics/router-stats

# Manually check both databases
docker exec -it mongo_hot mongosh hot_cold_db_hot --eval "db.users.count()"
docker exec -it mongo_cold mongosh hot_cold_db_cold --eval "db.users_archive.count()"
```

### Issue: High Memory Usage

Adjust MongoDB cache size in `docker-compose.yml`:

```yaml
mongo_hot:
  command: mongod --wiredTigerCacheSizeGB 1  # Reduce from 2GB to 1GB
```

## 📚 Additional Resources

### Data Separation Methods

1. **Time-Based**: Best for logs, transactions, events
2. **Access-Based**: Best for user profiles, documents
3. **Hybrid**: Best for e-commerce orders, analytics

### Performance Tips

- Use indexes on `date_field` and `access_field`
- Run migrations during off-peak hours
- Monitor hot storage size regularly
- Adjust `MIGRATION_BATCH_SIZE` based on available memory

### Security Considerations

- Use authentication for MongoDB in production
- Encrypt data at rest
- Use SSL/TLS for database connections
- Implement proper access controls

## 📝 License

MIT License

## 🤝 Contributing

Contributions welcome! Please submit pull requests.

---

**Questions?** Check the troubleshooting section or open an issue.
