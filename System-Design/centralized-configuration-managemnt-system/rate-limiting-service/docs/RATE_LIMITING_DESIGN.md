# Centralized Rate Limiting Service - Design Document

## Table of Contents
1. [Overview](#overview)
2. [Rate Limiting Algorithms](#rate-limiting-algorithms)
3. [Storage Strategies](#storage-strategies)
4. [Limiting Strategies](#limiting-strategies)
5. [Distributed Counters](#distributed-counters)
6. [Failure Modes & Resilience](#failure-modes--resilience)
7. [Architecture](#architecture)
8. [Implementation Considerations](#implementation-considerations)

---

## Overview

A centralized rate limiting service controls the rate of requests to APIs, protecting backend services from overload and ensuring fair resource allocation among users. This document covers the design of a production-ready, distributed rate limiting system.

### Key Requirements
- **High Performance**: Low latency (<5ms p99)
- **Accuracy**: Minimal false positives/negatives
- **Scalability**: Handle millions of requests per second
- **Flexibility**: Support multiple limiting strategies
- **Resilience**: Graceful degradation on failures

---

## Rate Limiting Algorithms

### 1. Token Bucket Algorithm

**Concept:**
Imagine a bucket that holds tokens. Each request consumes one token. Tokens are added to the bucket at a fixed rate. If the bucket is full, new tokens are discarded.

```
┌─────────────────────────────┐
│    Token Bucket (Capacity)  │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐   │
│  │ T │ │ T │ │ T │ │ T │   │  Tokens
│  └───┘ └───┘ └───┘ └───┘   │
└─────────────────────────────┘
         ↑              ↓
    Refill Rate    Consumption
    (e.g., 10/sec)  (per request)
```

**How It Works:**
1. Bucket has maximum capacity (e.g., 100 tokens)
2. Tokens refill at constant rate (e.g., 10 tokens/second)
3. Each request consumes 1 token
4. If tokens available → Allow request
5. If no tokens → Reject request (429 Too Many Requests)

**Advantages:**
- ✅ Allows bursts up to bucket capacity
- ✅ Smooth rate limiting over time
- ✅ Simple to implement
- ✅ Memory efficient

**Disadvantages:**
- ❌ Can allow large bursts if bucket is full
- ❌ Requires tracking last refill time

**Use Cases:**
- API rate limiting with burst allowance
- User-facing APIs where occasional bursts are acceptable
- Services with variable load patterns

**Implementation Pseudocode:**
```python
class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = now()
    
    def allow_request(self):
        # Refill tokens based on time elapsed
        now_time = now()
        elapsed = now_time - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now_time
        
        # Check if request can be allowed
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

---

### 2. Leaky Bucket Algorithm

**Concept:**
Imagine a bucket with a hole at the bottom. Requests are added to the bucket as water. Water leaks out at a constant rate. If the bucket overflows, requests are rejected.

```
    Incoming Requests
           ↓
    ┌─────────────┐
    │   Bucket    │
    │   (Queue)   │
    │ ┌─────────┐ │
    │ │ Request │ │
    │ │ Request │ │
    │ │ Request │ │
    │ └─────────┘ │
    └──────┬──────┘
           ↓
    Leak Rate (constant)
    (e.g., 10 req/sec)
```

**How It Works:**
1. Requests enter a queue (bucket)
2. Requests are processed at constant rate (leak rate)
3. If queue is full → Reject new requests
4. Queue drains at fixed rate regardless of input

**Advantages:**
- ✅ Smooths out traffic spikes
- ✅ Guarantees constant output rate
- ✅ Prevents sudden bursts
- ✅ Predictable resource usage

**Disadvantages:**
- ❌ No burst allowance
- ❌ Requires queue management
- ❌ Higher memory usage for queue

**Use Cases:**
- Traffic shaping for downstream services
- Protecting services that can't handle bursts
- Network traffic management

**Implementation Pseudocode:**
```python
class LeakyBucket:
    def __init__(self, capacity, leak_rate):
        self.capacity = capacity
        self.queue = []
        self.leak_rate = leak_rate  # requests per second
        self.last_leak = now()
    
    def allow_request(self):
        # Leak requests based on time elapsed
        now_time = now()
        elapsed = now_time - self.last_leak
        requests_to_leak = int(elapsed * self.leak_rate)
        
        # Remove leaked requests from queue
        self.queue = self.queue[requests_to_leak:]
        self.last_leak = now_time
        
        # Check if queue has space
        if len(self.queue) < self.capacity:
            self.queue.append(now_time)
            return True
        return False
```

---

### 3. Fixed Window Counter

**Concept:**
Divide time into fixed windows (e.g., 1 minute). Count requests in each window. Reset counter at window boundary.

```
Window 1 (0-60s)    Window 2 (60-120s)   Window 3 (120-180s)
┌─────────────┐     ┌─────────────┐      ┌─────────────┐
│ Count: 95   │     │ Count: 103  │      │ Count: 87   │
│ Limit: 100  │     │ Limit: 100  │      │ Limit: 100  │
└─────────────┘     └─────────────┘      └─────────────┘
     ✅ Allow            ❌ Reject            ✅ Allow
```

**Advantages:**
- ✅ Very simple to implement
- ✅ Low memory usage
- ✅ Easy to understand

**Disadvantages:**
- ❌ Boundary issues (can allow 2x limit at boundaries)
- ❌ Unfair to users at window edges

**Example of Boundary Issue:**
```
Window 1: 100 requests at 59s → Allowed
Window 2: 100 requests at 61s → Allowed
Total: 200 requests in 2 seconds!
```

---

### 4. Sliding Window Log

**Concept:**
Keep a log of all request timestamps. Count requests in the last N seconds.

```
Current Time: 100s
Window: Last 60s (40s - 100s)

Request Log:
[35s, 42s, 45s, 58s, 62s, 75s, 88s, 95s, 98s]
         ↑                                  ↑
    Outside window                   Inside window
    
Requests in window: 7
Limit: 10
Result: ✅ Allow
```

**Advantages:**
- ✅ Very accurate
- ✅ No boundary issues
- ✅ True sliding window

**Disadvantages:**
- ❌ High memory usage (stores all timestamps)
- ❌ Expensive to compute (scan all timestamps)
- ❌ Not suitable for high-traffic scenarios

---

### 5. Sliding Window Counter (Hybrid)

**Concept:**
Combine fixed window counters with weighted calculation for smooth sliding.

```
Previous Window     Current Window
(0-60s)            (60-120s)
Count: 80          Count: 30

Current Time: 90s (30s into current window)

Estimated Count = (Previous × Weight) + Current
                = (80 × 0.5) + 30
                = 40 + 30 = 70

Limit: 100
Result: ✅ Allow
```

**Formula:**
```
Weight = (Window Size - Elapsed Time in Current Window) / Window Size
Estimated Count = (Previous Window Count × Weight) + Current Window Count
```

**Advantages:**
- ✅ Good accuracy
- ✅ Low memory usage (only 2 counters)
- ✅ No boundary issues
- ✅ Efficient computation

**Disadvantages:**
- ❌ Approximate (not 100% accurate)
- ❌ Slightly complex logic

**Best Choice for Production:** This is often the best balance of accuracy, performance, and memory efficiency.

---

## Storage Strategies

### 1. In-Memory Storage

**Architecture:**
```
┌─────────────────────────────┐
│   Rate Limiter Service      │
│  ┌────────────────────────┐ │
│  │   In-Memory HashMap    │ │
│  │  user_id → Counter     │ │
│  │  ip_addr → Counter     │ │
│  └────────────────────────┘ │
└─────────────────────────────┘
```

**Advantages:**
- ✅ **Ultra-fast**: <1ms latency
- ✅ **Simple**: No external dependencies
- ✅ **Low cost**: No database needed

**Disadvantages:**
- ❌ **Not distributed**: Each instance has separate state
- ❌ **Lost on restart**: No persistence
- ❌ **Memory limited**: Can't scale beyond single machine
- ❌ **Inaccurate**: Multiple instances = multiple limits

**Use Cases:**
- Single-instance applications
- Development/testing
- Non-critical rate limiting
- Per-instance limits (not global)

**Example:**
```python
# Each API server instance has its own limits
Server 1: User A → 50 requests
Server 2: User A → 50 requests
Total: 100 requests (but limit was 60!)
```

---

### 2. Distributed Storage (Redis)

**Architecture:**
```
┌──────────┐  ┌──────────┐  ┌──────────┐
│  API     │  │  API     │  │  API     │
│ Server 1 │  │ Server 2 │  │ Server 3 │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   ↓
         ┌─────────────────┐
         │  Redis Cluster  │
         │  (Shared State) │
         └─────────────────┘
```

**Advantages:**
- ✅ **Distributed**: Shared state across all instances
- ✅ **Accurate**: Global rate limiting
- ✅ **Scalable**: Can handle millions of keys
- ✅ **Persistent**: Optional persistence
- ✅ **Atomic operations**: INCR, EXPIRE commands

**Disadvantages:**
- ❌ **Network latency**: 1-5ms overhead
- ❌ **Single point of failure**: Needs Redis HA
- ❌ **Cost**: Additional infrastructure
- ❌ **Complexity**: Requires Redis management

**Use Cases:**
- **Production systems** (most common)
- Multi-instance deployments
- Global rate limiting
- High-traffic APIs

**Redis Data Structures:**

```redis
# Token Bucket
SET user:123:tokens 100
SET user:123:last_refill 1234567890
EXPIRE user:123:tokens 3600

# Fixed Window Counter
INCR user:123:window:1234567800
EXPIRE user:123:window:1234567800 60

# Sliding Window
ZADD user:123:requests 1234567890 "req_id_1"
ZREMRANGEBYSCORE user:123:requests 0 1234567830
ZCARD user:123:requests
```

---

### 3. Hybrid Approach

**Architecture:**
```
┌─────────────────────────────┐
│      API Server             │
│  ┌────────────────────────┐ │
│  │  Local Cache (L1)      │ │ ← Fast, approximate
│  │  TTL: 1-5 seconds      │ │
│  └──────────┬─────────────┘ │
│             ↓                │
│  ┌────────────────────────┐ │
│  │  Redis (L2)            │ │ ← Accurate, slower
│  │  Global state          │ │
│  └────────────────────────┘ │
└─────────────────────────────┘
```

**How It Works:**
1. Check local cache first (fast path)
2. If cache miss or expired → Check Redis
3. Cache result locally for 1-5 seconds
4. Periodically sync with Redis

**Advantages:**
- ✅ Best of both worlds
- ✅ Low latency (most requests hit cache)
- ✅ Accurate (syncs with Redis)
- ✅ Reduces Redis load

**Disadvantages:**
- ❌ Complex implementation
- ❌ Slight inaccuracy during cache TTL
- ❌ Cache invalidation challenges

---

## Limiting Strategies

### 1. Per-User Rate Limiting

**Concept:** Limit requests per authenticated user.

```
User A: 100 requests/minute
User B: 100 requests/minute
User C: 1000 requests/minute (premium)
```

**Implementation:**
```python
def check_rate_limit(user_id, limit):
    key = f"rate_limit:user:{user_id}"
    current = redis.incr(key)
    
    if current == 1:
        redis.expire(key, 60)  # 60 seconds window
    
    return current <= limit
```

**Use Cases:**
- Authenticated APIs
- SaaS platforms with tiered pricing
- Preventing abuse by specific users

---

### 2. Per-IP Rate Limiting

**Concept:** Limit requests per IP address.

```
IP 1.2.3.4: 1000 requests/minute
IP 5.6.7.8: 1000 requests/minute
```

**Implementation:**
```python
def check_ip_rate_limit(ip_address, limit):
    key = f"rate_limit:ip:{ip_address}"
    current = redis.incr(key)
    
    if current == 1:
        redis.expire(key, 60)
    
    return current <= limit
```

**Use Cases:**
- Public APIs without authentication
- DDoS protection
- Bot detection

**Challenges:**
- **NAT/Proxy**: Multiple users behind same IP
- **IPv6**: Large address space
- **VPN/CDN**: Shared IP addresses

---

### 3. Per-Endpoint Rate Limiting

**Concept:** Different limits for different endpoints.

```
GET  /api/users      → 1000 req/min
POST /api/users      → 100 req/min
POST /api/payments   → 10 req/min
```

**Implementation:**
```python
def check_endpoint_rate_limit(user_id, endpoint, limit):
    key = f"rate_limit:user:{user_id}:endpoint:{endpoint}"
    current = redis.incr(key)
    
    if current == 1:
        redis.expire(key, 60)
    
    return current <= limit
```

---

### 4. Composite Rate Limiting

**Concept:** Multiple limits applied together.

```
Limits for User A:
- Global: 10,000 requests/hour
- Per-endpoint: 100 requests/minute per endpoint
- Per-IP: 1,000 requests/minute per IP
```

**Implementation:**
```python
def check_composite_limits(user_id, ip, endpoint):
    checks = [
        check_user_limit(user_id, 10000, 3600),
        check_endpoint_limit(user_id, endpoint, 100, 60),
        check_ip_limit(ip, 1000, 60)
    ]
    
    return all(checks)
```

---

## Distributed Counters

### Challenge: Race Conditions

**Problem:**
```
Server 1: Read count = 99
Server 2: Read count = 99
Server 1: Increment → 100 (Allow)
Server 2: Increment → 100 (Allow)
Result: 101 requests (limit was 100!)
```

### Solution 1: Redis Atomic Operations

**Using INCR:**
```lua
-- Atomic increment and check
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end

if current > tonumber(ARGV[2]) then
    return 0  -- Reject
else
    return 1  -- Allow
end
```

**Advantages:**
- ✅ Atomic operations
- ✅ No race conditions
- ✅ Simple to implement

---

### Solution 2: Lua Scripts

**Token Bucket in Lua:**
```lua
-- Token bucket implementation
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

-- Refill tokens
local elapsed = now - last_refill
local tokens_to_add = elapsed * refill_rate
tokens = math.min(capacity, tokens + tokens_to_add)

-- Check if request can be allowed
if tokens >= 1 then
    tokens = tokens - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 3600)
    return 1  -- Allow
else
    return 0  -- Reject
end
```

**Advantages:**
- ✅ Complex logic in single atomic operation
- ✅ Reduces network round trips
- ✅ Guaranteed consistency

---

### Solution 3: Distributed Locks

**Using Redis Locks:**
```python
def check_rate_limit_with_lock(user_id, limit):
    lock_key = f"lock:rate_limit:{user_id}"
    counter_key = f"rate_limit:{user_id}"
    
    # Acquire lock
    lock = redis.set(lock_key, "1", nx=True, ex=1)
    
    if lock:
        try:
            current = redis.incr(counter_key)
            if current == 1:
                redis.expire(counter_key, 60)
            return current <= limit
        finally:
            redis.delete(lock_key)
    else:
        # Lock acquisition failed, retry or reject
        return False
```

**Disadvantages:**
- ❌ Performance overhead
- ❌ Lock contention
- ❌ Complexity

---

## Failure Modes & Resilience

### 1. Redis Unavailable

**Failure Scenario:**
```
API Server → Redis (Connection Failed!)
```

**Strategies:**

#### A. Fail Open (Allow All Requests)
```python
def check_rate_limit(user_id, limit):
    try:
        return redis_check(user_id, limit)
    except RedisConnectionError:
        logger.error("Redis unavailable, failing open")
        return True  # Allow request
```

**Pros:** Service stays available
**Cons:** No rate limiting during outage

---

#### B. Fail Closed (Reject All Requests)
```python
def check_rate_limit(user_id, limit):
    try:
        return redis_check(user_id, limit)
    except RedisConnectionError:
        logger.error("Redis unavailable, failing closed")
        return False  # Reject request
```

**Pros:** Protects backend
**Cons:** Service becomes unavailable

---

#### C. Fallback to Local Limits
```python
local_limiter = InMemoryRateLimiter()

def check_rate_limit(user_id, limit):
    try:
        return redis_check(user_id, limit)
    except RedisConnectionError:
        logger.warning("Redis unavailable, using local limiter")
        return local_limiter.check(user_id, limit)
```

**Pros:** Best balance
**Cons:** Less accurate during outage

---

### 2. Redis Cluster Split-Brain

**Problem:**
```
Cluster Node 1: User A → 50 requests
Cluster Node 2: User A → 50 requests
Total: 100 requests (limit was 60!)
```

**Solutions:**
- Use Redis Cluster with proper configuration
- Implement quorum-based decisions
- Monitor cluster health

---

### 3. Clock Skew

**Problem:**
```
Server 1 Time: 10:00:00
Server 2 Time: 10:00:05 (5 seconds ahead)

Window calculations differ!
```

**Solutions:**
- Use NTP for time synchronization
- Use Redis TIME command for consistent timestamps
- Implement clock skew detection

---

### 4. Network Partitions

**Scenario:**
```
API Servers → [Network Partition] → Redis
```

**Mitigation:**
- Redis Sentinel for automatic failover
- Circuit breakers
- Health checks and monitoring
- Graceful degradation

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Load Balancer                     │
└──────────────┬──────────────────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    ↓          ↓          ↓          ↓
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│  API   │ │  API   │ │  API   │ │  API   │
│Server 1│ │Server 2│ │Server 3│ │Server 4│
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
    │          │          │          │
    └──────────┼──────────┴──────────┘
               ↓
    ┌─────────────────────┐
    │   Redis Cluster     │
    │  ┌───┐ ┌───┐ ┌───┐ │
    │  │ M │ │ S │ │ S │ │
    │  └───┘ └───┘ └───┘ │
    └─────────────────────┘
               ↓
    ┌─────────────────────┐
    │   Monitoring        │
    │ (Prometheus/Grafana)│
    └─────────────────────┘
```

### Component Details

**1. Rate Limiter Middleware**
```python
class RateLimiterMiddleware:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.local_cache = LRUCache(max_size=10000)
    
    async def __call__(self, request):
        user_id = extract_user_id(request)
        ip = extract_ip(request)
        endpoint = request.path
        
        # Check rate limits
        if not await self.check_limits(user_id, ip, endpoint):
            return Response(
                status=429,
                headers={
                    "X-RateLimit-Limit": "100",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": "1234567890",
                    "Retry-After": "60"
                }
            )
        
        return await next_handler(request)
```

**2. Redis Client with Retry**
```python
class ResilientRedisClient:
    def __init__(self, redis_url):
        self.redis = Redis.from_url(redis_url)
        self.circuit_breaker = CircuitBreaker()
    
    async def incr_with_retry(self, key, max_retries=3):
        for attempt in range(max_retries):
            try:
                if self.circuit_breaker.is_open():
                    raise CircuitBreakerOpen()
                
                result = await self.redis.incr(key)
                self.circuit_breaker.record_success()
                return result
            
            except RedisError as e:
                self.circuit_breaker.record_failure()
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
```

---

## Implementation Considerations

### 1. Response Headers

Always include rate limit information:
```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1234567890

HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1234567890
Retry-After: 60
```

### 2. Monitoring Metrics

**Key Metrics:**
- Rate limit hits (429 responses)
- Rate limit misses (allowed requests)
- Redis latency
- Redis connection errors
- Per-user/IP request rates

### 3. Performance Optimization

**Best Practices:**
- Use pipelining for multiple Redis operations
- Implement local caching (1-5 second TTL)
- Use Lua scripts for complex operations
- Monitor and tune Redis configuration
- Use connection pooling

### 4. Testing Strategies

**Load Testing:**
```python
# Simulate burst traffic
async def load_test():
    tasks = []
    for i in range(1000):
        tasks.append(make_request(user_id="test_user"))
    
    results = await asyncio.gather(*tasks)
    allowed = sum(1 for r in results if r.status == 200)
    rejected = sum(1 for r in results if r.status == 429)
    
    print(f"Allowed: {allowed}, Rejected: {rejected}")
```

---

## Summary

### Algorithm Comparison

| Algorithm | Accuracy | Memory | Complexity | Bursts | Production Ready |
|-----------|----------|--------|------------|--------|------------------|
| Token Bucket | High | Low | Medium | Yes | ✅ Yes |
| Leaky Bucket | High | Medium | Medium | No | ✅ Yes |
| Fixed Window | Low | Very Low | Low | Yes | ⚠️ Simple cases |
| Sliding Log | Very High | High | High | No | ❌ No (expensive) |
| Sliding Window | High | Low | Medium | Yes | ✅ Yes (Best) |

### Storage Comparison

| Storage | Latency | Accuracy | Scalability | Cost | Production Ready |
|---------|---------|----------|-------------|------|------------------|
| In-Memory | <1ms | Low | Low | Free | ⚠️ Single instance |
| Redis | 1-5ms | High | High | $$ | ✅ Yes (Recommended) |
| Hybrid | <1ms | Medium | High | $$ | ✅ Yes (Advanced) |

### Recommended Stack

**For Production:**
- **Algorithm**: Sliding Window Counter
- **Storage**: Redis Cluster
- **Fallback**: Local in-memory limits
- **Failure Mode**: Fail open with local limits
- **Monitoring**: Prometheus + Grafana

This design provides the best balance of accuracy, performance, scalability, and resilience for a production-grade rate limiting service.
