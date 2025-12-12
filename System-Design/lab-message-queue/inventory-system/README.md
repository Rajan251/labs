# Inventory Management System

> Complete FastAPI-based inventory management system with multi-warehouse support, reservations, and real-time tracking

## Features

✅ **Multi-Warehouse Support** - Track inventory across multiple locations  
✅ **Product Variants** - Handle size, color, and other variations  
✅ **Inventory Reservations** - Reserve stock during checkout (10-min timeout)  
✅ **Distributed Locking** - Prevent oversell with Redis locks  
✅ **Real-Time Tracking** - Complete audit trail of all transactions  
✅ **Low Stock Alerts** - Automatic reorder point monitoring  
✅ **Batch Operations** - Bulk import/export capabilities  
✅ **REST API** - Complete OpenAPI/Swagger documentation  
✅ **Docker Support** - Easy deployment with Docker Compose  

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### Run with Docker

```bash
# Clone and navigate
cd inventory-system

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f inventory-api

# Access API documentation
open http://localhost:8000/docs
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://admin:password@localhost:5432/inventory"
export REDIS_URL="redis://localhost:6379"

# Run database migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload

# API available at http://localhost:8000
```

## API Endpoints

### Inventory Operations

```bash
# Check stock
GET /api/v1/inventory/stock?sku=LAPTOP-001&warehouse=WH1

# Receive inventory
POST /api/v1/inventory/receive
{
  "sku": "LAPTOP-001",
  "warehouse_code": "WH1",
  "quantity": 50,
  "reason": "New shipment"
}

# Ship inventory
POST /api/v1/inventory/ship
{
  "sku": "LAPTOP-001",
  "warehouse_code": "WH1",
  "quantity": 5,
  "order_id": "uuid"
}

# Adjust inventory (manual count)
POST /api/v1/inventory/adjust
{
  "sku": "LAPTOP-001",
  "warehouse_code": "WH1",
  "new_quantity": 45,
  "reason": "Physical count correction"
}

# Transfer between warehouses
POST /api/v1/inventory/transfer
{
  "sku": "LAPTOP-001",
  "from_warehouse": "WH1",
  "to_warehouse": "WH2",
  "quantity": 10
}
```

### Reservations

```bash
# Create reservation
POST /api/v1/reservations
{
  "order_id": "uuid",
  "items": [
    {
      "inventory_id": "uuid",
      "product_id": "uuid",
      "warehouse_id": "uuid",
      "quantity": 2
    }
  ],
  "ttl": 600
}

# Confirm reservation (after payment)
POST /api/v1/reservations/{order_id}/confirm

# Release reservation (cancel order)
POST /api/v1/reservations/{order_id}/release
```

### Dashboard & Metrics

```bash
# Get dashboard metrics
GET /api/v1/dashboard/metrics

# Get low stock items
GET /api/v1/dashboard/low-stock?warehouse_id=uuid
```

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  FastAPI    │
│  REST API   │
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌─────────────┐ ┌──────────┐ ┌──────────┐
│ PostgreSQL  │ │  Redis   │ │ Services │
│  Database   │ │  Cache   │ │  Layer   │
└─────────────┘ └──────────┘ └──────────┘
```

### Technology Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15 with async support (asyncpg)
- **ORM**: SQLAlchemy 2.0 (async)
- **Cache/Locks**: Redis 7
- **Validation**: Pydantic V2
- **Deployment**: Docker & Docker Compose

## Project Structure

```
inventory-system/
├── app/
│   ├── api/              # API routes
│   ├── core/             # Core config (database, redis)
│   ├── models/           # SQLAlchemy models & Pydantic schemas
│   ├── services/         # Business logic
│   └── main.py           # FastAPI application
├── database/
│   └── init.sql          # Database initialization
├── tests/                # Unit & integration tests
├── docs/                 # Additional documentation
├── docker-compose.yml    # Docker setup
├── Dockerfile            # API container
└── requirements.txt      # Python dependencies
```

## Database Schema

### Core Tables

- **products** - Product catalog
- **product_variants** - Size/color variations
- **warehouses** - Storage locations
- **inventory** - Stock levels per warehouse
- **inventory_transactions** - Audit trail
- **inventory_reservations** - Temporary holds

### Key Relationships

```
Product (1) ──< (N) ProductVariant
Product (1) ──< (N) Inventory
Warehouse (1) ──< (N) Inventory
Inventory (1) ──< (N) InventoryTransaction
Inventory (1) ──< (N) InventoryReservation
```

## Key Features Explained

### 1. Reservation System

Prevents overselling by reserving stock during checkout:

```python
# User clicks checkout
reservation = await reserve_inventory(items, order_id, ttl=600)

# User completes payment
await confirm_reservation(order_id)  # Decrements stock

# Or if timeout/cancel
await release_reservation(order_id)  # Releases hold
```

### 2. Distributed Locking

Uses Redis to prevent race conditions:

```python
async with redis_client.lock(f"inventory_lock:{product_id}"):
    # Only one process can execute this at a time
    inventory = await get_inventory(product_id)
    inventory.quantity -= quantity
    await db.commit()
```

### 3. Audit Trail

Every inventory change is logged:

```python
transaction = InventoryTransaction(
    inventory_id=inventory.id,
    transaction_type="ship",
    quantity_change=-5,
    quantity_before=100,
    quantity_after=95,
    performed_by=user_id
)
```

## API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_inventory.py::test_receive_inventory
```

## Deployment

### Docker Compose (Development)

```bash
docker-compose up -d
```

### Kubernetes (Production)

```bash
# Deploy to development
kubectl apply -k k8s/overlays/dev

# Deploy to production
kubectl apply -k k8s/overlays/prod

# Check status
kubectl get pods -n inventory-system

# Access API
kubectl port-forward svc/inventory-api-service 8000:80 -n inventory-system
```

See [KUBERNETES_DEPLOYMENT.md](docs/KUBERNETES_DEPLOYMENT.md) for complete guide.

## Configuration

Environment variables:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/inventory
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
```

## Monitoring

- **Health Check**: GET /health
- **Metrics**: Prometheus-compatible metrics at /metrics
- **Logs**: Structured JSON logging

## Security

- JWT authentication (TODO)
- Role-based access control (TODO)
- API rate limiting
- SQL injection prevention (parameterized queries)
- Input validation (Pydantic)

## Performance

- **Async I/O**: All database operations are async
- **Connection Pooling**: 20 connections, 10 overflow
- **Redis Caching**: Frequently accessed data
- **Database Indexes**: Optimized queries

## License

MIT

## Support

For issues and questions:
- GitHub Issues
- Email: support@example.com
