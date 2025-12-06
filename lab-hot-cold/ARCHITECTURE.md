# System Architecture & Execution Flow

## 📁 Complete File Structure

```
lab-hot-cold/
├── README.md                           # Main documentation
├── ARCHITECTURE.md                     # This file - System architecture
├── docker-compose.yml                  # Docker orchestration
│
├── backend/
│   ├── data_separation/                # Hot-Cold separation logic
│   │   ├── __init__.py                # Module initializer
│   │   ├── config.py                  # [1] Configuration & policies
│   │   ├── migrator.py                # [3] Data migration engine
│   │   ├── router.py                  # [2] Query routing logic
│   │   └── scheduler.py               # [4] Automated scheduling
│   │
│   ├── monitoring/                     # Metrics & monitoring
│   │   ├── __init__.py                # Module initializer
│   │   └── data_metrics.py            # [5] Metrics tracking
│   │
│   ├── scripts/                        # Management scripts
│   │   ├── migrate_cold_data.py       # [6] Manual migration CLI
│   │   ├── restore_hot_data.py        # [7] Restoration CLI
│   │   └── analyze_data.py            # [8] Analysis CLI
│   │
│   ├── django_app/                     # Django application
│   │   ├── manage.py                  # Django CLI
│   │   ├── requirements.txt           # Django dependencies
│   │   ├── core/                      # Django core settings
│   │   │   ├── __init__.py
│   │   │   ├── settings.py            # Django configuration
│   │   │   ├── urls.py                # URL routing
│   │   │   └── wsgi.py                # WSGI application
│   │   └── users/                     # User app
│   │       ├── __init__.py
│   │       ├── apps.py
│   │       ├── models.py
│   │       ├── admin.py
│   │       └── views.py
│   │
│   └── fastapi_app/                    # FastAPI application
│       ├── main.py                    # [9] FastAPI main app
│       └── requirements.txt           # FastAPI dependencies
│
└── docker/                             # Docker configurations
    ├── django/
    │   ├── Dockerfile                 # Django container
    │   └── entrypoint.sh              # Django startup script
    ├── fastapi/
    │   ├── Dockerfile                 # FastAPI container
    │   └── entrypoint.sh              # FastAPI startup script
    └── nginx/
        └── nginx.conf                 # Nginx configuration
```

---

## 🔄 Execution Flow & Script Order

### Phase 1: System Startup (Docker Compose)

#### **Step 1: Docker Compose Initialization**
```bash
docker-compose up -d
```

**What Happens:**
1. **MongoDB Hot** starts (Port 27017)
   - Allocates 2GB cache
   - Creates `hot_cold_db_hot` database
   
2. **MongoDB Cold** starts (Port 27018)
   - Allocates 1GB cache
   - Creates `hot_cold_db_cold` database

3. **Django Container** starts
   - Waits for MongoDB Hot
   - Runs `docker/django/entrypoint.sh`

4. **FastAPI Container** starts
   - Waits for both MongoDB instances
   - Runs `docker/fastapi/entrypoint.sh`

5. **Nginx Container** starts
   - Waits for Django and FastAPI
   - Starts reverse proxy

---

### Phase 2: Application Initialization

#### **Step 2: FastAPI Startup Sequence**

**File: `backend/fastapi_app/main.py`**

```python
# Execution Order:
1. Import modules
   ├── sys.path.insert() - Add backend to path
   ├── from data_separation.router import QueryRouter
   ├── from data_separation.config import HOT_DB_CONFIG, COLD_DB_CONFIG
   └── from monitoring.data_metrics import DataMetrics

2. Create FastAPI app
   └── app = FastAPI(title="Hot-Cold Data Separation API")

3. @app.on_event("startup") - Runs automatically
   ├── Initialize QueryRouter
   │   └── Connects to both MongoDB instances
   ├── Initialize DataMetrics
   │   └── Connects to both MongoDB instances
   └── Print connection status

4. Register endpoints
   ├── User endpoints (/api/users/*)
   ├── Order endpoints (/api/orders/*)
   ├── Metrics endpoints (/api/metrics/*)
   └── Admin endpoints (/api/admin/*)

5. Start Uvicorn server
   └── Listens on 0.0.0.0:8000
```

