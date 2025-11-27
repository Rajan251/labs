# FastAPI Production Project - Complete Setup Guide

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Local Development Setup](#local-development-setup)
5. [Docker Setup](#docker-setup)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Jenkins CI/CD Pipeline](#jenkins-cicd-pipeline)
8. [Environment Configuration](#environment-configuration)
9. [Testing](#testing)
10. [Monitoring and Logging](#monitoring-and-logging)
11. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

This is a production-ready FastAPI application with complete CI/CD pipeline using Jenkins and Kubernetes deployment.

**Key Features:**
- FastAPI web framework with async support
- Multi-stage Docker builds for optimized images
- Kubernetes deployment with auto-scaling
- Jenkins CI/CD pipeline with automated testing
- Health checks and monitoring
- Security best practices

---

## 📁 Project Structure

```
fastapi-k8s-project/
├── app/                          # Application source code
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API routes
│   │   └── v1/
│   │       ├── health.py         # Health check endpoints
│   │       └── users.py          # User management endpoints
│   ├── core/                     # Core functionality
│   │   └── config.py             # Configuration management
│   ├── models/                   # Database models
│   ├── schemas/                  # Pydantic schemas
│   ├── services/                 # Business logic
│   └── tests/                    # Test files
│
├── k8s/                          # Kubernetes manifests
│   └── base/
│       ├── namespace.yaml        # Namespace definition
│       ├── configmap.yaml        # Configuration data
│       ├── secret.yaml           # Sensitive data (template)
│       ├── deployment.yaml       # Application deployment
│       ├── service.yaml          # Service definition
│       ├── ingress.yaml          # Ingress rules
│       └── hpa.yaml              # Horizontal Pod Autoscaler
│
├── scripts/                      # Deployment scripts
│   ├── deploy.sh                 # Kubernetes deployment script
│   └── build.sh                  # Docker build script
│
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Local development environment
├── Jenkinsfile                   # CI/CD pipeline definition
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .dockerignore                 # Docker build exclusions
└── README.md                     # Project documentation
```

---

## ✅ Prerequisites

### Required Software

1. **Python 3.11+**
   ```bash
   python --version
   ```

2. **Docker & Docker Compose**
   ```bash
   docker --version
   docker-compose --version
   ```

3. **Kubernetes CLI (kubectl)**
   ```bash
   kubectl version --client
   ```

4. **Git**
   ```bash
   git --version
   ```

### Optional (for production)

5. **Jenkins** - For CI/CD pipeline
6. **Kubernetes Cluster** - EKS, GKE, AKS, or on-premise
7. **Docker Registry** - Docker Hub, ECR, GCR, or ACR

---

## 🚀 Local Development Setup

### Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd fastapi-k8s-project
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Important variables to configure:**
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `REDIS_HOST` - Redis server host

### Step 5: Run the Application

```bash
# Run with uvicorn (development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python -m app.main
```

### Step 6: Access the Application

- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/api/v1/health

---

## 🐳 Docker Setup

### Build Docker Image

```bash
# Build the image
docker build -t fastapi-app:latest .

# Or use the build script
./scripts/build.sh latest
```

### Run with Docker Compose

```bash
# Start all services (app, postgres, redis)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Docker Compose Services

The `docker-compose.yml` includes:
- **app**: FastAPI application
- **postgres**: PostgreSQL database
- **redis**: Redis cache

---

## ☸️ Kubernetes Deployment

### Step 1: Prepare Kubernetes Cluster

Ensure you have access to a Kubernetes cluster:

```bash
# Check cluster connection
kubectl cluster-info

# View current context
kubectl config current-context
```

### Step 2: Create Secrets

**IMPORTANT**: Never commit secrets to Git!

```bash
# Method 1: Create from literals
kubectl create secret generic fastapi-secrets \
  --from-literal=DATABASE_URL='postgresql://user:pass@host:5432/db' \
  --from-literal=SECRET_KEY='your-secret-key' \
  -n fastapi-app

# Method 2: Create from .env file
kubectl create secret generic fastapi-secrets \
  --from-env-file=.env.production \
  -n fastapi-app
```

### Step 3: Update Image Registry

Edit `k8s/base/deployment.yaml` and update the image:

```yaml
image: your-registry.com/fastapi-app:v1.0.0
```

### Step 4: Deploy to Kubernetes

```bash
# Option 1: Use deployment script (recommended)
./scripts/deploy.sh prod v1.0.0

# Option 2: Apply manifests manually
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/base/secret.yaml
kubectl apply -f k8s/base/deployment.yaml
kubectl apply -f k8s/base/service.yaml
kubectl apply -f k8s/base/ingress.yaml
kubectl apply -f k8s/base/hpa.yaml
```

### Step 5: Verify Deployment

```bash
# Check pods
kubectl get pods -n fastapi-app

# Check services
kubectl get svc -n fastapi-app

# Check ingress
kubectl get ingress -n fastapi-app

# View logs
kubectl logs -f deployment/fastapi-deployment -n fastapi-app

# Check pod details
kubectl describe pod <pod-name> -n fastapi-app
```

### Step 6: Access the Application

```bash
# Get ingress URL
kubectl get ingress fastapi-ingress -n fastapi-app

# Test health endpoint
curl https://your-domain.com/api/v1/health
```

---

## 🔄 Jenkins CI/CD Pipeline

### Pipeline Stages

The Jenkins pipeline (`Jenkinsfile`) includes:

1. **Checkout** - Clone repository
2. **Build** - Build Docker image
3. **Test** - Run unit tests
4. **Security Scan** - Trivy & SonarQube
5. **Push** - Push to Docker registry
6. **Deploy** - Deploy to Kubernetes
7. **Smoke Tests** - Verify deployment

### Setup Jenkins

#### Step 1: Install Required Plugins

- Docker Pipeline
- Kubernetes CLI
- SonarQube Scanner
- Pipeline

#### Step 2: Configure Credentials

Add these credentials in Jenkins:

1. **docker-registry-credentials**
   - Type: Username with password
   - ID: `docker-registry-credentials`
   - Username: Your registry username
   - Password: Your registry password

2. **kubernetes-credentials**
   - Type: Secret file
   - ID: `kubernetes-credentials`
   - File: Your kubeconfig file

3. **sonarqube-token**
   - Type: Secret text
   - ID: `sonarqube-token`
   - Secret: Your SonarQube token

#### Step 3: Create Jenkins Pipeline

1. Create new Pipeline job
2. Configure SCM (Git repository)
3. Set Pipeline script path to `Jenkinsfile`
4. Save and run

#### Step 4: Configure Webhooks (Optional)

For automatic builds on Git push:

1. In Jenkins job, enable "GitHub hook trigger"
2. In GitHub/GitLab, add webhook:
   - URL: `http://jenkins-url/github-webhook/`
   - Events: Push events

---

## ⚙️ Environment Configuration

### Development Environment

```bash
ENVIRONMENT=development
PROJECT_NAME=FastAPI Dev App
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db
REDIS_HOST=localhost
LOG_LEVEL=DEBUG
```

### Staging Environment

```bash
ENVIRONMENT=staging
PROJECT_NAME=FastAPI Staging App
DATABASE_URL=postgresql://user:pass@staging-db:5432/fastapi_db
REDIS_HOST=staging-redis
LOG_LEVEL=INFO
```

### Production Environment

```bash
ENVIRONMENT=production
PROJECT_NAME=FastAPI Production App
DATABASE_URL=postgresql://user:pass@prod-db:5432/fastapi_db
REDIS_HOST=prod-redis
LOG_LEVEL=WARNING
SECRET_KEY=<strong-secret-key>
```

---

## 🧪 Testing

### Run Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_health.py

# Run with verbose output
pytest -v
```

### Run Tests in Docker

```bash
docker-compose run app pytest
```

---

## 📊 Monitoring and Logging

### Health Checks

- **Liveness**: `/api/v1/health/live` - Is the app running?
- **Readiness**: `/api/v1/health/ready` - Is the app ready for traffic?
- **Health**: `/api/v1/health` - General health status

### Kubernetes Monitoring

```bash
# View pod metrics
kubectl top pods -n fastapi-app

# View HPA status
kubectl get hpa -n fastapi-app

# View events
kubectl get events -n fastapi-app --sort-by='.lastTimestamp'
```

### Application Logs

```bash
# View logs
kubectl logs -f deployment/fastapi-deployment -n fastapi-app

# View logs from specific pod
kubectl logs -f <pod-name> -n fastapi-app

# View previous container logs
kubectl logs <pod-name> -n fastapi-app --previous
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n fastapi-app

# Common causes:
# - Image pull errors (check registry credentials)
# - Resource limits (check node resources)
# - Configuration errors (check configmap/secrets)
```

#### 2. Database Connection Errors

```bash
# Verify DATABASE_URL in secrets
kubectl get secret fastapi-secrets -n fastapi-app -o yaml

# Check database connectivity from pod
kubectl exec -it <pod-name> -n fastapi-app -- sh
# Inside pod:
ping postgres-service
```

#### 3. Ingress Not Working

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress configuration
kubectl describe ingress fastapi-ingress -n fastapi-app

# Verify DNS points to ingress IP
kubectl get ingress fastapi-ingress -n fastapi-app
```

#### 4. Image Pull Errors

```bash
# Create image pull secret
kubectl create secret docker-registry registry-credentials \
  --docker-server=your-registry.com \
  --docker-username=your-username \
  --docker-password=your-password \
  -n fastapi-app

# Add to deployment
imagePullSecrets:
- name: registry-credentials
```

### Rollback Deployment

```bash
# View rollout history
kubectl rollout history deployment/fastapi-deployment -n fastapi-app

# Rollback to previous version
kubectl rollout undo deployment/fastapi-deployment -n fastapi-app

# Rollback to specific revision
kubectl rollout undo deployment/fastapi-deployment --to-revision=2 -n fastapi-app
```

### Scale Deployment

```bash
# Manual scaling
kubectl scale deployment/fastapi-deployment --replicas=5 -n fastapi-app

# Check scaling status
kubectl get pods -n fastapi-app -w
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Jenkins Documentation](https://www.jenkins.io/doc/)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License.
