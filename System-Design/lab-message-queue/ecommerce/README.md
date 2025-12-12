# E-Commerce Platform

> Complete microservices-based e-commerce platform with Kubernetes deployment

## Overview

Full-featured e-commerce platform with:
- **6 Microservices**: Catalog, Cart, Order, Payment, Inventory, User
- **Kubernetes Ready**: Complete K8s manifests with auto-scaling
- **Event-Driven**: RabbitMQ for async communication
- **Scalable**: Horizontal pod autoscaling
- **Production Ready**: Monitoring, logging, health checks

## Quick Start

```bash
# Deploy to Kubernetes (Development)
kubectl apply -k k8s/overlays/dev

# Deploy to Production
kubectl apply -k k8s/overlays/prod

# Check status
kubectl get pods -n ecommerce

# Access services
kubectl port-forward svc/api-gateway 8080:80 -n ecommerce
```

## Architecture

```
                    ┌─────────────────┐
                    │   API Gateway   │
                    │     (Nginx)     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Catalog    │    │     Cart     │    │    Order     │
│   Service    │    │   Service    │    │   Service    │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                    │
       ▼                   ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │    Redis     │    │  PostgreSQL  │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Services

| Service | Port | Database | Purpose |
|---------|------|----------|---------|
| **Catalog** | 8001 | PostgreSQL | Product management |
| **Cart** | 8002 | Redis | Shopping cart |
| **Order** | 8003 | PostgreSQL | Order processing |
| **Payment** | 8004 | - | Payment gateway |
| **Inventory** | 8005 | PostgreSQL | Stock management |
| **User** | 8006 | PostgreSQL | Authentication |

## Features

✅ **Microservices Architecture** - Independent, scalable services  
✅ **Kubernetes Deployment** - Production-ready manifests  
✅ **Auto-Scaling** - HPA for dynamic scaling  
✅ **Event-Driven** - RabbitMQ for async processing  
✅ **API Gateway** - Nginx for routing  
✅ **Monitoring** - Prometheus + Grafana  
✅ **Distributed Tracing** - Jaeger integration  
✅ **CI/CD Ready** - GitHub Actions workflows  

## Documentation

- **[KUBERNETES_DEPLOYMENT.md](docs/KUBERNETES_DEPLOYMENT.md)** - Complete K8s guide
- **[API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** - API reference
- **[FLOW_DOCUMENTATION.md](docs/FLOW_DOCUMENTATION.md)** - System flows
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Architecture details

## Technology Stack

- **Framework**: FastAPI (Python)
- **Databases**: PostgreSQL, Redis, MongoDB
- **Message Queue**: RabbitMQ
- **Container**: Docker + Kubernetes
- **Monitoring**: Prometheus, Grafana
- **Tracing**: Jaeger

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run service locally
cd services/catalog
uvicorn app.main:app --reload --port 8001

# Run tests
pytest tests/
```

## Deployment

See [KUBERNETES_DEPLOYMENT.md](docs/KUBERNETES_DEPLOYMENT.md) for complete deployment guide.

## License

MIT
