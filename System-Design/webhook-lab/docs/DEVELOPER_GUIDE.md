# Developer Guide

Guide for developers extending and customizing the Webhook Delivery Platform.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Adding New Event Types](#adding-new-event-types)
3. [Customizing Retry Logic](#customizing-retry-logic)
4. [Extending Rate Limiting](#extending-rate-limiting)
5. [Adding Custom Metrics](#adding-custom-metrics)
6. [Testing](#testing)
7. [Code Style](#code-style)

---

## Project Structure

```
webhook-lab/
├── app/
│   ├── api/                    # REST API endpoints
│   │   ├── tenants.py         # Tenant management endpoints
│   │   ├── events.py          # Event publishing endpoints
│   │   └── dlq.py             # DLQ management endpoints
│   ├── services/               # Business logic layer
│   │   ├── tenant_service.py  # Tenant operations
│   │   ├── event_service.py   # Event operations
│   │   ├── dlq_service.py     # DLQ operations
│   │   └── signature_service.py # HMAC signature utilities
│   ├── workers/                # Celery workers
│   │   └── delivery_worker.py # Webhook delivery worker
│   ├── middleware/             # Middleware components
│   │   └── rate_limiter.py    # Rate limiting middleware
│   ├── monitoring/             # Observability
│   │   ├── metrics.py         # Prometheus metrics
│   │   └── logging.py         # Logging configuration
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   ├── database.py            # Database connection
│   ├── config.py              # Configuration management
│   ├── celery_app.py          # Celery configuration
│   └── main.py                # FastAPI application
├── docs/                       # Documentation
├── tests/                      # Test suite
├── monitoring/                 # Monitoring configuration
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Adding New Event Types

Event types are flexible and don't require code changes. Simply publish events with the desired type:

```python
# Example: Publishing a new event type
import requests

response = requests.post(
    "http://localhost:8000/api/v1/events",
    headers={"X-API-Key": "your-api-key"},
    json={
        "event_id": "evt_new_123",
        "event_type": "payment.succeeded",  # New event type
        "payload": {
            "payment_id": "pay_456",
            "amount": 100.00,
            "currency": "USD"
        }
    }
)
```

### Event Type Conventions

Follow these naming conventions:

- Use lowercase with dots: `resource.action`
- Examples:
  - `user.created`
  - `user.updated`
  - `user.deleted`
  - `order.completed`
  - `payment.succeeded`
  - `payment.failed`

### Filtering by Event Type

Tenants can subscribe to specific event types:

```python
# Subscribe to specific events
requests.post(
    "http://localhost:8000/api/v1/tenants/1/endpoints",
    json={
        "url": "https://example.com/webhooks",
        "event_types": ["user.created", "user.updated"]
    }
)

# Subscribe to all events
requests.post(
    "http://localhost:8000/api/v1/tenants/1/endpoints",
    json={
        "url": "https://example.com/webhooks",
        "event_types": []  # Empty = all events
    }
)
```

---

## Customizing Retry Logic

### Modifying Retry Strategy

Edit `app/workers/delivery_worker.py`:

```python
# Current exponential backoff
retry_delay = min(
    settings.initial_retry_delay * (2 ** (attempt_number - 1)),
    settings.max_retry_delay
)

# Custom: Linear backoff
retry_delay = settings.initial_retry_delay * attempt_number

# Custom: Fibonacci backoff
def fibonacci_backoff(n):
    if n <= 1:
        return 1
    a, b = 1, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return a

retry_delay = fibonacci_backoff(attempt_number)
```

### Configuring Retry Attempts

Update `.env`:

```bash
MAX_RETRY_ATTEMPTS=10        # Increase max retries
INITIAL_RETRY_DELAY=2        # Start with 2s delay
MAX_RETRY_DELAY=60           # Cap at 60s
```

### Per-Endpoint Retry Configuration

Add custom retry config to webhook endpoints:

```python
# In app/models.py - WebhookEndpoint
retry_config = Column(JSON, default=dict)

# Usage
{
    "max_attempts": 10,
    "initial_delay": 2,
    "max_delay": 120,
    "backoff_multiplier": 2
}
```

Then modify `delivery_worker.py` to use endpoint-specific config.

---

## Extending Rate Limiting

### Custom Rate Limit Algorithms

#### Sliding Window

```python
# app/middleware/rate_limiter.py

def sliding_window_check(self, tenant_id: int, limit: int, window: int):
    """Sliding window rate limiter."""
    key = f"rate_limit:sliding:{tenant_id}"
    current_time = time.time()
    window_start = current_time - window
    
    pipe = self.redis_client.pipeline()
    
    # Remove old entries
    pipe.zremrangebyscore(key, 0, window_start)
    
    # Count entries in window
    pipe.zcard(key)
    
    # Add current request
    pipe.zadd(key, {str(current_time): current_time})
    
    # Set expiry
    pipe.expire(key, window * 2)
    
    results = pipe.execute()
    count = results[1]
    
    return count < limit
```

#### Fixed Window

```python
def fixed_window_check(self, tenant_id: int, limit: int, window: int):
    """Fixed window rate limiter."""
    current_window = int(time.time() / window)
    key = f"rate_limit:fixed:{tenant_id}:{current_window}"
    
    count = self.redis_client.incr(key)
    
    if count == 1:
        self.redis_client.expire(key, window)
    
    return count <= limit
```

### Per-Endpoint Rate Limiting

```python
# Add to WebhookEndpoint model
rate_limit_override = Column(Integer, nullable=True)

# Check in rate limiter
def check_endpoint_rate_limit(self, endpoint_id: int):
    # Implementation
    pass
```

---

## Adding Custom Metrics

### Creating New Metrics

Edit `app/monitoring/metrics.py`:

```python
from prometheus_client import Counter, Histogram, Gauge

# Custom counter
webhook_custom_events_counter = Counter(
    "webhook_custom_events_total",
    "Custom events processed",
    ["event_category"]
)

# Custom histogram
webhook_queue_wait_time = Histogram(
    "webhook_queue_wait_seconds",
    "Time events spend in queue",
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0]
)

# Custom gauge
webhook_queue_depth = Gauge(
    "webhook_queue_depth",
    "Current queue depth"
)
```

### Recording Metrics

```python
# In your code
from app.monitoring.metrics import webhook_custom_events_counter

# Increment counter
webhook_custom_events_counter.labels(event_category="payment").inc()

# Record histogram
webhook_queue_wait_time.observe(wait_time_seconds)

# Set gauge
webhook_queue_depth.set(current_depth)
```

### Querying Custom Metrics

```promql
# In Prometheus/Grafana
rate(webhook_custom_events_total[5m])
histogram_quantile(0.95, rate(webhook_queue_wait_seconds_bucket[5m]))
webhook_queue_depth
```

---

## Testing

### Unit Tests

Create `tests/test_event_service.py`:

```python
import pytest
from app.services.event_service import EventService
from app.schemas import EventPublish

def test_generate_idempotency_key():
    """Test idempotency key generation."""
    key1 = EventService.generate_idempotency_key("evt_123", 1)
    key2 = EventService.generate_idempotency_key("evt_123", 1)
    key3 = EventService.generate_idempotency_key("evt_123", 2)
    
    assert key1 == key2  # Same event + tenant = same key
    assert key1 != key3  # Different tenant = different key

def test_create_event_idempotency(db_session):
    """Test event creation with idempotency."""
    event_data = EventPublish(
        event_id="evt_test_123",
        event_type="test.event",
        payload={"test": "data"}
    )
    
    # Create event
    event1 = EventService.create_event(db_session, 1, event_data)
    
    # Create duplicate
    event2 = EventService.create_event(db_session, 1, event_data)
    
    # Should return same event
    assert event1.id == event2.id
```

### Integration Tests

Create `tests/integration/test_end_to_end.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_complete_flow():
    """Test complete event flow from publishing to delivery."""
    
    # 1. Create tenant
    response = client.post("/api/v1/tenants", json={
        "name": "Test Company",
        "email": "test@example.com",
        "rate_limit": 100
    })
    assert response.status_code == 201
    tenant = response.json()
    api_key = tenant["api_key"]
    
    # 2. Create webhook endpoint
    response = client.post(
        f"/api/v1/tenants/{tenant['id']}/endpoints",
        json={
            "url": "https://webhook.site/test",
            "event_types": ["test.event"]
        }
    )
    assert response.status_code == 201
    
    # 3. Publish event
    response = client.post(
        "/api/v1/events",
        headers={"X-API-Key": api_key},
        json={
            "event_id": "evt_integration_test",
            "event_type": "test.event",
            "payload": {"test": "data"}
        }
    )
    assert response.status_code == 201
    event = response.json()
    
    # 4. Check event status
    response = client.get(
        f"/api/v1/events/{event['event_id']}/status",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 200
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov httpx

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_event_service.py::test_create_event_idempotency

# Run integration tests only
pytest tests/integration/ -v
```

---

## Code Style

### Python Style Guide

Follow PEP 8 with these additions:

- **Line length**: 100 characters
- **Imports**: Group by standard library, third-party, local
- **Docstrings**: Google style
- **Type hints**: Use for function signatures

### Example

```python
"""
Module docstring explaining purpose.
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Event
from app.schemas import EventPublish


class EventService:
    """Service for managing events."""
    
    @staticmethod
    def create_event(
        db: Session,
        tenant_id: int,
        event_data: EventPublish
    ) -> Optional[Event]:
        """
        Create a new event with idempotency checking.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            event_data: Event data
            
        Returns:
            Created event or existing event if duplicate
            
        Raises:
            HTTPException: If validation fails
        """
        # Implementation
        pass
```

### Linting

```bash
# Install linters
pip install black isort flake8 mypy

# Format code
black app/
isort app/

# Check style
flake8 app/

# Type checking
mypy app/
```

---

## Best Practices

1. **Always use type hints** for better IDE support
2. **Write docstrings** for all public functions
3. **Add tests** for new features
4. **Update metrics** for monitoring
5. **Log important events** with structured logging
6. **Handle errors gracefully** with proper exceptions
7. **Use transactions** for database operations
8. **Validate input** with Pydantic schemas
9. **Document API changes** in API.md
10. **Update CHANGELOG** for releases

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linters
6. Submit a pull request

---

## Useful Commands

```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f api

# Run tests
pytest tests/ -v

# Format code
black app/ tests/

# Type check
mypy app/

# Database migrations
alembic revision --autogenerate -m "Add column"
alembic upgrade head

# Access database
docker-compose exec postgres psql -U webhook_user -d webhook_db

# Access Redis
docker-compose exec redis redis-cli

# Monitor queue
docker-compose exec rabbitmq rabbitmqctl list_queues
```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
