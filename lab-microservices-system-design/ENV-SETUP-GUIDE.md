# 🔧 Environment Configuration Step-by-Step Guide

## 📋 Overview

This guide explains **every single step** to create and configure your environment variables for the microservices system using Redis, RabbitMQ, and Celery.

---

## 🎯 What You'll Configure

Your `.env` file controls:
- ✅ **MongoDB** - Database connection
- ✅ **Redis** - Cache and task results storage
- ✅ **RabbitMQ** - Message queue (task broker)
- ✅ **Celery** - Background task processing
- ✅ **API** - FastAPI server settings
- ✅ **Security** - Authentication and CORS

---

## 📝 Step-by-Step Configuration

### Step 1: Create Your Environment File

```bash
# Navigate to project directory
cd /home/rk/Documents/labs/lab-microservices-system-design

# Copy the example file to create your actual .env file
cp .env.example .env

# Verify it was created
ls -la .env
```

**What this does:** Creates your actual `.env` file from the template

---

### Step 2: Understand Each Configuration Section

Open the `.env` file:
```bash
nano .env
# or use your preferred editor
```

---

### 📦 Section 1: MongoDB Configuration

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DB_NAME=myapp
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10
```

#### What Each Variable Means:

| Variable | Purpose | Example Value | When to Change |
|----------|---------|---------------|----------------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://mongodb:27017` | Use external MongoDB: `mongodb://user:pass@host:27017` |
| `MONGODB_DB_NAME` | Database name | `myapp` | Change to your app name: `production_db` |
| `MONGODB_MAX_POOL_SIZE` | Max concurrent connections | `100` | High traffic: increase to `200-500` |
| `MONGODB_MIN_POOL_SIZE` | Min idle connections | `10` | Low traffic: decrease to `5` |

#### Common Scenarios:

**Development (Default):**
```bash
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DB_NAME=myapp_dev
MONGODB_MAX_POOL_SIZE=50
MONGODB_MIN_POOL_SIZE=5
```

**Production (External MongoDB):**
```bash
MONGODB_URL=mongodb://admin:SecurePass123@mongodb.example.com:27017/myapp?authSource=admin
MONGODB_DB_NAME=myapp_production
MONGODB_MAX_POOL_SIZE=200
MONGODB_MIN_POOL_SIZE=20
```

**MongoDB Atlas (Cloud):**
```bash
MONGODB_URL=mongodb+srv://username:password@cluster0.mongodb.net/myapp?retryWrites=true&w=majority
MONGODB_DB_NAME=myapp_production
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10
```

---

### 🔴 Section 2: Redis Configuration

```bash
# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=50
```

#### What Each Variable Means:

| Variable | Purpose | Example Value | When to Change |
|----------|---------|---------------|----------------|
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` | External Redis: `redis://user:pass@host:6379/0` |
| `REDIS_MAX_CONNECTIONS` | Max connection pool size | `50` | High traffic: increase to `100-200` |

#### Database Numbers in Redis:

Redis has 16 databases (0-15). We use:
- **Database 0** (`/0`) - General caching and rate limiting
- **Database 1** (`/1`) - Celery task results (configured below)

#### Common Scenarios:

**Development (Default):**
```bash
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=50
```

**Production (External Redis with Password):**
```bash
REDIS_URL=redis://:YourRedisPassword@redis.example.com:6379/0
REDIS_MAX_CONNECTIONS=100
```

**Redis Cloud:**
```bash
REDIS_URL=redis://default:password@redis-12345.cloud.redislabs.com:12345/0
REDIS_MAX_CONNECTIONS=100
```

---

### 🐰 Section 3: RabbitMQ Configuration

```bash
# RabbitMQ Configuration
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672//
```

#### What This Variable Means:

| Variable | Purpose | Format | When to Change |
|----------|---------|--------|----------------|
| `RABBITMQ_URL` | RabbitMQ connection string | `amqp://user:pass@host:port//` | Production: change credentials |

#### URL Format Breakdown:

```
amqp://guest:guest@rabbitmq:5672//
  │     │     │      │        │    │
  │     │     │      │        │    └─ Virtual host (// = default)
  │     │     │      │        └────── Port (5672 = default)
  │     │     │      └─────────────── Hostname
  │     │     └────────────────────── Password
  │     └──────────────────────────── Username
  └────────────────────────────────── Protocol
```

#### Common Scenarios:

**Development (Default):**
```bash
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672//
```

**Production (Custom Credentials):**
```bash
RABBITMQ_URL=amqp://admin:SecureRabbitPass123@rabbitmq:5672//
```