**Detailed Startup Flow:**

```
FastAPI Container Starts
    ↓
Load main.py
    ↓
Import data_separation.config [FILE 1]
    ├── Load environment variables
    ├── Define HOT_DB_CONFIG
    ├── Define COLD_DB_CONFIG
    ├── Define COLLECTIONS_CONFIG
    └── Define all policies
    ↓
Import data_separation.router [FILE 2]
    ├── Load QueryRouter class
    └── Depends on config.py
    ↓
Import monitoring.data_metrics [FILE 5]
    ├── Load DataMetrics class
    └── Depends on config.py
    ↓
Create FastAPI app instance
    ↓
@startup event triggered
    ├── query_router = QueryRouter()
    ├── await query_router.connect()
    │   ├── Connect to mongo_hot:27017
    │   └── Connect to mongo_cold:27017
    ├── metrics_tracker = DataMetrics()
    └── await metrics_tracker.connect()
        ├── Connect to mongo_hot:27017
        └── Connect to mongo_cold:27017
    ↓
Server Ready - Listening on Port 8000
```

---

## 📋 Module Execution Order & Dependencies

### **[1] config.py - First to Load**

**Purpose:** Central configuration for all hot-cold separation logic

**Loaded By:** All other modules

**Execution:**
```python
# When imported:
1. Read environment variables
   ├── HOT_MONGO_URI
   ├── COLD_MONGO_URI
   ├── HOT_THRESHOLD_DAYS
   └── MIGRATION_BATCH_SIZE

2. Define database configurations
   ├── HOT_DB_CONFIG
   └── COLD_DB_CONFIG

3. Define separation policies
   ├── TIME_BASED_POLICY
   ├── ACCESS_BASED_POLICY
   └── HYBRID_POLICY

4. Define collection mappings
   └── COLLECTIONS_CONFIG
       ├── users (access_based)
       ├── orders (time_based)
       ├── logs (time_based)
       └── transactions (hybrid)

5. Define migration settings
6. Define routing settings
7. Define monitoring settings
```

**Key Functions:**
- `get_hot_threshold()` - Returns timedelta for hot data
- `get_cold_threshold()` - Returns timedelta for cold data
- `get_collection_config(name)` - Get config for specific collection
- `is_collection_enabled(name)` - Check if collection has hot-cold enabled

---

### **[2] router.py - Query Routing Engine**

**Purpose:** Intelligent routing of queries between hot and cold databases

**Depends On:** config.py

**Loaded By:** main.py (FastAPI startup)

**Execution Flow:**

```python
# When QueryRouter() is instantiated:
1. Initialize instance variables
   ├── hot_client = None
   ├── cold_client = None
   ├── routing_cache = {}
   └── stats = {'hot_hits': 0, 'cold_hits': 0, ...}

# When connect() is called:
2. Connect to databases
   ├── hot_client = AsyncIOMotorClient(HOT_DB_CONFIG['uri'])
   ├── cold_client = AsyncIOMotorClient(COLD_DB_CONFIG['uri'])
   ├── hot_db = hot_client[HOT_DB_CONFIG['database']]
   └── cold_db = cold_client[COLD_DB_CONFIG['database']]

# When find_one() is called:
3. Query execution
   ├── Check if collection has hot-cold enabled
   ├── Query hot database first
   │   ├── If found → Update access timestamp → Return
   │   └── If not found → Continue
   ├── Query cold database (fallback)
   │   ├── If found → Optionally promote to hot
   │   └── Update access timestamp → Return
   └── Return None if not found anywhere
```

**Key Methods:**
- `find_one(collection, query)` - Find single document
- `find(collection, query, limit, skip, sort)` - Find multiple documents
- `count_documents(collection, query)` - Count across both DBs
- `insert_one(collection, document)` - Insert into hot
- `update_one(collection, query, update)` - Update in hot or cold
- `delete_one(collection, query)` - Delete from hot or cold

