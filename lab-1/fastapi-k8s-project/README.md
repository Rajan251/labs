# FastAPI Production Application

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue.svg)](https://kubernetes.io/)

Production-ready FastAPI application with complete CI/CD pipeline using Jenkins and Kubernetes deployment.

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone <your-repo-url>
cd fastapi-k8s-project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run application
uvicorn app.main:app --reload
```

Visit http://localhost:8000/api/docs for API documentation.

### Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Kubernetes

```bash
# Deploy to Kubernetes
./scripts/deploy.sh prod v1.0.0

# Check status
kubectl get pods -n fastapi-app
```

## 📋 Features

- ✅ **FastAPI Framework** - Modern, fast web framework
- ✅ **Async Support** - Full async/await support
- ✅ **Auto Documentation** - Swagger UI and ReDoc
- ✅ **Docker Ready** - Multi-stage optimized builds
- ✅ **Kubernetes Ready** - Production-grade manifests
- ✅ **CI/CD Pipeline** - Jenkins automation
- ✅ **Auto-scaling** - Horizontal Pod Autoscaler
- ✅ **Health Checks** - Liveness and readiness probes
- ✅ **Security** - Best practices implemented
- ✅ **Monitoring** - Prometheus-ready metrics

## 🏗️ Architecture

```
┌─────────────┐
│   Ingress   │ ← HTTPS/TLS Termination
└──────┬──────┘
       │
┌──────▼──────┐
│   Service   │ ← Load Balancing
└──────┬──────┘
       │
┌──────▼──────┐
│ Deployment  │ ← 3+ Replicas with HPA
│  (Pods)     │
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──▼──┐ ┌─▼───┐
│ DB  │ │Redis│
└─────┘ └─────┘
```

## 📁 Project Structure

```
fastapi-k8s-project/
├── app/                 # Application code
│   ├── api/            # API routes
│   ├── core/           # Core functionality
│   ├── models/         # Database models
│   └── tests/          # Tests
├── k8s/                # Kubernetes manifests
├── scripts/            # Deployment scripts
├── Dockerfile          # Docker build
├── Jenkinsfile         # CI/CD pipeline
└── requirements.txt    # Dependencies
```

## 🔧 Configuration

### Environment Variables

Key configuration variables (see `.env.example` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `development` |
| `DATABASE_URL` | PostgreSQL connection | - |
| `REDIS_HOST` | Redis server host | `localhost` |
| `SECRET_KEY` | JWT secret key | - |
| `LOG_LEVEL` | Logging level | `INFO` |

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 📦 Deployment

### Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (EKS, GKE, AKS, etc.)
- kubectl configured
- Jenkins (for CI/CD)

### Manual Deployment

```bash
# Build Docker image
./scripts/build.sh v1.0.0

# Deploy to Kubernetes
./scripts/deploy.sh prod v1.0.0
```

### CI/CD Pipeline

The Jenkins pipeline automatically:
1. Builds Docker image
2. Runs tests
3. Scans for security vulnerabilities
4. Pushes to registry
5. Deploys to Kubernetes
6. Runs smoke tests

## 📊 API Endpoints

### Health Checks

- `GET /api/v1/health` - General health status
- `GET /api/v1/health/live` - Liveness probe
- `GET /api/v1/health/ready` - Readiness probe

### Users (Example)

- `GET /api/v1/users` - List all users
- `GET /api/v1/users/{id}` - Get user by ID
- `POST /api/v1/users` - Create user
- `DELETE /api/v1/users/{id}` - Delete user

## 🔐 Security

- Non-root container user
- Read-only root filesystem
- Secret management via Kubernetes Secrets
- Security scanning with Trivy
- CORS configuration
- Rate limiting via Ingress

## 📈 Monitoring

### Kubernetes

```bash
# View pod metrics
kubectl top pods -n fastapi-app

# View HPA status
kubectl get hpa -n fastapi-app

# View logs
kubectl logs -f deployment/fastapi-deployment -n fastapi-app
```

### Prometheus Metrics

Metrics available at `/metrics` endpoint (when configured).

## 🐛 Troubleshooting

### Pods not starting?

```bash
kubectl describe pod <pod-name> -n fastapi-app
kubectl logs <pod-name> -n fastapi-app
```

### Database connection issues?

```bash
# Check secrets
kubectl get secret fastapi-secrets -n fastapi-app -o yaml

# Test connectivity
kubectl exec -it <pod-name> -n fastapi-app -- sh
```

### Need to rollback?

```bash
kubectl rollout undo deployment/fastapi-deployment -n fastapi-app
```

## 📚 Documentation

- [Complete Setup Guide](PROJECT_SETUP.md) - Detailed setup instructions
- [API Documentation](http://localhost:8000/api/docs) - Swagger UI
- [ReDoc](http://localhost:8000/api/redoc) - Alternative API docs

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI framework by Sebastián Ramírez
- Kubernetes community
- Jenkins community

---

**Need help?** Check the [PROJECT_SETUP.md](PROJECT_SETUP.md) for detailed instructions.
