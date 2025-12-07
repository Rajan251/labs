# Centralized Rate Limiting Service

A comprehensive design document for building a production-ready, distributed rate limiting service for APIs.

## 📚 Documentation

### [Complete Design Document](docs/RATE_LIMITING_DESIGN.md)

This document covers:

### 🎯 Rate Limiting Algorithms
- **Token Bucket** - Allows bursts, smooth rate limiting
- **Leaky Bucket** - Constant output rate, traffic shaping
- **Fixed Window Counter** - Simple but has boundary issues
- **Sliding Window Log** - Very accurate but expensive
- **Sliding Window Counter** - Best balance (recommended)

### 💾 Storage Strategies
- **In-Memory** - Ultra-fast but not distributed
- **Redis (Distributed)** - Production-ready, accurate, scalable
- **Hybrid Approach** - Best of both worlds

### 🎚️ Limiting Strategies
- **Per-User** - Limit by authenticated user ID
- **Per-IP** - Limit by IP address (DDoS protection)
- **Per-Endpoint** - Different limits for different APIs
- **Composite** - Multiple limits combined

### 🔄 Distributed Counters
- Race condition handling
- Redis atomic operations
- Lua scripts for complex logic
- Distributed locks

### 🛡️ Failure Modes & Resilience
- Redis unavailability strategies
- Fail open vs fail closed
- Fallback to local limits
- Circuit breakers
- Clock skew handling
- Network partition mitigation

## 🏗️ Architecture Overview

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
    │  (Shared Counters)  │
    └─────────────────────┘
```

## 🚀 Quick Concepts

### Token Bucket (Recommended)

```
Bucket Capacity: 100 tokens
Refill Rate: 10 tokens/second

Request comes in:
- If tokens available → Allow & consume 1 token
- If no tokens → Reject (429 Too Many Requests)
```

**Allows bursts** up to bucket capacity while maintaining average rate.

### Sliding Window Counter (Best for Production)

```
Combines two fixed windows with weighted calculation:

Previous Window: 80 requests
Current Window: 30 requests
Current Time: 30s into current window

Estimated = (80 × 0.5) + 30 = 70 requests
Limit: 100 → ✅ Allow
```

**Accurate, efficient, and production-ready.**

## 📊 Algorithm Comparison

| Algorithm | Accuracy | Memory | Bursts | Production |
|-----------|----------|--------|--------|------------|
| Token Bucket | High | Low | ✅ Yes | ✅ Yes |
| Leaky Bucket | High | Medium | ❌ No | ✅ Yes |
| Fixed Window | Low | Very Low | ✅ Yes | ⚠️ Simple cases |
| Sliding Log | Very High | High | ❌ No | ❌ Expensive |
| **Sliding Window** | **High** | **Low** | **✅ Yes** | **✅ Best** |

## 💡 Key Insights

### 1. Storage Choice

**For Production: Use Redis**
- Distributed state across all API servers
- Atomic operations (no race conditions)
- Scalable to millions of keys
- Optional persistence

### 2. Failure Strategy

**Recommended: Fail Open with Local Fallback**
```python
try:
    return redis_rate_limit(user_id)
except RedisError:
    return local_rate_limit(user_id)  # Fallback
```

### 3. Response Headers

Always inform clients about their limits:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1234567890
Retry-After: 60
```

## 🎯 Use Cases

### API Rate Limiting
```
GET /api/users → 1000 req/min
POST /api/users → 100 req/min
POST /api/payments → 10 req/min
```

### DDoS Protection
```
Per-IP limit: 1000 req/min
Blocks malicious traffic automatically
```

### Tiered Pricing
```
Free tier: 100 req/hour
Pro tier: 10,000 req/hour
Enterprise: Unlimited
```

## 🔐 Security Considerations

1. **Prevent Bypass**: Rate limit before authentication
2. **IP Spoofing**: Use X-Forwarded-For carefully
3. **Distributed Attacks**: Combine IP + User limits
4. **Cache Poisoning**: Validate all inputs

## 📈 Monitoring

**Essential Metrics:**
- Rate limit hits (429 responses)
- Redis latency (p50, p95, p99)
- Redis connection errors
- Per-user/IP request rates
- Cache hit rates

## 🛠️ Implementation Checklist

- [ ] Choose algorithm (Sliding Window recommended)
- [ ] Set up Redis cluster with replication
- [ ] Implement rate limiter middleware
- [ ] Add response headers
- [ ] Configure failure fallback
- [ ] Set up monitoring and alerts
- [ ] Load test with burst traffic
- [ ] Document rate limits for API users

## 📚 Further Reading

See [RATE_LIMITING_DESIGN.md](docs/RATE_LIMITING_DESIGN.md) for:
- Detailed algorithm explanations with pseudocode
- Redis implementation examples
- Lua scripts for atomic operations
- Failure mode analysis
- Performance optimization techniques
- Complete architecture diagrams

## 🎓 Learning Path

1. **Start Here**: Read algorithm concepts
2. **Understand Storage**: Compare in-memory vs Redis
3. **Study Failures**: Learn resilience patterns
4. **Review Architecture**: See complete system design
5. **Implement**: Build your own rate limiter

---

**Recommended Production Stack:**
- Algorithm: Sliding Window Counter
- Storage: Redis Cluster
- Fallback: Local in-memory limits
- Failure Mode: Fail open with local limits
- Monitoring: Prometheus + Grafana
