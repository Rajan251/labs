# Webhook Delivery Platform

A production-ready webhook delivery platform with reliable delivery, exponential backoff retry, idempotency, signature verification, dead-letter queues, per-tenant rate limiting, and comprehensive monitoring.

## Features

- ✅ **Multi-Tenant Architecture**: Isolated tenant configurations with API key authentication
- ✅ **Reliable Delivery**: Exponential backoff retry (1s → 32s) with configurable policies
- ✅ **Idempotency**: Duplicate event detection using event ID + tenant hash
- ✅ **Security**: HMAC-SHA256 signature verification for webhook authenticity
- ✅ **Dead-Letter Queue**: Failed event storage with manual retry capabilities
- ✅ **Rate Limiting**: Redis-based token bucket algorithm per tenant
- ✅ **Monitoring**: Prometheus metrics + Grafana dashboards
- ✅ **Structured Logging**: JSON logging for centralized log aggregation
- ✅ **Async Workers**: Celery workers with RabbitMQ for scalable delivery

## Architecture

```
Event Publishers → API Gateway → Rate Limiter → Message Queue → Workers → Tenant Webhooks
                                                      ↓
                                                  DLQ (on failure)
```

**Tech Stack**: FastAPI, PostgreSQL, Redis, RabbitMQ, Celery, Prometheus, Grafana

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd webhook-lab

# Copy environment file
cp .env.example .env
```

### 2. Start All Services

```bash
docker-compose up -d
```

This starts:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (user: webhook_user, pass: webhook_pass)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (user: admin, pass: admin)

### 3. Create Your First Tenant

```bash
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Company",
    "email": "webhooks@mycompany.com",
    "rate_limit": 100
  }'
```

Response includes `api_key` and `secret_key` - **save these securely!**

### 4. Configure Webhook Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/tenants/1/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks",
    "event_types": ["user.created", "order.completed"],
    "is_active": true
  }'
```

### 5. Publish an Event

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "X-API-Key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_123",
    "event_type": "user.created",
    "payload": {
      "user_id": "user_456",
      "email": "user@example.com",
      "created_at": "2024-01-01T00:00:00Z"
    }
  }'
```

The webhook will be delivered to your endpoint with HMAC signature!

## Project Structure

```
webhook-lab/
├── app/
│   ├── api/              # REST API endpoints
│   │   ├── tenants.py    # Tenant management
│   │   ├── events.py     # Event publishing
│   │   └── dlq.py        # Dead-letter queue
│   ├── services/         # Business logic
│   │   ├── tenant_service.py
│   │   ├── event_service.py
│   │   ├── dlq_service.py
│   │   └── signature_service.py
│   ├── workers/          # Celery workers
│   │   └── delivery_worker.py
│   ├── middleware/       # Middleware
│   │   └── rate_limiter.py
│   ├── monitoring/       # Observability
│   │   ├── metrics.py
│   │   └── logging.py
│   ├── models.py         # Database models
│   ├── schemas.py        # Pydantic schemas
│   ├── database.py       # DB connection
│   ├── config.py         # Configuration
│   └── main.py           # FastAPI app
├── docs/                 # Documentation
├── monitoring/           # Prometheus & Grafana config
├── tests/                # Test suite
├── docker-compose.yml    # Docker setup
├── Dockerfile
└── requirements.txt
```

## Key Concepts

### Tenant Registration

Each tenant gets:
- Unique API key for authentication
- Secret key for HMAC signature generation
- Configurable rate limit (events/minute)
- Multiple webhook endpoints

### Event Routing

Events are routed to endpoints based on:
- Tenant ownership
- Event type subscriptions (empty = all events)
- Endpoint active status

### Delivery Retry Strategy

| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | 1 second |
| 3 | 2 seconds |
| 4 | 4 seconds |
| 5 | 8 seconds |
| 6 | 16 seconds |
| 7 | 32 seconds (max) |

After 7 attempts, events move to Dead-Letter Queue.

### Signature Verification

Each webhook includes `X-Webhook-Signature` header:

```
X-Webhook-Signature: sha256=<hmac-sha256-hex>
```

Recipients should verify:

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret_key):
    expected = hmac.new(
        secret_key.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Rate Limiting

Token bucket algorithm:
- Each tenant has a bucket with N tokens
- Each event consumes 1 token
- Tokens refill at constant rate
- Requests blocked when bucket empty

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)**: System design and components
- **[API Reference](docs/API.md)**: Complete API documentation
- **[Deployment Guide](docs/DEPLOYMENT.md)**: Production deployment
- **[Monitoring Guide](docs/MONITORING.md)**: Metrics and dashboards
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)**: Extending the platform

## Monitoring

### Key Metrics

- `webhook_events_published_total`: Events published by tenant/type
- `webhook_delivery_success_total`: Successful deliveries
- `webhook_delivery_failure_total`: Failed deliveries
- `webhook_delivery_duration_seconds`: Delivery latency
- `webhook_dlq_size`: Unresolved DLQ entries
- `webhook_rate_limit_hits_total`: Rate limit violations

### Grafana Dashboards

Access Grafana at http://localhost:3000 to view:
- Event throughput
- Delivery success rates
- Retry attempt distribution
- DLQ size over time
- Per-tenant metrics

## Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://webhook_user:webhook_pass@localhost:5432/webhook_db"
export REDIS_URL="redis://localhost:6379/0"
export CELERY_BROKER_URL="amqp://webhook_user:webhook_pass@localhost:5672/"

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload

# Start worker (in another terminal)
celery -A app.workers.delivery_worker worker --loglevel=info
```

### Running Tests

```bash
pytest tests/ -v --cov=app
```

## Production Considerations

1. **Security**:
   - Change default passwords in `.env`
   - Use strong `SECRET_KEY`
   - Enable HTTPS/TLS
   - Implement API key rotation

2. **Scalability**:
   - Scale workers horizontally
   - Use connection pooling
   - Configure appropriate rate limits
   - Monitor queue depth

3. **Reliability**:
   - Set up database backups
   - Configure Redis persistence
   - Monitor DLQ size
   - Set up alerting

4. **Performance**:
   - Tune worker concurrency
   - Optimize database indexes
   - Cache frequently accessed data
   - Use CDN for static assets

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.