---

### **[3] migrator.py - Data Migration Engine**

**Purpose:** Move data from hot to cold storage based on policies

**Depends On:** config.py

**Loaded By:** 
- scripts/migrate_cold_data.py (manual)
- scheduler.py (automated)
- main.py (admin endpoint)

**Execution Flow:**

```python
# When DataMigrator() is instantiated:
1. Initialize instance variables
   ├── hot_client = None
   ├── cold_client = None
   └── stats = {'migrated': 0, 'failed': 0, 'skipped': 0}

# When connect() is called:
2. Connect to both databases

# When migrate_collection(collection_name) is called:
3. Build migration query
   ├── Get collection config
   ├── Determine policy (time_based/access_based/hybrid)
   └── Build MongoDB query
       ├── Time-based: {date_field: {$lt: threshold}}
       ├── Access-based: {access_field: {$lt: threshold}}
       └── Hybrid: {$and: [age_check, access_check]}

4. Count records to migrate
   └── hot_db[collection].count_documents(query)

5. Migrate in batches
   ├── Fetch batch (default 1000 records)
   ├── Add migration metadata (_migrated_at, _migrated_from)
   ├── Insert into cold database
   ├── Verify insertion
   └── Delete from hot database (if verify succeeds)

6. Return statistics
   └── {migrated: X, failed: Y, skipped: Z}
```

**Key Methods:**
- `migrate_collection(name, dry_run)` - Migrate single collection
- `migrate_all(dry_run)` - Migrate all enabled collections
- `restore_to_hot(name, query, dry_run)` - Restore data from cold
- `_migrate_batch(documents, hot_coll, cold_coll)` - Internal batch processing

---

### **[4] scheduler.py - Automated Scheduling**

**Purpose:** Schedule automated migrations using Celery

**Depends On:** config.py, migrator.py

**Loaded By:** Celery worker (if enabled)

**Execution Flow:**

```python
# When Celery worker starts:
1. Initialize Celery app
   ├── Connect to Redis broker
   └── Load task definitions

# When scheduled task runs:
2. migrate_cold_data_task()
   ├── Create DataMigrator instance
   ├── Connect to databases
   ├── Run migrate_all()
   ├── Log results
   ├── Send notification (if configured)
   └── Disconnect

# Schedule configuration:
3. Beat schedule
   └── 'migrate-cold-data-daily': runs every 24 hours
```

**Key Functions:**
- `run_migration()` - Async migration execution
- `migrate_cold_data_task()` - Celery task wrapper
- `trigger_migration_sync()` - Manual trigger without Celery

---

### **[5] data_metrics.py - Monitoring & Analytics**

**Purpose:** Track metrics and performance

**Depends On:** config.py

**Loaded By:** main.py (FastAPI startup)

**Execution Flow:**

```python
# When DataMetrics() is instantiated:
1. Initialize instance variables
   ├── hot_client = None
   └── cold_client = None

# When connect() is called:
2. Connect to both databases

# When get_storage_metrics() is called:
3. Collect storage data
   ├── For each enabled collection:
   │   ├── Get hot collection stats (size, count)
   │   └── Get cold collection stats (size, count)
   ├── Calculate totals
   └── Check alert thresholds

4. Return metrics
   └── {timestamp, hot: {...}, cold: {...}, total: {...}}
```

**Key Methods:**
- `get_storage_metrics()` - Storage usage per collection
- `get_distribution_metrics()` - Hot vs cold distribution
- `log_migration_event()` - Record migration in metrics DB
- `log_query_performance()` - Track query performance
- `get_migration_history()` - Retrieve past migrations

---

## 🎯 Request Flow Examples

### Example 1: User Query Request

