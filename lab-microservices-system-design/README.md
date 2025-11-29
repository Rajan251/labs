# Production-Ready Microservices Architecture

A robust, production-grade microservices system built with Docker, designed to handle high concurrency without freezing or crashes.

## 🏗️ Architecture

```
┌─────────────┐
│   Clients   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Nginx (Load Balancer + Rate Limit) │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌──────────┐    ┌──────────┐
│ FastAPI  │    │ FastAPI  │  (3 replicas)
│   API    │    │   API    │
└────┬─────┘    └────┬─────┘
     │               │
     ├───────┬───────┴──────┬──────────┐
     ▼       ▼              ▼          ▼
┌─────────┐ ┌──────────┐ ┌──────┐ ┌────────┐
│ MongoDB │ │ RabbitMQ │ │ Redis│ │ Celery │
│         │ │          │ │      │ │ Worker │ (3 replicas)
└─────────┘ └──────────┘ └──────┘ └────────┘
```

## 🚀 Features

- **High Concurrency**: Handles thousands of concurrent requests without freezing
- **Async Processing**: Heavy operations processed by background workers
- **Load Balancing**: Nginx distributes traffic across multiple API instances
- **Rate Limiting**: Prevents system overload from single clients
- **Auto-Scaling**: Multiple replicas of API and workers
- **Health Checks**: All services monitored with automatic restarts
- **Connection Pooling**: Optimized database and cache connections
- **Graceful Degradation**: System continues operating even if components fail

## 📋 Prerequisites

- Ubuntu 20.04+ (or any Linux with Docker support)
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM recommended
- 2+ CPU cores recommended

## 🛠️ Installation

### 1. Install Docker and Docker Compose

```bash
# Update package index
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (logout/login required)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### 2. Clone/Setup Project

```bash
# Navigate to project directory
cd /home/rk/Documents/labs/lab-microservices-system-design

# Create .env file from example
cp .env.example .env

# Edit .env if needed (optional for local testing)
nano .env
```

### 3. Build and Start Services

```bash
# Build Docker images
docker compose build

# Start all services in background
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### 4. Verify Services

```bash
# Check health endpoint
curl http://localhost/health

# Expected output:
# {
#   "status": "healthy",
#   "timestamp": "2024-01-01T00:00:00Z",
#   "services": {
#     "mongodb": "connected",
#     "redis": "connected",
#     "rabbitmq": "connected"
#   }
# }
```

## 📚 API Endpoints

### Health Check
```bash
GET /health
```

### Sync Endpoints (Fast, Direct Database)

**Get All Items:**
```bash
curl http://localhost/api/items
```

**Create Item:**
```bash
curl -X POST http://localhost/api/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Item",
    "description": "This is a test item",
    "metadata": {"category": "test"}
  }'
```

**Get Single Item:**
```bash
curl http://localhost/api/items/{item_id}
```

### Async Endpoints (Heavy Processing via Queue)

**Submit Async Task:**
```bash
curl -X POST http://localhost/api/async/process \
  -H "Content-Type: application/json" \
  -d '{
    "data": "heavy processing task",
    "iterations": 100,
    "priority": "high"
  }'

# Response:
# {
#   "task_id": "a7f8c9d0-1234-5678-9abc-def012345678",
#   "status": "PENDING",
#   "message": "Task submitted successfully..."
# }
```

**Check Task Status:**
```bash
# Replace {task_id} with actual task ID from previous response
curl http://localhost/api/async/status/{task_id}

# Response (in progress):
# {
#   "task_id": "a7f8c9d0-1234-5678-9abc-def012345678",
#   "status": "PROGRESS",
#   "progress": {"current": 50, "total": 100, "progress": 50}
# }

# Response (completed):
# {
#   "task_id": "a7f8c9d0-1234-5678-9abc-def012345678",
#   "status": "SUCCESS",
#   "result": {
#     "processed_items": [...],
#     "total_processed": 100
#   }
# }
```

## 🔍 Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f celery_worker
docker compose logs -f nginx
docker compose logs -f mongodb
docker compose logs -f redis
docker compose logs -f rabbitmq
```

### RabbitMQ Management UI

Access at: http://localhost:15672
- Username: `guest`
- Password: `guest`

Monitor queues, message rates, and worker connections.

### Container Stats

```bash
# Real-time resource usage
docker stats

# Service status
docker compose ps
```

### MongoDB Shell

```bash
# Connect to MongoDB
docker compose exec mongodb mongosh