**External RabbitMQ:**
```bash
RABBITMQ_URL=amqp://myuser:mypass@rabbitmq.example.com:5672/production
```

**CloudAMQP (Cloud RabbitMQ):**
```bash
RABBITMQ_URL=amqp://username:password@jellyfish.rmq.cloudamqp.com/username
```

---

### ⚙️ Section 4: Celery Configuration

```bash
# Celery Configuration
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true
```

#### What Each Variable Means:

| Variable | Purpose | Example Value | When to Change |
|----------|---------|---------------|----------------|
| `CELERY_BROKER_URL` | Where tasks are queued | `amqp://guest:guest@rabbitmq:5672//` | Must match `RABBITMQ_URL` |
| `CELERY_RESULT_BACKEND` | Where results are stored | `redis://redis:6379/1` | Use different Redis DB (`/1`, `/2`, etc.) |
| `CELERY_TASK_SERIALIZER` | How tasks are encoded | `json` | Use `pickle` for complex objects (less secure) |
| `CELERY_RESULT_SERIALIZER` | How results are encoded | `json` | Use `pickle` for complex objects (less secure) |
| `CELERY_ACCEPT_CONTENT` | Accepted formats | `json` | Add `pickle` if needed |
| `CELERY_TIMEZONE` | Timezone for scheduled tasks | `UTC` | Change to `America/New_York`, `Asia/Kolkata`, etc. |
| `CELERY_ENABLE_UTC` | Use UTC timestamps | `true` | Keep `true` for consistency |

#### Why Two URLs?

```
CELERY_BROKER_URL      → RabbitMQ → Stores PENDING tasks (queue)
CELERY_RESULT_BACKEND  → Redis    → Stores COMPLETED results (cache)
```

**Flow:**
1. Task submitted → Stored in **RabbitMQ** (broker)
2. Worker picks up task → Processes it
3. Result saved → Stored in **Redis** (backend)

#### Common Scenarios:

**Development (Default):**
```bash
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true
```

**Production (External Services):**
```bash
CELERY_BROKER_URL=amqp://admin:SecurePass@rabbitmq.example.com:5672//
CELERY_RESULT_BACKEND=redis://:RedisPass@redis.example.com:6379/1
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=America/New_York
CELERY_ENABLE_UTC=true
```

**India Timezone:**
```bash
CELERY_TIMEZONE=Asia/Kolkata
```

---

### 🚀 Section 5: API Configuration

```bash
# API Configuration
LOG_LEVEL=INFO
WORKERS_PER_CORE=2
MAX_WORKERS=4
API_TITLE=Production Microservices API
API_VERSION=1.0.0
```

#### What Each Variable Means:

| Variable | Purpose | Example Value | When to Change |
|----------|---------|---------------|----------------|
| `LOG_LEVEL` | Logging verbosity | `INFO` | Debug: `DEBUG`, Production: `WARNING` |
| `WORKERS_PER_CORE` | Uvicorn workers per CPU core | `2` | High traffic: `4`, Low traffic: `1` |
| `MAX_WORKERS` | Maximum total workers | `4` | Server with 8 cores: `16` |
| `API_TITLE` | API documentation title | `Production Microservices API` | Change to your app name |
| `API_VERSION` | API version | `1.0.0` | Increment on releases |

#### Log Levels Explained:

| Level | What It Shows | When to Use |
|-------|---------------|-------------|
| `DEBUG` | Everything (very verbose) | Development, troubleshooting |
| `INFO` | General information | Development, staging |
| `WARNING` | Warnings and errors | Production (recommended) |
| `ERROR` | Only errors | Production (minimal logs) |

#### Worker Calculation:

```bash
# Formula: (CPU cores × WORKERS_PER_CORE) = Total workers
# But capped at MAX_WORKERS

# Example: 4-core server
WORKERS_PER_CORE=2
MAX_WORKERS=8
# Result: 4 cores × 2 = 8 workers (matches MAX_WORKERS)

# Example: 8-core server
WORKERS_PER_CORE=2
MAX_WORKERS=12
# Result: 8 cores × 2 = 16, but capped at MAX_WORKERS=12
```

#### Common Scenarios:

**Development:**
```bash
LOG_LEVEL=DEBUG
WORKERS_PER_CORE=1
MAX_WORKERS=2
API_TITLE=MyApp Development API
API_VERSION=0.1.0
```

**Production (Small Server - 2 cores):**
```bash
LOG_LEVEL=WARNING
WORKERS_PER_CORE=2
MAX_WORKERS=4
API_TITLE=MyApp Production API
API_VERSION=1.0.0
```

