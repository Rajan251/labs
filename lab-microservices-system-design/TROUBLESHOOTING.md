# Troubleshooting Guide

Common issues and solutions for the production microservices system.

## 🚨 Service Startup Issues

### Problem: Services won't start

**Symptoms:**
```bash
docker compose ps
# Shows services as "Exit 1" or "Restarting"
```

**Solutions:**

1. **Check logs for specific service:**
```bash
docker compose logs mongodb
docker compose logs redis
docker compose logs rabbitmq
docker compose logs api
```

2. **Port conflicts:**
```bash
# Check if ports are already in use
sudo netstat -tulpn | grep -E '80|5672|15672|27017|6379'

# Kill process using the port
sudo kill -9 <PID>

# Or change port in docker-compose.yml
```

3. **Insufficient resources:**
```bash
# Check available memory
free -h

# Check disk space
df -h

# Solution: Stop other services or increase resources
```

4. **Permission issues:**
```bash
# Ensure user is in docker group
groups $USER

# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again
```

---

## 🔌 Connection Issues

### Problem: MongoDB connection failed

**Error in logs:**
```
pymongo.errors.ServerSelectionTimeoutError: localhost:27017: [Errno 111] Connection refused
```

**Solutions:**

1. **Check MongoDB is running:**
```bash
docker compose ps mongodb
# Should show "Up" and "healthy"
```

2. **Check MongoDB logs:**
```bash
docker compose logs mongodb
# Look for startup errors
```

3. **Restart MongoDB:**
```bash
docker compose restart mongodb

# Wait for health check
sleep 30

# Verify
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

4. **Check network connectivity:**
```bash
# From API container
docker compose exec api ping -c 3 mongodb
```

### Problem: RabbitMQ connection failed

**Error in logs:**
```
kombu.exceptions.OperationalError: [Errno 111] Connection refused
```

**Solutions:**

1. **Check RabbitMQ is running:**
```bash
docker compose ps rabbitmq
```

2. **Check RabbitMQ logs:**
```bash
docker compose logs rabbitmq
# Look for "Server startup complete"
```

3. **Verify RabbitMQ health:**
```bash
docker compose exec rabbitmq rabbitmq-diagnostics ping
docker compose exec rabbitmq rabbitmqctl status
```

4. **Check queues:**
```bash
docker compose exec rabbitmq rabbitmqctl list_queues
```

5. **Restart RabbitMQ:**
```bash
docker compose restart rabbitmq
sleep 30
```

### Problem: Redis connection failed

**Error in logs:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions:**

1. **Check Redis is running:**
```bash
docker compose ps redis
```

2. **Test Redis connection:**
```bash
docker compose exec redis redis-cli ping
# Should return "PONG"
```

3. **Check Redis logs:**
```bash
docker compose logs redis
```

4. **Restart Redis:**
```bash
docker compose restart redis
```

---

## 🔄 Task Processing Issues

### Problem: Tasks not being processed

**Symptoms:**
- Tasks stuck in PENDING status
- Queue length increasing
- No worker activity

**Solutions:**

1. **Check worker status:**
```bash
docker compose logs celery_worker

# Look for:
# - "celery@worker ready"
# - Task consumption messages
```

2. **Check worker count:**
```bash
docker compose ps | grep celery_worker
# Should show 3 workers running
```

3. **Verify RabbitMQ queues:**
```bash
# Access RabbitMQ management UI
# http://localhost:15672 (guest/guest)

