# Performance Tuning Guide

This guide explains key performance settings and how they prevent freezing under high load.

## 🎯 Overview

The system is designed to handle high concurrency through:
1. **Load balancing** across multiple API instances
2. **Async processing** for heavy operations
3. **Connection pooling** for database and cache
4. **Rate limiting** to prevent overload
5. **Proper timeouts** and retry logic

## 🔧 Nginx Tuning

### Worker Processes

```nginx
worker_processes auto;  # Auto-detect CPU cores
```

**Why it matters:**
- Each worker can handle thousands of connections
- Auto-detection ensures optimal CPU utilization
- On 4-core system: 4 workers × 10,000 connections = 40,000 concurrent connections

### Worker Connections

```nginx
worker_connections 10000;
```

**Why it matters:**
- Defines max concurrent connections per worker
- Higher value = more concurrent users
- Limited by system's `ulimit` (see System Tuning below)

**Recommendation:**
- Development: 1024
- Production: 10000+
- High-traffic: 20000+

### Event Mechanism

```nginx
use epoll;
multi_accept on;
```

**Why it matters:**
- `epoll` is Linux's efficient event notification mechanism
- `multi_accept` allows accepting multiple connections at once
- Reduces CPU usage and latency

### Request Buffering

```nginx
proxy_request_buffering off;
proxy_buffering off;
```

**Why it matters:**
- Disables buffering for real-time responses
- Reduces memory usage
- Prevents freezing on large requests
- Critical for streaming responses

**Trade-off:**
- Slightly higher backend load
- Better user experience (no waiting for buffering)

### Rate Limiting

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
limit_req zone=api_limit burst=200 nodelay;
```

**Why it matters:**
- Prevents single client from overwhelming system
- 100 requests/second baseline
- Burst of 200 for traffic spikes
- `nodelay` processes burst immediately

**Tuning:**
```nginx
# Strict (low-traffic API)
rate=10r/s burst=20

# Normal (typical API)
rate=100r/s burst=200

# Permissive (high-traffic API)
rate=500r/s burst=1000
```

### Timeouts

```nginx
proxy_connect_timeout 60s;
proxy_send_timeout 120s;
proxy_read_timeout 120s;
```

**Why it matters:**
- Prevents hanging connections
- Frees resources for new requests
- Adjust based on your slowest endpoint

**Recommendation:**
- Fast APIs: 30s
- Normal APIs: 60-120s
- Long-running: 300s (5 min)

## 🐍 Celery Tuning

### Worker Concurrency

```bash
celery -A app.celery_app worker --concurrency=4
```

**Why it matters:**
- Number of parallel tasks per worker
- Higher = more throughput
- Too high = resource contention

**Formula:**
```
Concurrency = (CPU cores × 2) + 1
```

**Examples:**
- 2 cores: `--concurrency=5`
- 4 cores: `--concurrency=9`
- 8 cores: `--concurrency=17`

**For I/O-bound tasks:**
```bash
--concurrency=20  # Can be higher
```

**For CPU-bound tasks:**
```bash
--concurrency=4   # Match CPU cores
```

### Prefetch Multiplier

```python
worker_prefetch_multiplier=1
```

**Why it matters:**
- Controls how many tasks worker fetches ahead
- `1` = fair distribution (one task at a time)
- Higher = better throughput, unfair distribution

**Recommendation:**
- Short tasks: `4`
- Mixed tasks: `2`
- Long tasks: `1` (prevents worker hogging)

### Task Acknowledgment

```python
task_acks_late=True
task_reject_on_worker_lost=True
```

**Why it matters:**
- `acks_late=True`: Task acknowledged AFTER completion
- If worker crashes, task is retried
- Prevents data loss

**Trade-off:**
- Slightly lower throughput
- Much higher reliability

### Time Limits

```python
task_time_limit=300        # Hard timeout: 5 minutes
task_soft_time_limit=270   # Soft timeout: 4.5 minutes
```

**Why it matters:**
- Prevents runaway tasks
- Soft limit raises exception (graceful cleanup)
- Hard limit kills task (forced termination)

**Recommendation:**
```python
# Fast tasks
task_time_limit=60
task_soft_time_limit=50