**Production (Large Server - 8 cores):**
```bash
LOG_LEVEL=WARNING
WORKERS_PER_CORE=4
MAX_WORKERS=32
API_TITLE=MyApp Production API
API_VERSION=1.0.0
```

---

### 🛡️ Section 6: Rate Limiting

```bash
# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

#### What This Variable Means:

| Variable | Purpose | Example Value | When to Change |
|----------|---------|---------------|----------------|
| `RATE_LIMIT_PER_MINUTE` | Max requests per user per minute | `100` | Strict: `50`, Lenient: `200` |

#### Common Scenarios:

**Development (No limit):**
```bash
RATE_LIMIT_PER_MINUTE=1000
```

**Production (Moderate):**
```bash
RATE_LIMIT_PER_MINUTE=100
```

**Production (Strict):**
```bash
RATE_LIMIT_PER_MINUTE=50
```

**Public API (Very Strict):**
```bash
RATE_LIMIT_PER_MINUTE=30
```

---

### 🔐 Section 7: Security Configuration

```bash
# Security (change in production!)
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_ORIGINS=http://localhost,http://localhost:80
```

#### What Each Variable Means:

| Variable | Purpose | Example Value | When to Change |
|----------|---------|---------------|----------------|
| `SECRET_KEY` | JWT token signing key | Random string | **ALWAYS change in production!** |
| `ALLOWED_ORIGINS` | CORS allowed domains | `http://localhost,https://myapp.com` | Add your frontend domains |

#### ⚠️ CRITICAL: Generate Secure SECRET_KEY

**Never use the default in production!**

**Generate a secure key:**

```bash
# Method 1: Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Method 2: Using OpenSSL
openssl rand -hex 32

# Method 3: Using /dev/urandom
cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1
```

**Example output:**
```
xK9mP2vL8nQ4wR7tY6uI3oP5aS1dF0gH2jK4lM6nB8vC3xZ9qW7eR5tY3uI1oP0a
```

**Use it:**
```bash
SECRET_KEY=xK9mP2vL8nQ4wR7tY6uI3oP5aS1dF0gH2jK4lM6nB8vC3xZ9qW7eR5tY3uI1oP0a
```

#### CORS Configuration:

**Development:**
```bash
ALLOWED_ORIGINS=http://localhost,http://localhost:3000,http://localhost:8080
```

**Production:**
```bash
ALLOWED_ORIGINS=https://myapp.com,https://www.myapp.com,https://api.myapp.com
```

**Allow All (NOT RECOMMENDED):**
```bash
ALLOWED_ORIGINS=*
```

---

### 🌍 Section 8: Environment

```bash
# Environment
ENVIRONMENT=production
```

#### What This Variable Means:

| Variable | Purpose | Example Value | When to Change |
|----------|---------|---------------|----------------|
| `ENVIRONMENT` | Deployment environment | `production` | Use `development`, `staging`, or `production` |

#### Common Values:

```bash
# Development
ENVIRONMENT=development

# Staging
ENVIRONMENT=staging

# Production
ENVIRONMENT=production
```

---

## 🎯 Step 3: Complete Configuration Examples

### Development Environment

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DB_NAME=myapp_dev
MONGODB_MAX_POOL_SIZE=50
MONGODB_MIN_POOL_SIZE=5

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=50

# RabbitMQ Configuration
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672//

# Celery Configuration
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true

# API Configuration
LOG_LEVEL=DEBUG
WORKERS_PER_CORE=1
MAX_WORKERS=2
API_TITLE=MyApp Development API
API_VERSION=0.1.0

# Rate Limiting
RATE_LIMIT_PER_MINUTE=1000

# Security
SECRET_KEY=dev-secret-key-not-for-production
ALLOWED_ORIGINS=http://localhost,http://localhost:3000