```
User Request: GET /api/users/123
    ↓
Nginx (Port 80)
    ↓
FastAPI (Port 8001)
    ↓
Endpoint: get_user(user_id="123")
    ↓
query_router.find_one('users', {'_id': '123'})
    ↓
[router.py execution]
    ├── Check COLLECTIONS_CONFIG['users']['enabled'] = True
    ├── hot_collection = 'users'
    ├── cold_collection = 'users_archive'
    ├── access_field = 'last_accessed'
    ↓
Step 1: Query Hot Database
    ├── hot_db.users.find_one({'_id': '123'})
    ├── Result: Found ✓
    ├── Update: users.update_one({'_id': '123'}, {$set: {last_accessed: NOW}})
    ├── stats['hot_hits'] += 1
    └── Return user document
    ↓
FastAPI Response
    └── Return JSON to client
```

### Example 2: User Query (Not in Hot)

```
User Request: GET /api/users/old_user_456
    ↓
FastAPI → query_router.find_one('users', {'_id': 'old_user_456'})
    ↓
Step 1: Query Hot Database
    ├── hot_db.users.find_one({'_id': 'old_user_456'})
    └── Result: Not Found ✗
    ↓
Step 2: Fallback to Cold Database
    ├── cold_db.users_archive.find_one({'_id': 'old_user_456'})
    ├── Result: Found ✓
    ├── stats['cold_hits'] += 1
    ↓
Step 3: Optional Promotion (if PROMOTE_ON_ACCESS=True)
    ├── Remove migration metadata
    ├── Insert into hot_db.users
    ├── Delete from cold_db.users_archive
    └── Log: "Promoted old_user_456 to hot storage"
    ↓
Step 4: Update Access Timestamp
    └── Update last_accessed field
    ↓
Return user document
```

### Example 3: Manual Migration

```
Admin runs: python scripts/migrate_cold_data.py --collection users
    ↓
[migrate_cold_data.py execution]
    ├── Parse arguments (collection='users', dry_run=False)
    ├── Import DataMigrator from migrator.py
    └── Create migrator instance
    ↓
migrator.connect()
    ├── Connect to mongo_hot:27017
    └── Connect to mongo_cold:27017
    ↓
migrator.migrate_collection('users', dry_run=False)
    ↓
[migrator.py execution]
    ├── Get config: COLLECTIONS_CONFIG['users']
    ├── Policy: 'access_based'
    ├── access_field: 'last_accessed'
    ├── threshold: 30 days ago
    ↓
Build query:
    └── {last_accessed: {$lt: 2024-11-02}}
    ↓
Count documents:
    └── hot_db.users.count_documents(query) → 5000 records
    ↓
Migrate in batches (1000 per batch):
    ├── Batch 1: 1000 records
    │   ├── Add metadata: {_migrated_at: NOW, _migrated_from: 'hot'}
    │   ├── Insert into cold_db.users_archive
    │   ├── Verify: 1000 inserted ✓
    │   └── Delete from hot_db.users
    ├── Batch 2: 1000 records
    ├── Batch 3: 1000 records
    ├── Batch 4: 1000 records
    └── Batch 5: 1000 records
    ↓
Return statistics:
    └── {migrated: 5000, failed: 0, skipped: 0}
    ↓
Print summary to console
```

---

## 🔍 Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose                          │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐    │
│  │MongoDB   │  │MongoDB   │  │ Django  │  │ FastAPI  │    │
│  │  Hot     │  │  Cold    │  │         │  │          │    │
│  │:27017    │  │:27018    │  │:8000    │  │:8001     │    │
│  └────▲─────┘  └────▲─────┘  └─────────┘  └────▲─────┘    │
│       │             │                           │          │
└───────┼─────────────┼───────────────────────────┼──────────┘
        │             │                           │
        │             │         ┌─────────────────┘
        │             │         │
    ┌───┴─────────────┴─────────┴───┐
    │      Query Router              │ [2]
    │  - find_one()                  │
    │  - find()                      │
    │  - insert_one()                │
    │  - update_one()                │
    └───────────▲────────────────────┘
                │
                │ Uses
                │
    ┌───────────┴────────────────────┐
    │      Configuration             │ [1]
    │  - HOT_DB_CONFIG               │
    │  - COLD_DB_CONFIG              │
    │  - COLLECTIONS_CONFIG          │
    │  - Policies                    │
    └───────────▲────────────────────┘
                │
                │ Used by
                │
    ┌───────────┴────────────────────┐
    │      Data Migrator             │ [3]
    │  - migrate_collection()        │
    │  - migrate_all()               │
    │  - restore_to_hot()            │
    └───────────▲────────────────────┘
                │
                │ Called by
                │
    ┌───────────┴────────────────────┐
    │      Scheduler                 │ [4]
    │  - Celery tasks                │
    │  - Automated migration         │
    └────────────────────────────────┘
