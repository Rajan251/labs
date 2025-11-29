# Quick Start Guide

Get the system running in 5 minutes.

## Prerequisites

- Ubuntu with Docker installed
- 4GB RAM minimum

## Steps

### 1. Install Docker (if not installed)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**Important:** Logout and login again for group changes to take effect.

### 2. Start Services

```bash
# Navigate to project directory
cd /home/rk/Documents/labs/lab-microservices-system-design

# Create environment file
cp .env.example .env

# Build and start all services
docker compose up -d --build

# Wait 30 seconds for services to initialize
sleep 30
```

### 3. Verify System

```bash
# Check all services are running
docker compose ps

# Test health endpoint
curl http://localhost/health
```

Expected output:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "mongodb": "connected",
    "redis": "connected",
    "rabbitmq": "connected"
  }
}
```

### 4. Test Sync Endpoint

```bash
# Create an item
curl -X POST http://localhost/api/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Item","description":"Quick test"}'

# Get all items
curl http://localhost/api/items
```

### 5. Test Async Endpoint

```bash
# Submit async task
TASK_RESPONSE=$(curl -X POST http://localhost/api/async/process \
  -H "Content-Type: application/json" \
  -d '{"data":"test task","iterations":50}')

echo $TASK_RESPONSE

# Extract task_id (requires jq)
TASK_ID=$(echo $TASK_RESPONSE | jq -r '.task_id')

# Check status (wait a few seconds)
sleep 5
curl http://localhost/api/async/status/$TASK_ID
```

## Next Steps

- **API Documentation**: http://localhost/docs
- **RabbitMQ Dashboard**: http://localhost:15672 (guest/guest)
- **View Logs**: `docker compose logs -f`
- **Read Full Guide**: [README.md](README.md)
- **Performance Tuning**: [TUNING.md](TUNING.md)

## Common Commands

```bash
# View logs
docker compose logs -f

# Stop services
docker compose down

# Restart services
docker compose restart

# Scale API instances
docker compose up -d --scale api=5

# Check resource usage
docker stats
```

## Troubleshooting

**Services won't start:**
```bash
docker compose logs
```

**Port already in use:**
```bash
sudo netstat -tulpn | grep 80
# Kill process using port 80, or change port in docker-compose.yml
```

**Out of memory:**
```bash
# Reduce replicas in docker-compose.yml
# Change: replicas: 3 → replicas: 1
docker compose up -d
```

## Architecture at a Glance

```
Client → Nginx (Port 80)
         ↓
    FastAPI (3 instances)
         ↓
    ┌────┴────┬─────────┬────────┐
    ↓         ↓         ↓        ↓
MongoDB   RabbitMQ   Redis   Celery Workers (3)
```

- **Nginx**: Load balancer + rate limiting
- **FastAPI**: API endpoints (sync + async)
- **RabbitMQ**: Message queue for async tasks
- **Celery**: Background workers
- **MongoDB**: Database
- **Redis**: Cache + task results

## Success Criteria

✅ All services show "healthy" status
✅ Health endpoint returns 200 OK
✅ Can create and retrieve items
✅ Can submit and check async tasks
✅ No errors in logs

You're ready to go! 🚀