# Environment
ENVIRONMENT=development
```

---

### Production Environment

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://admin:SecureMongoPass123@mongodb.example.com:27017/myapp?authSource=admin
MONGODB_DB_NAME=myapp_production
MONGODB_MAX_POOL_SIZE=200
MONGODB_MIN_POOL_SIZE=20

# Redis Configuration
REDIS_URL=redis://:SecureRedisPass123@redis.example.com:6379/0
REDIS_MAX_CONNECTIONS=100

# RabbitMQ Configuration
RABBITMQ_URL=amqp://admin:SecureRabbitPass123@rabbitmq.example.com:5672//

# Celery Configuration
CELERY_BROKER_URL=amqp://admin:SecureRabbitPass123@rabbitmq.example.com:5672//
CELERY_RESULT_BACKEND=redis://:SecureRedisPass123@redis.example.com:6379/1
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true

# API Configuration
LOG_LEVEL=WARNING
WORKERS_PER_CORE=4
MAX_WORKERS=16
API_TITLE=MyApp Production API
API_VERSION=1.0.0

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Security (CHANGE THESE!)
SECRET_KEY=xK9mP2vL8nQ4wR7tY6uI3oP5aS1dF0gH2jK4lM6nB8vC3xZ9qW7eR5tY3uI1oP0a
ALLOWED_ORIGINS=https://myapp.com,https://www.myapp.com

# Environment
ENVIRONMENT=production
```

---

## ✅ Step 4: Verify Your Configuration

### Test Configuration Loading

```bash
# Start services
docker compose up -d

# Check if environment variables are loaded
docker compose exec api env | grep MONGODB
docker compose exec api env | grep REDIS
docker compose exec api env | grep RABBITMQ
docker compose exec api env | grep CELERY
```

### Test Connections

```bash
# Test health endpoint
curl http://localhost/health

# Expected response:
# {
#   "status": "healthy",
#   "services": {
#     "mongodb": "connected",
#     "redis": "connected",
#     "rabbitmq": "connected"
#   }
# }
```

---

## 🔧 Step 5: Troubleshooting

### Issue: Services Can't Connect

**Symptom:**
```json
{
  "status": "unhealthy",
  "services": {
    "mongodb": "disconnected"
  }
}
```

**Solutions:**

1. **Check if services are running:**
```bash
docker compose ps
```

2. **Check service logs:**
```bash
docker compose logs mongodb
docker compose logs redis
docker compose logs rabbitmq
```

3. **Verify environment variables:**
```bash
docker compose exec api env | grep MONGODB_URL
```

4. **Test connection manually:**
```bash
# MongoDB
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Redis
docker compose exec redis redis-cli ping

# RabbitMQ
docker compose exec rabbitmq rabbitmqctl status
```

---

### Issue: Wrong Database Used

**Symptom:** Data not appearing in expected database

**Solution:**

1. **Check current database:**
```bash
docker compose exec mongodb mongosh --eval "db.getName()"
```

2. **Verify MONGODB_DB_NAME:**
```bash
docker compose exec api env | grep MONGODB_DB_NAME
```

3. **Restart services:**
```bash
docker compose down
docker compose up -d
```

---

### Issue: Celery Tasks Not Processing

**Symptom:** Tasks stuck in PENDING state

**Solutions:**

1. **Check Celery worker logs:**
```bash
docker compose logs celery_worker
```

2. **Verify broker connection:**
```bash
docker compose exec celery_worker celery -A app.celery_app inspect ping
```

3. **Check RabbitMQ queue:**
```bash
# Open RabbitMQ Management UI
http://localhost:15672
# Login: guest / guest
# Check Queues tab
```

4. **Verify CELERY_BROKER_URL matches RABBITMQ_URL:**
```bash
docker compose exec api env | grep BROKER
docker compose exec api env | grep RABBITMQ
```

---

## 📚 Next Steps

1. ✅ **Configuration Complete** - Your `.env` file is ready
2. 📖 **Read:** `QUICKSTART.md` - Quick start guide
3. 🚀 **Deploy:** `DEPLOY-00-MASTER-CHECKLIST.md` - Deployment checklist
4. 🔍 **Monitor:** `TUNING.md` - Performance tuning
5. 🐛 **Debug:** `TROUBLESHOOTING.md` - Common issues

---

## 🎓 Key Takeaways

1. **Never commit `.env` to git** - Use `.env.example` as template
2. **Always change SECRET_KEY in production** - Generate secure random keys
3. **Use strong passwords** - Especially for production databases
4. **Match broker URLs** - `RABBITMQ_URL` and `CELERY_BROKER_URL` must be identical
5. **Use different Redis databases** - `/0` for cache, `/1` for Celery results
6. **Configure CORS properly** - Only allow trusted domains
7. **Set appropriate rate limits** - Protect your API from abuse
8. **Use UTC timezone** - Avoid timezone-related bugs

---

## 📞 Need Help?

- **Quick Start:** See `QUICKSTART.md`
- **Troubleshooting:** See `TROUBLESHOOTING.md`
- **Full Guide:** See `BEGINNER-COMPLETE-GUIDE.md`
- **Deployment:** See `DEPLOY-00-MASTER-CHECKLIST.md`