# Normal tasks
task_time_limit=300
task_soft_time_limit=270

# Long tasks
task_time_limit=3600
task_soft_time_limit=3540
```

### Max Tasks Per Child

```python
worker_max_tasks_per_child=1000
```

**Why it matters:**
- Worker restarts after processing N tasks
- Prevents memory leaks
- Keeps workers fresh

**Recommendation:**
- Memory-intensive: `100`
- Normal: `1000`
- Lightweight: `10000`

### Retry Configuration

```python
max_retries=3
default_retry_delay=60
retry_backoff=True
retry_backoff_max=600
```

**Why it matters:**
- Handles transient failures
- Exponential backoff prevents thundering herd
- Max backoff caps retry delay

**Example backoff:**
- Retry 1: 60s
- Retry 2: 120s
- Retry 3: 240s

## 🗄️ MongoDB Tuning

### Connection Pooling

```python
MongoClient(
    maxPoolSize=100,
    minPoolSize=10,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000
)
```

**Why it matters:**
- Reuses connections (no overhead)
- `maxPoolSize`: Max connections per client
- `minPoolSize`: Always-ready connections

**Formula:**
```
maxPoolSize = (API instances × workers per instance) + buffer
```

**Example:**
- 3 API instances × 4 workers = 12
- Add 20% buffer = 15
- Recommended: 20-50

**System limit:**
```bash
# MongoDB default max connections: 1000
# Set in docker-compose.yml:
command: mongod --maxConns 1000
```

### Timeouts

```python
serverSelectionTimeoutMS=5000   # 5s to find server
connectTimeoutMS=10000          # 10s to connect
socketTimeoutMS=10000           # 10s for operations
```

**Why it matters:**
- Prevents hanging on database issues
- Fails fast, allowing retries
- Frees resources quickly

### Write Concern

```python
w='majority'
journal=True
```

**Why it matters:**
- `w='majority'`: Wait for majority of replicas
- `journal=True`: Wait for disk write
- Ensures data durability

**Trade-off:**
- Slower writes
- Higher reliability

**For high throughput:**
```python
w=1           # Only primary
journal=False # Don't wait for disk
```

## 🔴 Redis Tuning

### Connection Pooling

```python
redis.from_url(
    redis_url,
    max_connections=50
)
```

**Why it matters:**
- Reuses connections
- Prevents connection exhaustion

**Recommendation:**
- API instances: 20-50 per instance
- Workers: 10-20 per worker

### Memory Management

```bash
redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

**Why it matters:**
- `maxmemory`: Prevents Redis from consuming all RAM
- `allkeys-lru`: Evicts least recently used keys
- Prevents OOM crashes

**Policies:**
- `allkeys-lru`: General cache
- `volatile-lru`: Only evict keys with TTL
- `allkeys-random`: Random eviction
- `noeviction`: Return errors when full

### Persistence

```bash
redis-server --appendonly yes
```

**Why it matters:**
- AOF (Append Only File) logs all writes
- Survives crashes
- Slower than no persistence

**For cache-only (no persistence needed):**
```bash
redis-server --appendonly no --save ""
```

## 🖥️ System Tuning

### File Descriptors

```bash
# Check current limit
ulimit -n

# Increase limit (temporary)
ulimit -n 65535

# Permanent: edit /etc/security/limits.conf
* soft nofile 65535
* hard nofile 65535
```

**Why it matters:**
- Each connection = 1 file descriptor
- Default (1024) is too low
- Nginx with 10k connections needs 10k+ FDs

### Kernel Parameters

