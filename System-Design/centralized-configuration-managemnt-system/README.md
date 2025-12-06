# Centralized Configuration Management System

A production-ready centralized configuration management service with versioning, hierarchical key-value storage, advanced rollout strategies, client-side caching, real-time change notifications, comprehensive audit logging, and multi-environment support.

## 🚀 Features

- ✅ **Versioned Configurations** - Full version history with rollback support
- ✅ **Hierarchical Key-Value Storage** - Global → App → Environment hierarchy
- ✅ **Advanced Rollout Strategies** - Percentage, canary, feature flags, time-based, user targeting
- ✅ **Client-Side Caching** - Intelligent caching with TTL and auto-refresh
- ✅ **Real-Time Notifications** - RabbitMQ-based change notifications
- ✅ **Comprehensive Audit Logging** - Track all configuration changes
- ✅ **Multi-Environment Support** - Dev, Staging, Production isolation
- ✅ **RESTful API** - FastAPI-based async API
- ✅ **Python Client SDK** - Easy integration with fallback support
- ✅ **Kubernetes-Ready** - Complete K8s manifests included
- ✅ **Monitoring & Metrics** - Prometheus metrics and Grafana dashboards

## 📋 Architecture

```
┌─────────────────┐
│   Client Apps   │
│  (Python SDK)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│     Config Management Service       │
│  ┌──────────┐  ┌────────────────┐  │
│  │ FastAPI  │  │  Business      │  │
│  │   API    │──│    Logic       │  │
│  └──────────┘  └────────────────┘  │
└────┬────────┬──────────┬───────────┘
     │        │          │
     ▼        ▼          ▼
┌──────┐ ┌───────┐ ┌──────────┐
│ PG   │ │ Redis │ │ RabbitMQ │
│ SQL  │ │ Cache │ │  Notify  │
└──────┘ └───────┘ └──────────┘
```

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Message Queue**: RabbitMQ 3
- **ORM**: SQLAlchemy (async)
- **Monitoring**: Prometheus + Grafana
- **Container**: Docker
- **Orchestration**: Kubernetes

## 📦 Quick Start

### Local Development with Docker Compose

1. **Clone the repository**
```bash
cd /home/rk/Documents/labs/System-Design/centralized-configuration-managemnt-system
```

2. **Start all services**
```bash
cd infrastructure/docker
docker-compose up -d
```

3. **Verify services are running**
```bash
docker-compose ps
```

4. **Access the API**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health
- RabbitMQ Management: http://localhost:15672 (guest/guest)

### Using the Python Client SDK

```python
import asyncio
from client_sdk.python.config_client import ConfigClient

async def main():
    # Initialize client
    client = ConfigClient(
        base_url="http://localhost:8000/api/v1",
        app_id="my-app",
        environment="development"
    )
    
    await client.initialize()
    
    # Get configuration
    db_host = client.get("database.host", default="localhost")
    print(f"Database: {db_host}")
    
    # Register change listener
    client.on_change(lambda configs: print("Configs updated!"))
    
    # Start auto-refresh
    await client.start_auto_refresh(interval=60)
    
    await client.close()

asyncio.run(main())
```

## 🔧 Configuration Hierarchy

Configurations are resolved in the following order (later overrides earlier):

1. **Global** - Applies to all apps and environments
2. **App-Level** - Applies to specific app across all environments
3. **Environment-Specific** - Applies to specific app in specific environment

Example:
```
Global:         database.timeout = 30
App-Level:      database.timeout = 60  (overrides global)
Environment:    database.timeout = 120 (overrides app-level)
```

## 📊 API Endpoints

### Configurations
- `POST /api/v1/configs` - Create configuration
- `GET /api/v1/configs` - List configurations
- `GET /api/v1/configs/{id}` - Get configuration
- `PUT /api/v1/configs/{id}` - Update configuration
- `DELETE /api/v1/configs/{id}` - Delete configuration
- `POST /api/v1/configs/fetch` - Fetch configs for client

### Versions
- `GET /api/v1/versions/config/{id}` - Get version history
- `POST /api/v1/versions/rollback/{id}` - Rollback to version

### Rollouts
- `POST /api/v1/rollouts` - Create rollout strategy
- `GET /api/v1/rollouts/{id}` - Get rollout
- `PUT /api/v1/rollouts/{id}` - Update rollout
- `GET /api/v1/rollouts/config/{id}` - Get config rollouts

### Audit
- `GET /api/v1/audit` - Query audit logs
- `GET /api/v1/audit/{id}` - Get audit log entry

### Health
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe

## 🚢 Deployment

### Kubernetes

1. **Create namespace**
```bash
kubectl apply -f infrastructure/kubernetes/namespace.yaml
```

2. **Deploy dependencies**
```bash
kubectl apply -f infrastructure/kubernetes/postgres-statefulset.yaml
kubectl apply -f infrastructure/kubernetes/redis-deployment.yaml
kubectl apply -f infrastructure/kubernetes/rabbitmq-deployment.yaml
```

3. **Deploy config service**
```bash
kubectl apply -f infrastructure/kubernetes/configmap.yaml
kubectl apply -f infrastructure/kubernetes/secrets.yaml
kubectl apply -f infrastructure/kubernetes/deployment.yaml
kubectl apply -f infrastructure/kubernetes/service.yaml
kubectl apply -f infrastructure/kubernetes/ingress.yaml
```

4. **Verify deployment**
```bash
kubectl get pods -n config-management
kubectl logs -f deployment/config-service -n config-management
```

## 📈 Monitoring

### Prometheus Metrics

The service exposes metrics at `/metrics`:
- HTTP request metrics
- Database connection pool metrics
- Cache hit/miss rates
- Configuration fetch metrics
- Rollout evaluation metrics

### Grafana Dashboards

Pre-built dashboards available in `monitoring/grafana/`:
- Service metrics dashboard
- Audit log visualization
- Rollout progress tracking

## 🔐 Security

- **Encryption**: Sensitive configs can be encrypted at rest
- **Authentication**: Integrate with your auth system (JWT, OAuth2)
- **Secrets Management**: Use Kubernetes secrets or external secret managers
- **Audit Logging**: All changes are logged with user, IP, and timestamp

## 📚 Documentation

Detailed documentation available in `docs/`:
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [API Reference](docs/API.md) - Complete API documentation
- [Client Guide](docs/CLIENT_GUIDE.md) - SDK integration guide
- [Deployment](docs/DEPLOYMENT.md) - Deployment instructions
- [Rollout Strategies](docs/ROLLOUT_STRATEGIES.md) - Rollout documentation
- [Security](docs/SECURITY.md) - Security best practices
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues
- [Runbook](docs/RUNBOOK.md) - Operational procedures

## 🧪 Testing

```bash
# Unit tests
pytest tests/unit/ -v --cov=app

# Integration tests
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v

# Performance tests
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/your-org/config-management/issues)
- Documentation: See `docs/` directory
- Email: support@example.com

## 🗺️ Roadmap

- [ ] Web UI for configuration management
- [ ] GraphQL API support
- [ ] Multi-region replication
- [ ] Configuration templates
- [ ] Import/export functionality
- [ ] Advanced RBAC
- [ ] Configuration validation schemas
- [ ] Webhook notifications
- [ ] Slack/Teams integrations

---

Built with ❤️ using FastAPI, PostgreSQL, Redis, and RabbitMQ