# Use database
use myapp

# View collections
show collections

# Query items
db.items.find().pretty()

# Query task results
db.task_results.find().pretty()
```

### Redis CLI

```bash
# Connect to Redis
docker compose exec redis redis-cli

# View all keys
KEYS *

# Get task result
GET celery-task-meta-{task_id}

# Monitor commands
MONITOR
```

## 🧪 Load Testing

### Install Apache Bench

```bash
sudo apt-get install apache2-utils
```

### Test Health Endpoint

```bash
# 10,000 requests, 100 concurrent
ab -n 10000 -c 100 http://localhost/health
```

### Test API Endpoint

```bash
# 1,000 requests, 50 concurrent
ab -n 1000 -c 50 http://localhost/api/items
```

### Test Async Endpoint

```bash
# Create test file
echo '{"data":"test","iterations":10}' > test.json

# POST requests
ab -n 100 -c 10 -p test.json -T application/json \
  http://localhost/api/async/process
```

## 🛑 Stopping Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v

# Stop specific service
docker compose stop api
```

## 🔄 Updating Code

```bash
# After code changes, rebuild and restart
docker compose build
docker compose up -d

# Or rebuild specific service
docker compose build api
docker compose up -d api
```

## 📊 Scaling

### Scale API Instances

```bash
# Scale to 5 API instances
docker compose up -d --scale api=5

# Nginx will automatically load balance across all instances
```

### Scale Workers

```bash
# Scale to 5 worker instances
docker compose up -d --scale celery_worker=5
```

## 🔧 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose logs {service_name}

# Check if port is already in use
sudo netstat -tulpn | grep {port}

# Restart specific service
docker compose restart {service_name}
```

### MongoDB Connection Issues

```bash
# Check MongoDB is running
docker compose ps mongodb

# Check MongoDB logs
docker compose logs mongodb

# Test connection
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### RabbitMQ Connection Issues

```bash
# Check RabbitMQ is running
docker compose ps rabbitmq

# Check RabbitMQ logs
docker compose logs rabbitmq

# Check queues
docker compose exec rabbitmq rabbitmqctl list_queues
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Restart services to free memory
docker compose restart

# Reduce worker concurrency in docker-compose.yml:
# --concurrency=2 (instead of 4)
```

### Tasks Not Processing

```bash
# Check worker logs
docker compose logs celery_worker

# Check RabbitMQ queues
# Access http://localhost:15672

# Restart workers
docker compose restart celery_worker
```

## 📁 Project Structure

```
.
├── docker-compose.yml          # All services configuration
├── Dockerfile.app              # FastAPI app container
├── .env.example                # Environment variables template
├── .dockerignore               # Docker build exclusions
├── requirements.txt            # Python dependencies
├── nginx/
│   ├── nginx.conf             # Nginx configuration
│   └── logs/                  # Nginx logs
└── app/
    ├── __init__.py            # Package init
    ├── main.py                # FastAPI application
    ├── models.py              # Pydantic models
    ├── database.py            # MongoDB connection
    ├── celery_app.py          # Celery configuration
    └── tasks.py               # Celery tasks
```

## 🎯 Key Performance Settings

See [TUNING.md](TUNING.md) for detailed tuning guide.

### Nginx
- **Workers**: Auto (CPU cores)
- **Connections**: 10,000 per worker
- **Rate Limit**: 100 req/s per IP

### Celery
- **Concurrency**: 4 workers per container
- **Prefetch**: 1 task at a time
- **Max Retries**: 3

### MongoDB
- **Max Connections**: 1,000
- **Pool Size**: 10-100 per API instance

### Redis
- **Max Memory**: 512MB
- **Eviction**: LRU (Least Recently Used)

## 📖 API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost/docs
- ReDoc: http://localhost/redoc

## 🔒 Security Notes

For production deployment:

1. **Change default passwords** in `.env`
2. **Enable SSL/TLS** in Nginx
3. **Use secrets management** (Docker secrets, Vault)
4. **Restrict network access** (firewall rules)
5. **Enable authentication** on RabbitMQ and MongoDB
6. **Use environment-specific configs**
7. **Regular security updates** for base images

## 📝 License

This is a production-ready template for educational and commercial use.

## 🤝 Support

For issues or questions, check:
- Container logs: `docker compose logs`
- Service status: `docker compose ps`
- Resource usage: `docker stats`