```bash
# Edit /etc/sysctl.conf

# Increase connection backlog
net.core.somaxconn=65535

# Increase max connections
net.ipv4.ip_local_port_range=1024 65535

# Enable TCP fast open
net.ipv4.tcp_fastopen=3

# Increase TCP buffer sizes
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216

# Apply changes
sudo sysctl -p
```

## 📊 Monitoring Metrics

### What to Monitor

**Nginx:**
- Active connections
- Requests per second
- Response times
- Error rate (4xx, 5xx)

**API:**
- Request latency
- Error rate
- Database query time
- Cache hit rate

**Celery:**
- Queue length
- Task processing time
- Failed tasks
- Worker utilization

**MongoDB:**
- Connection pool usage
- Query execution time
- Slow queries
- Replication lag

**Redis:**
- Memory usage
- Eviction rate
- Hit/miss ratio
- Connection count

### Alert Thresholds

```
Nginx active connections > 80% of max
API response time > 1s (p95)
Celery queue length > 1000
MongoDB connections > 80% of max
Redis memory > 90% of max
```

## 🎯 Tuning Checklist

- [ ] Set Nginx `worker_processes auto`
- [ ] Set Nginx `worker_connections 10000`
- [ ] Enable `proxy_buffering off` for API routes
- [ ] Configure rate limiting (100r/s baseline)
- [ ] Set Celery concurrency based on CPU cores
- [ ] Enable `task_acks_late=True`
- [ ] Set `worker_prefetch_multiplier=1` for fair distribution
- [ ] Configure MongoDB connection pool (50-100)
- [ ] Set Redis max memory and eviction policy
- [ ] Increase system file descriptors (`ulimit -n 65535`)
- [ ] Tune kernel parameters (`somaxconn`, `tcp_fastopen`)
- [ ] Set up monitoring and alerts
- [ ] Load test and adjust based on results

## 🔬 Load Testing

### Baseline Test

```bash
# Test current capacity
ab -n 10000 -c 100 http://localhost/api/items

# Look for:
# - Requests per second
# - Time per request
# - Failed requests (should be 0)
```

### Find Bottleneck

```bash
# Monitor during load test
docker stats

# Check which service is maxed out:
# - CPU 100% = need more workers/instances
# - Memory 100% = need more RAM or reduce cache
# - Network I/O = need faster network or compression
```

### Gradual Increase

```bash
# Start low
ab -n 1000 -c 10 http://localhost/api/items

# Increase concurrency
ab -n 1000 -c 50 http://localhost/api/items
ab -n 1000 -c 100 http://localhost/api/items
ab -n 1000 -c 200 http://localhost/api/items

# Find breaking point
```

## 📈 Scaling Strategy

### Vertical Scaling (Single Server)

1. Increase API replicas: `docker compose up -d --scale api=5`
2. Increase worker replicas: `docker compose up -d --scale celery_worker=5`
3. Increase Celery concurrency: `--concurrency=8`
4. Increase MongoDB connections: `--maxConns 2000`
5. Increase Redis memory: `--maxmemory 1gb`

### Horizontal Scaling (Multiple Servers)

1. Move MongoDB to dedicated server or managed service
2. Move Redis to dedicated server or managed service
3. Move RabbitMQ to dedicated server or managed service
4. Run API + Workers on multiple app servers
5. Use external load balancer (AWS ALB, Nginx Plus)
6. Consider Kubernetes for orchestration

## 🎓 Performance Tips

1. **Use async endpoints for heavy operations** - Never block API requests
2. **Cache frequently accessed data** - Reduce database load
3. **Batch database operations** - Fewer round trips
4. **Use database indexes** - Faster queries
5. **Monitor slow queries** - Optimize or cache
6. **Set appropriate timeouts** - Fail fast, retry
7. **Use connection pooling** - Reuse connections
8. **Enable compression** - Reduce bandwidth
9. **Optimize Docker images** - Faster deployments
10. **Regular maintenance** - Restart workers, clean old data