# Or via CLI
docker compose exec rabbitmq rabbitmqctl list_queues name messages consumers
```

4. **Check worker connectivity:**
```bash
# Inspect Celery workers
docker compose exec celery_worker celery -A app.celery_app inspect active
docker compose exec celery_worker celery -A app.celery_app inspect stats
```

5. **Restart workers:**
```bash
docker compose restart celery_worker
```

6. **Check for task errors:**
```bash
# Look for failed tasks in logs
docker compose logs celery_worker | grep ERROR
docker compose logs celery_worker | grep FAILED
```

### Problem: Tasks timing out

**Error in logs:**
```
SoftTimeLimitExceeded: Task exceeded soft time limit
```

**Solutions:**

1. **Increase time limits in `app/celery_app.py`:**
```python
task_time_limit=600        # 10 minutes instead of 5
task_soft_time_limit=570   # 9.5 minutes
```

2. **Optimize task code:**
- Break large tasks into smaller chunks
- Use batch processing
- Add progress checkpoints

3. **Check resource constraints:**
```bash
docker stats
# Look for CPU or memory bottlenecks
```

### Problem: Tasks failing with retries exhausted

**Error in logs:**
```
MaxRetriesExceededError: Can't retry app.tasks.process_heavy_task
```

**Solutions:**

1. **Check task error details:**
```bash
docker compose logs celery_worker | grep -A 10 "Task failed"
```

2. **Increase retry count in `app/tasks.py`:**
```python
@celery_app.task(
    max_retries=5,  # Increase from 3
    default_retry_delay=120  # Increase delay
)
```

3. **Fix underlying issue:**
- Database connection issues
- Network timeouts
- Invalid input data

---

## 🌐 Nginx Issues

### Problem: 502 Bad Gateway

**Symptoms:**
```bash
curl http://localhost/api/items
# Returns: 502 Bad Gateway
```

**Solutions:**

1. **Check API containers are running:**
```bash
docker compose ps api
# All should be "Up" and "healthy"
```

2. **Check Nginx logs:**
```bash
docker compose logs nginx
# Look for upstream connection errors
```

3. **Check Nginx configuration:**
```bash
docker compose exec nginx nginx -t
# Should return "syntax is ok"
```

4. **Restart Nginx:**
```bash
docker compose restart nginx
```

5. **Check API health:**
```bash
# Direct connection to API (bypass Nginx)
docker compose exec api curl http://localhost:8000/health
```

### Problem: 429 Too Many Requests

**Symptoms:**
```bash
curl http://localhost/api/items
# Returns: 429 Too Many Requests
```

**Cause:** Rate limiting triggered (100 req/s per IP)

**Solutions:**

1. **Wait for rate limit to reset** (1 second)

2. **Increase rate limit in `nginx/nginx.conf`:**
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=200r/s;
limit_req zone=api_limit burst=400 nodelay;
```

3. **Restart Nginx:**
```bash
docker compose restart nginx
```

### Problem: Nginx not starting

**Error:**
```
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
```

**Solutions:**

1. **Find process using port 80:**
```bash
sudo netstat -tulpn | grep :80
```

2. **Stop the process:**
```bash
sudo systemctl stop apache2  # If Apache is running
# Or
sudo kill -9 <PID>
```

3. **Or change Nginx port in `docker-compose.yml`:**
```yaml
nginx:
  ports:
    - "8080:80"  # Use port 8080 instead
```

---

## 💾 Database Issues

### Problem: MongoDB running out of connections

**Error in logs:**
```
pymongo.errors.ServerSelectionTimeoutError: connection pool is full
```

**Solutions:**

1. **Check current connections:**
```bash
docker compose exec mongodb mongosh --eval "db.serverStatus().connections"
```

2. **Increase MongoDB max connections in `docker-compose.yml`:**
```yaml
mongodb:
  command: mongod --maxConns 2000  # Increase from 1000
```

3. **Reduce API connection pool size in `app/database.py`:**
```python
MongoClient(
    maxPoolSize=50,  # Reduce from 100
    minPoolSize=5
)
```

4. **Restart services:**
```bash
docker compose restart mongodb api
```

### Problem: MongoDB data lost after restart

**Cause:** Volume not properly mounted

**Solutions:**

1. **Check volumes:**
```bash
docker volume ls | grep mongodb
```

2. **Verify volume mount in `docker-compose.yml`:**
```yaml
mongodb:
  volumes:
    - mongodb_data:/data/db  # Ensure this exists
```

3. **Backup data before restart:**
```bash
docker compose exec mongodb mongodump --out /tmp/backup
docker cp $(docker compose ps -q mongodb):/tmp/backup ./backup
```

---

## 🧠 Memory Issues

### Problem: High memory usage

**Symptoms:**
```bash
docker stats
# Shows containers using >80% memory
```

**Solutions:**

1. **Reduce worker concurrency in `docker-compose.yml`:**
```yaml
celery_worker:
  command: celery -A app.celery_app worker --concurrency=2  # Reduce from 4
```

2. **Reduce number of replicas:**
```yaml
api:
  deploy:
    replicas: 2  # Reduce from 3
```

3. **Set memory limits in `docker-compose.yml`:**
```yaml
api:
  deploy:
    resources:
      limits:
        memory: 512M
```

4. **Increase system swap:**
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Problem: Redis out of memory

**Error in logs:**
```
OOM command not allowed when used memory > 'maxmemory'
```

**Solutions:**

1. **Increase Redis max memory in `docker-compose.yml`:**
```yaml
redis:
  command: redis-server --maxmemory 1gb  # Increase from 512mb
```

2. **Clear Redis cache:**
```bash
docker compose exec redis redis-cli FLUSHALL
```

3. **Check eviction policy:**
```bash
docker compose exec redis redis-cli CONFIG GET maxmemory-policy
# Should be "allkeys-lru"
```

---

## 🔍 Debugging Tips

### Enable debug logging

**In `.env`:**
```bash
LOG_LEVEL=DEBUG
```

