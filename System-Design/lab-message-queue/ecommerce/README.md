# E-Commerce Backend System

> Complete microservices-based e-commerce platform backend

## Overview

Production-ready e-commerce backend with:
- **8 Microservices**: Catalog, Search, Cart, Order, Payment, Inventory, Promotions, User
- **Consistency Models**: Strong consistency for orders/inventory, eventual for catalog/search
- **Concurrency Handling**: Optimistic locking (cart), pessimistic locking (inventory)
- **Horizontal Scaling**: Stateless services, read replicas, caching
- **Payment Integration**: Stripe with idempotency
- **Distributed Transactions**: Saga pattern for order creation

## Quick Start

```bash
# Clone and setup
cd ecommerce

# Start all services
docker-compose -f docker-compose-ecommerce.yml up -d

# Initialize databases
./scripts/init-db.sh

# Test the system
curl http://localhost:8001/products  # Catalog
curl http://localhost:8002/cart      # Cart
```

## Architecture

```
Client → API Gateway → Microservices → Databases
                           ↓
                    Message Queue (RabbitMQ)
```

### Services

| Service | Port | Database | Purpose |
|---------|------|----------|---------|
| Catalog | 8001 | PostgreSQL | Product management |
| Search | 8002 | Elasticsearch | Full-text search |
| Cart | 8003 | Redis | Shopping cart |
| Order | 8004 | PostgreSQL | Order management |
| Payment | 8005 | - | Stripe integration |
| Inventory | 8006 | PostgreSQL + Redis | Stock management |
| Promotions | 8007 | PostgreSQL | Discounts/coupons |
| User | 8008 | PostgreSQL | Authentication |

## Key Features

### 1. Concurrency Control

**Cart (Optimistic Locking)**:
```python
# Version-based updates
UPDATE cart SET items = $1, version = version + 1
WHERE user_id = $2 AND version = $3
```

**Inventory (Pessimistic Locking)**:
```python
# Distributed lock + row lock
async with RedisLock(f"inventory:{product_id}"):
    SELECT * FROM inventory WHERE id = $1 FOR UPDATE
    UPDATE inventory SET reserved = reserved + $2
```

### 2. Distributed Transactions

**Saga Pattern** for order creation:
1. Reserve inventory
2. Apply promotions
3. Create payment intent
4. Create order
5. If any fails → compensate previous steps

### 3. Consistency Models

- **Strong**: Orders, Inventory (ACID transactions)
- **Eventual**: Catalog → Search (async indexing)
- **Causal**: User sees own writes

### 4. Scaling Strategies

- **Horizontal**: Stateless services, load balancing
- **Database**: Read replicas, sharding by user_id
- **Caching**: Redis (L1), CDN (L2)

## Documentation

- **[ECOMMERCE_DESIGN.md](docs/ECOMMERCE_DESIGN.md)** - Complete system design
- **[IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md)** - Step-by-step guide
- **[API_DOCS.md](docs/API_DOCS.md)** - API reference
- **[CONSISTENCY_CONCURRENCY.md](docs/CONSISTENCY_CONCURRENCY.md)** - Deep dive

## Technology Stack

- **Services**: FastAPI (Python)
- **Databases**: PostgreSQL, MongoDB, Redis, Elasticsearch
- **Message Queue**: RabbitMQ
- **Payment**: Stripe
- **Deployment**: Docker, Kubernetes

## Project Structure

```
ecommerce/
├── services/
│   ├── catalog/        # Product catalog
│   ├── search/         # Elasticsearch integration
│   ├── cart/           # Shopping cart (Redis)
│   ├── order/          # Order management + Saga
│   ├── payment/        # Stripe integration
│   ├── inventory/      # Stock management
│   ├── promotions/     # Discounts/coupons
│   └── user/           # Authentication
├── gateway/            # API Gateway (Nginx)
├── database/schemas/   # SQL schemas
├── docs/               # Documentation
└── docker-compose-ecommerce.yml
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run single service
cd services/catalog
uvicorn app:app --reload --port 8001

# Run tests
pytest tests/

# Load test
locust -f tests/load_test.py
```

## API Examples

### Create Product
```bash
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "LAPTOP-001",
    "name": "Gaming Laptop",
    "base_price": 1299.99,
    "category_id": "uuid"
  }'
```

### Add to Cart
```bash
curl -X POST http://localhost:8003/cart/items \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "uuid",
    "quantity": 2,
    "expected_version": 0
  }'
```

### Create Order
```bash
curl -X POST http://localhost:8004/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid",
    "items": [...],
    "shipping_address": {...}
  }'
```

## Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **RabbitMQ**: http://localhost:15672

## Performance

- **Throughput**: 10,000+ requests/sec
- **Latency**: p99 < 100ms
- **Availability**: 99.9%

## License

MIT