```

---

## 📊 Data Flow Diagrams

### Write Operation (Insert)

```
Client → POST /api/users
    ↓
FastAPI: create_user()
    ↓
Add timestamps:
    ├── created_at = NOW
    ├── last_login = NOW
    └── last_accessed = NOW
    ↓
query_router.insert_one('users', user_data)
    ↓
ALWAYS insert into HOT database
    ↓
hot_db.users.insert_one(user_data)
    ↓
Return: {message: "User created", id: "..."}
```

### Read Operation (Find)

```
Client → GET /api/users?limit=10
    ↓
FastAPI: list_users(limit=10, skip=0)
    ↓
query_router.find('users', {}, limit=10, skip=0)
    ↓
Query HOT database:
    └── hot_results = hot_db.users.find({}).limit(10)
    ↓
Query COLD database:
    └── cold_results = cold_db.users_archive.find({})
    ↓
Merge results:
    ├── Combine hot_results + cold_results
    ├── Apply sorting (if specified)
    ├── Apply skip
    └── Apply limit
    ↓
Return merged list
```

### Migration Operation

```
Scheduled Task / Manual Trigger
    ↓
migrator.migrate_collection('users')
    ↓
Determine policy: access_based
    ↓
Build query: {last_accessed: {$lt: 30_days_ago}}
    ↓
Find candidates in HOT:
    └── hot_db.users.find(query) → 5000 docs
    ↓
Process in batches (1000 each):
    ├── Batch 1 → cold_db.users_archive.insert_many()
    ├── Verify insertion
    ├── Delete from hot_db.users
    └── Repeat for remaining batches
    ↓
Log migration event:
    └── metrics_db.data_metrics.insert_one({
            event_type: 'migration',
            collection: 'users',
            migrated_count: 5000,
            ...
        })
```

---

## 🚀 Startup Checklist

### When System Starts:

1. ✅ **MongoDB Hot** starts and initializes
2. ✅ **MongoDB Cold** starts and initializes
3. ✅ **Django** container starts
   - Runs migrations
   - Collects static files
   - Starts Gunicorn
4. ✅ **FastAPI** container starts
   - Loads `config.py` (defines all settings)
   - Loads `router.py` (query routing logic)
   - Loads `data_metrics.py` (monitoring)
   - Connects to both MongoDB instances
   - Starts Uvicorn server
5. ✅ **Nginx** starts and routes traffic

### First Request Flow:

```
1. User → http://localhost/api/users
2. Nginx → FastAPI:8001
3. FastAPI → query_router.find()
4. Router → Queries hot_db first, then cold_db
5. Results merged and returned
```

---

## 🎓 Summary

### Execution Order:
1. **config.py** - Loaded first by all modules
2. **router.py** - Loaded at FastAPI startup
3. **migrator.py** - Loaded when migration is triggered
4. **scheduler.py** - Loaded if Celery is enabled
5. **data_metrics.py** - Loaded at FastAPI startup

### Key Principles:
- **Hot-first routing**: Always check hot DB before cold
- **Batch processing**: Migrate data in configurable batches
- **Verification**: Verify cold insertion before hot deletion
- **Monitoring**: Track all operations for analytics
- **Flexibility**: Support multiple separation policies

---

**For detailed API usage, see [README.md](README.md)**
**For implementation details, see [walkthrough.md](.gemini/antigravity/brain/*/walkthrough.md)**