**Restart services:**
```bash
docker compose restart api celery_worker
```

### View real-time logs

```bash
# All services
docker compose logs -f

# Specific service with timestamps
docker compose logs -f --timestamps api

# Last 100 lines
docker compose logs --tail=100 celery_worker
```

### Inspect container

```bash
# Get shell access
docker compose exec api bash

# Check environment variables
docker compose exec api env

# Check running processes
docker compose exec api ps aux
```

### Network debugging

```bash
# Test connectivity between containers
docker compose exec api ping mongodb
docker compose exec api ping redis
docker compose exec api ping rabbitmq

# Check DNS resolution
docker compose exec api nslookup mongodb
```

### Database debugging

```bash
# MongoDB shell
docker compose exec mongodb mongosh

# Check database size
use myapp
db.stats()

# Find slow queries
db.setProfilingLevel(2)
db.system.profile.find().pretty()

# Check indexes
db.items.getIndexes()
```

---

## 🔄 Recovery Procedures

### Complete system restart

```bash
# Stop all services
docker compose down

# Remove volumes (WARNING: deletes data)
docker compose down -v

# Clean up
docker system prune -f

# Rebuild and start
docker compose build --no-cache
docker compose up -d

# Wait for health checks
sleep 60

# Verify
docker compose ps
curl http://localhost/health
```

### Restart single service

```bash
# Restart without downtime (if multiple replicas)
docker compose restart api

# Force recreate
docker compose up -d --force-recreate api
```

### Rollback changes

```bash
# Revert to previous image
docker compose down
git checkout HEAD~1 docker-compose.yml
docker compose up -d
```

---

## 📊 Performance Debugging

### High CPU usage

```bash
# Find CPU-intensive container
docker stats --no-stream | sort -k 3 -h

# Check processes inside container
docker compose exec api top

# Reduce worker concurrency
# Edit docker-compose.yml and restart
```

### Slow API responses

```bash
# Check API logs for slow queries
docker compose logs api | grep -i "slow"

# Monitor MongoDB queries
docker compose exec mongodb mongosh
use myapp
db.setProfilingLevel(1, { slowms: 100 })
db.system.profile.find().sort({ts:-1}).limit(5).pretty()

# Add database indexes
db.items.createIndex({ created_at: -1 })
```

### Queue backlog

```bash
# Check queue length
docker compose exec rabbitmq rabbitmqctl list_queues

# Increase workers
docker compose up -d --scale celery_worker=5

# Increase worker concurrency
# Edit docker-compose.yml: --concurrency=8
docker compose restart celery_worker
```

---

## 🆘 Emergency Contacts

### Critical failure recovery

1. **Stop all services:**
```bash
docker compose down
```

2. **Backup data:**
```bash
docker volume ls
docker run --rm -v mongodb_data:/data -v $(pwd):/backup ubuntu tar czf /backup/mongodb_backup.tar.gz /data
```

3. **Check system resources:**
```bash
free -h
df -h
docker system df
```

4. **Clean up:**
```bash
docker system prune -a --volumes
```

5. **Restore from backup and restart**

---

## 📞 Getting Help

**Before asking for help, collect:**

1. **System info:**
```bash
docker --version
docker compose version
uname -a
free -h
df -h
```

2. **Service status:**
```bash
docker compose ps
docker compose logs > logs.txt
```

3. **Error messages:**
```bash
docker compose logs | grep -i error > errors.txt
```

4. **Configuration:**
```bash
cat docker-compose.yml
cat .env
```

**Include in your support request:**
- What you were trying to do
- What happened instead
- Error messages
- System information
- Steps to reproduce

---

## ✅ Health Check Checklist

Run this checklist to verify system health:

```bash
# 1. All services running
docker compose ps
# Expected: All "Up" and "healthy"

# 2. Health endpoint
curl http://localhost/health
# Expected: status "healthy"

# 3. API endpoint
curl http://localhost/api/items
# Expected: 200 OK

# 4. MongoDB connection
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"
# Expected: { ok: 1 }

# 5. Redis connection
docker compose exec redis redis-cli ping
# Expected: PONG

# 6. RabbitMQ status
docker compose exec rabbitmq rabbitmqctl status
# Expected: Status of node...

# 7. Worker status
docker compose exec celery_worker celery -A app.celery_app inspect ping
# Expected: pong from workers

# 8. Resource usage
docker stats --no-stream
# Expected: All <80% CPU and memory

# 9. No errors in logs
docker compose logs --tail=100 | grep -i error
# Expected: No critical errors

# 10. Test async task
curl -X POST http://localhost/api/async/process \
  -H "Content-Type: application/json" \
  -d '{"data":"test","iterations":10}'
# Expected: task_id returned
```

If all checks pass: ✅ System is healthy!
