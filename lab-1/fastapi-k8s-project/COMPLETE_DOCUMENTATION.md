# Complete Project Documentation

## 📚 Table of Contents

1. [Project Overview](#project-overview)
2. [Complete File Structure](#complete-file-structure)
3. [Technologies Used](#technologies-used)
4. [File-by-File Explanation](#file-by-file-explanation)
5. [How Everything Works Together](#how-everything-works-together)
6. [Execution Flow](#execution-flow)
7. [Deployment Process](#deployment-process)
8. [Architecture Diagram](#architecture-diagram)

---

## 🎯 Project Overview

This is a **production-ready FastAPI application** designed for deployment on Kubernetes with automated CI/CD using Jenkins. It follows modern software engineering best practices and is structured for scalability, maintainability, and reliability.

**Purpose:** A template for building and deploying FastAPI applications in enterprise environments with complete automation from code commit to production deployment.

---

## 📁 Complete File Structure

```
fastapi-k8s-project/
│
├── app/                                    # Application Source Code
│   ├── __init__.py                        # Package initializer
│   ├── main.py                            # Application entry point
│   │
│   ├── api/                               # API Routes
│   │   ├── __init__.py
│   │   └── v1/                            # API Version 1
│   │       ├── __init__.py
│   │       ├── health.py                  # Health check endpoints
│   │       └── users.py                   # User management endpoints
│   │
│   ├── core/                              # Core Application Logic
│   │   ├── __init__.py
│   │   └── config.py                      # Configuration management
│   │
│   ├── models/                            # Database Models (SQLAlchemy)
│   ├── schemas/                           # Pydantic Schemas (Data Validation)
│   ├── services/                          # Business Logic Layer
│   │
│   └── tests/                             # Test Suite
│       ├── __init__.py
│       └── test_health.py                 # Health endpoint tests
│
├── k8s/                                   # Kubernetes Configuration
│   ├── base/                              # Base Kubernetes Manifests
│   │   ├── namespace.yaml                 # Namespace definition
│   │   ├── configmap.yaml                 # Non-sensitive configuration
│   │   ├── secret.yaml                    # Sensitive data (template)
│   │   ├── deployment.yaml                # Application deployment
│   │   ├── service.yaml                   # Service (load balancer)
│   │   ├── ingress.yaml                   # External access routing
│   │   └── hpa.yaml                       # Horizontal Pod Autoscaler
│   │
│   └── overlays/                          # Environment-specific configs
│       ├── dev/                           # Development environment
│       ├── staging/                       # Staging environment
│       └── prod/                          # Production environment
│
├── scripts/                               # Automation Scripts
│   ├── build.sh                           # Docker build & push script
│   └── deploy.sh                          # Kubernetes deployment script
│
├── Dockerfile                             # Multi-stage Docker build
├── docker-compose.yml                     # Local development environment
├── Jenkinsfile                            # CI/CD Pipeline definition
│
├── requirements.txt                       # Python dependencies
├── pytest.ini                             # Test configuration
├── .env.example                           # Environment variables template
├── .dockerignore                          # Docker build exclusions
├── .gitignore                             # Git exclusions
│
├── README.md                              # Quick start guide
├── PROJECT_SETUP.md                       # Detailed setup instructions
└── COMPLETE_DOCUMENTATION.md              # This file
```

---

## 🛠️ Technologies Used

### **Backend Framework**
- **FastAPI** (v0.109+) - Modern, fast web framework for building APIs
  - Why: Automatic API documentation, async support, type validation
  - Features: OpenAPI/Swagger UI, async/await, dependency injection

### **Python Libraries**

#### Core Dependencies
- **Uvicorn** (v0.27+) - ASGI server for running FastAPI
- **Pydantic** (v2.5+) - Data validation using Python type hints
- **Pydantic Settings** - Environment variable management

#### Database
- **SQLAlchemy** (v2.0+) - SQL toolkit and ORM
- **asyncpg** - Async PostgreSQL driver
- **Alembic** - Database migration tool

#### Caching
- **Redis** (v5.0+) - In-memory data store
- **hiredis** - Redis protocol parser (performance)

#### Security
- **python-jose** - JWT token handling
- **passlib** - Password hashing
- **python-multipart** - Form data parsing

#### HTTP Clients
- **httpx** - Async HTTP client
- **aiohttp** - Alternative async HTTP client

#### Testing
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Code coverage reporting

#### Code Quality
- **black** - Code formatter
- **flake8** - Linting
- **mypy** - Type checking
- **isort** - Import sorting

#### Monitoring
- **prometheus-client** - Metrics collection

### **Containerization**
- **Docker** - Container platform
  - Multi-stage builds for optimization
  - Layer caching for faster builds
- **Docker Compose** - Multi-container orchestration for local dev

### **Orchestration**
- **Kubernetes** - Container orchestration platform
  - Deployments - Application lifecycle management
  - Services - Load balancing and service discovery
  - Ingress - External access and routing
  - ConfigMaps - Configuration management
  - Secrets - Sensitive data management
  - HPA - Horizontal Pod Autoscaler

### **CI/CD**
- **Jenkins** - Automation server
  - Declarative Pipeline
  - Docker Pipeline plugin
  - Kubernetes CLI plugin

### **Security Scanning**
- **Trivy** - Container vulnerability scanner
- **SonarQube** - Code quality and security analysis

### **Infrastructure**
- **PostgreSQL** (v15) - Relational database
- **Redis** (v7) - Caching layer
- **Nginx Ingress Controller** - Kubernetes ingress

---

## 📄 File-by-File Explanation

### **Application Files**

#### `app/main.py`
**Purpose:** Application entry point and FastAPI initialization

**What it does:**
- Creates FastAPI application instance
- Configures CORS middleware for cross-origin requests
- Includes API routers (health, users)
- Defines startup/shutdown event handlers
- Sets up global exception handling
- Configures API documentation URLs

**Key Components:**
```python
app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/api/docs",      # Swagger UI
    redoc_url="/api/redoc"     # ReDoc
)
```

**When it runs:** 
- Imported by Uvicorn server
- Executed on application startup

---

#### `app/core/config.py`
**Purpose:** Centralized configuration management

**What it does:**
- Defines all application settings using Pydantic
- Loads environment variables from `.env` file
- Provides type-safe configuration access
- Caches settings for performance

**Key Features:**
- Environment-based configuration (dev/staging/prod)
- Database connection settings
- Redis configuration
- Security settings (JWT secret, algorithm)
- API configuration (CORS, rate limits)

**How it works:**
```python
settings = get_settings()  # Cached singleton
DATABASE_URL = settings.DATABASE_URL
```

---

#### `app/api/v1/health.py`
**Purpose:** Health check endpoints for Kubernetes

**What it does:**
- **`/api/v1/health`** - General health status
- **`/api/v1/health/live`** - Liveness probe (is app running?)
- **`/api/v1/health/ready`** - Readiness probe (can accept traffic?)

**Why it's important:**
- Kubernetes uses these to manage pod lifecycle
- Liveness probe: Restarts pod if failing
- Readiness probe: Removes pod from load balancer if not ready

**Example Response:**
```json
{
  "status": "healthy",
  "service": "FastAPI Production App",
  "version": "1.0.0",
  "timestamp": "2025-11-24T17:18:24Z"
}
```

---

#### `app/api/v1/users.py`
**Purpose:** Example CRUD API for user management

**What it does:**
- GET `/api/v1/users` - List all users
- GET `/api/v1/users/{id}` - Get specific user
- POST `/api/v1/users` - Create new user
- DELETE `/api/v1/users/{id}` - Delete user

**Demonstrates:**
- RESTful API design
- Pydantic models for validation
- HTTP status codes
- Error handling

---

#### `app/tests/test_health.py`
**Purpose:** Unit tests for health endpoints

**What it does:**
- Tests all health check endpoints
- Validates response structure
- Ensures correct status codes

**How to run:**
```bash
pytest app/tests/test_health.py -v
```

---

### **Docker Files**

#### `Dockerfile`
**Purpose:** Build optimized Docker image

**Structure:** Multi-stage build (2 stages)

**Stage 1 - Builder:**
```dockerfile
FROM python:3.11-slim as builder
# Install build dependencies (gcc, g++, libpq-dev)
# Install Python packages
# Creates compiled wheels
```

**Stage 2 - Runtime:**
```dockerfile
FROM python:3.11-slim
# Copy only compiled packages from builder
# No build tools in final image
# Run as non-root user (security)
```

**Benefits:**
- **Smaller image:** ~200MB reduction
- **Faster deployments:** Less data to transfer
- **More secure:** Fewer tools in production
- **Better caching:** Separate dependency and code layers

**Build process:**
```bash
docker build -t fastapi-app:latest .
```

---

#### `docker-compose.yml`
**Purpose:** Local development environment

**Services:**

1. **app** - FastAPI application
   - Mounts source code for hot reload
   - Connects to postgres and redis
   - Exposes port 8000

2. **postgres** - PostgreSQL database
   - Persistent volume for data
   - Health checks
   - Port 5432

3. **redis** - Redis cache
   - Persistent volume
   - Health checks
   - Port 6379

**Usage:**
```bash
docker-compose up -d      # Start all services
docker-compose logs -f    # View logs
docker-compose down       # Stop services
```

---

#### `.dockerignore`
**Purpose:** Exclude files from Docker build context

**What it excludes:**
- Python cache files (`__pycache__`, `*.pyc`)
- Virtual environments (`venv/`, `.venv`)
- Git files (`.git/`, `.gitignore`)
- Documentation (`*.md`, `docs/`)
- Tests and coverage reports
- Environment files (`.env`)
- IDE files (`.vscode/`, `.idea/`)

**Impact:**
- **60% faster builds** (less data to send to Docker daemon)
- Smaller build context
- Better security (no secrets in image)

---

### **Kubernetes Files**

#### `k8s/base/namespace.yaml`
**Purpose:** Create isolated namespace for the application

**What it does:**
- Creates namespace `fastapi-app`
- Provides resource isolation
- Enables RBAC (Role-Based Access Control)
- Allows resource quotas per namespace

**Apply:**
```bash
kubectl apply -f k8s/base/namespace.yaml
```

---

#### `k8s/base/configmap.yaml`
**Purpose:** Store non-sensitive configuration

**Contains:**
- Application settings (name, version, environment)
- API configuration (CORS origins)
- Database pool settings
- Redis connection details
- Performance tuning parameters

**Why separate from code:**
- Change config without rebuilding image
- Different configs per environment
- Share config across multiple pods

**Access in pod:**
```yaml
envFrom:
  - configMapRef:
      name: fastapi-config
```

---

#### `k8s/base/secret.yaml`
**Purpose:** Store sensitive data (template)

**Contains (base64 encoded):**
- Database connection URL with password
- JWT secret key
- Redis password
- External API keys

**⚠️ IMPORTANT:**
- This is a TEMPLATE only
- Never commit real secrets to Git
- Create secrets separately:
```bash
kubectl create secret generic fastapi-secrets \
  --from-literal=DATABASE_URL='postgresql://...' \
  --from-literal=SECRET_KEY='...' \
  -n fastapi-app
```

**Best Practice:**
- Use external secret management (Vault, AWS Secrets Manager)
- Rotate secrets regularly
- Limit access with RBAC

---

#### `k8s/base/deployment.yaml`
**Purpose:** Define how application runs in Kubernetes

**Key Configuration:**

**Replicas:**
```yaml
replicas: 3  # Run 3 copies for high availability
```

**Rolling Update Strategy:**
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1  # Max 1 pod down during update
    maxSurge: 1        # Max 1 extra pod during update
```
**Result:** Zero-downtime deployments

**Resource Limits:**
```yaml
resources:
  requests:
    cpu: 250m      # Guaranteed CPU
    memory: 512Mi  # Guaranteed memory
  limits:
    cpu: 1000m     # Maximum CPU
    memory: 1Gi    # Maximum memory
```

**Health Probes:**

1. **Liveness Probe** - Is the app alive?
   - Checks `/api/v1/health/live`
   - Restarts pod if fails 3 times
   - Checks every 10 seconds

2. **Readiness Probe** - Can it handle traffic?
   - Checks `/api/v1/health/ready`
   - Removes from load balancer if fails
   - Checks every 5 seconds

3. **Startup Probe** - Has it started?
   - Allows 60 seconds for startup
   - Disables other probes until succeeds

**Security:**
```yaml
securityContext:
  runAsNonRoot: true      # Don't run as root
  runAsUser: 1000         # Run as user 1000
  allowPrivilegeEscalation: false
  capabilities:
    drop: [ALL]           # Drop all capabilities
```

**Deploy:**
```bash
kubectl apply -f k8s/base/deployment.yaml -n fastapi-app
```

---

#### `k8s/base/service.yaml`
**Purpose:** Load balancing and service discovery

**What it does:**
- Creates stable IP address for pods
- Load balances traffic across pod replicas
- Provides DNS name: `fastapi-service.fastapi-app.svc.cluster.local`
- Routes external port 80 to container port 8000

**Type: ClusterIP**
- Internal only (not exposed outside cluster)
- Use with Ingress for external access

**How it works:**
```
Client → Service (port 80) → Pod 1 (port 8000)
                           → Pod 2 (port 8000)
                           → Pod 3 (port 8000)
```

---

#### `k8s/base/ingress.yaml`
**Purpose:** External HTTP/HTTPS access to the application

**Features:**

1. **HTTPS/TLS Termination**
   - Handles SSL certificates
   - Redirects HTTP to HTTPS
   - Automatic cert management with cert-manager

2. **Routing**
   - Routes `api.yourdomain.com` to service
   - Path-based routing support
   - Host-based routing support

3. **Security**
   - CORS configuration
   - Rate limiting (100 req/sec)
   - Custom security headers
   - Request size limits (10MB)

4. **Performance**
   - Connection timeouts
   - Proxy settings
   - WebSocket support (optional)

**Flow:**
```
Internet → Ingress Controller (NGINX) → Ingress Rules → Service → Pods
```

**Configure:**
- Update `hosts` with your domain
- Create TLS secret with your certificate

---

#### `k8s/base/hpa.yaml`
**Purpose:** Automatic scaling based on load

**Configuration:**
```yaml
minReplicas: 3   # Always run at least 3 pods
maxReplicas: 10  # Scale up to 10 pods max
```

**Scaling Triggers:**
1. CPU > 70% - Scale up
2. Memory > 80% - Scale up

**Scaling Behavior:**

**Scale Up:**
- Add up to 2 pods per minute
- Or increase by 50% per minute
- Immediate (no stabilization window)

**Scale Down:**
- Remove max 1 pod per minute
- Or decrease by 10% per minute
- Wait 5 minutes before scaling down (prevents flapping)

**How it works:**
```
Load increases → CPU > 70% → HPA adds pods → Load distributed
Load decreases → CPU < 70% → Wait 5 min → HPA removes pods
```

**View status:**
```bash
kubectl get hpa -n fastapi-app
```

---

### **CI/CD Files**

#### `Jenkinsfile`
**Purpose:** Automated CI/CD pipeline

**Pipeline Stages:**

**1. Checkout**
- Clone Git repository
- Display commit information

**2. Build**
- Build Docker image
- Tag with build number and 'latest'
- Add build metadata (date, git commit, version)

**3. Test**
- Run pytest in Docker container
- Generate coverage reports
- Publish test results to Jenkins

**4. Security Scan** (Parallel)
- **Trivy:** Scan Docker image for vulnerabilities
- **SonarQube:** Analyze code quality and security

**5. Push**
- Login to Docker registry
- Push versioned image (`fastapi-app:123`)
- Push latest tag (`fastapi-app:latest`)

**6. Deploy**
- Update Kubernetes deployment with new image
- Wait for rollout to complete (5 min timeout)
- Verify pod status

**7. Smoke Tests**
- Test health endpoints
- Verify application is responding

**Post-Build:**
- Clean up Docker images
- Archive artifacts (test results, reports)
- Send notifications (Slack/email)

**Trigger:**
- Manual build
- Git webhook (automatic on push)
- Scheduled builds

**View:**
- Jenkins Blue Ocean UI
- Console output
- Test reports
- Coverage reports

---

### **Scripts**

#### `scripts/deploy.sh`
**Purpose:** Automated Kubernetes deployment

**What it does:**

1. **Prerequisites Check**
   - Verify kubectl is installed
   - Check cluster connectivity

2. **Namespace Management**
   - Create namespace if doesn't exist

3. **Apply Manifests**
   - Apply all Kubernetes YAML files in order
   - ConfigMap → Secret → Deployment → Service → Ingress → HPA

4. **Update Image**
   - Set new image tag on deployment
   - Trigger rolling update

5. **Wait for Rollout**
   - Monitor deployment progress
   - Timeout after 5 minutes
   - Exit with error if fails

6. **Verification**
   - Check pod status
   - Display service and ingress info
   - Count ready pods

7. **Smoke Tests**
   - Test health endpoint
   - Verify application responds

**Usage:**
```bash
./scripts/deploy.sh prod v1.2.3
```

**Features:**
- Colored output for readability
- Error handling and rollback
- Progress monitoring
- Detailed logging

---

#### `scripts/build.sh`
**Purpose:** Build and push Docker image

**What it does:**

1. **Build Image**
   - Run `docker build`
   - Tag with specified version
   - Tag with 'latest'
   - Add build metadata

2. **Push to Registry**
   - Push versioned tag
   - Push latest tag

3. **Display Info**
   - Show image details
   - Display image size

**Usage:**
```bash
./scripts/build.sh v1.2.3
```

**Environment Variables:**
- `DOCKER_REGISTRY` - Registry URL
- `IMAGE_NAME` - Image name

---

### **Configuration Files**

#### `requirements.txt`
**Purpose:** Python package dependencies

**Categories:**

1. **Framework** - FastAPI, Uvicorn
2. **Validation** - Pydantic
3. **Database** - SQLAlchemy, asyncpg, Alembic
4. **Cache** - Redis, hiredis
5. **Security** - python-jose, passlib
6. **HTTP** - httpx, aiohttp
7. **Monitoring** - prometheus-client
8. **Testing** - pytest, pytest-asyncio, pytest-cov
9. **Code Quality** - black, flake8, mypy, isort

**Install:**
```bash
pip install -r requirements.txt
```

---

#### `.env.example`
**Purpose:** Environment variables template

**Usage:**
```bash
cp .env.example .env
# Edit .env with your values
```

**Categories:**
- Application config
- Database connection
- Redis settings
- Security keys
- Logging levels
- Performance tuning

**⚠️ Never commit `.env` to Git!**

---

#### `pytest.ini`
**Purpose:** Test configuration

**Settings:**
- Test discovery patterns
- Coverage configuration
- Test markers (unit, integration, slow)
- Output formatting

**Run tests:**
```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov=app          # With coverage
```

---

#### `.gitignore`
**Purpose:** Exclude files from version control

**Excludes:**
- Python cache (`__pycache__`, `*.pyc`)
- Virtual environments
- Test artifacts
- Environment files (`.env`)
- Logs
- IDE files

---

## 🔄 How Everything Works Together

### **Local Development Flow**

```
1. Developer writes code in app/
2. Configuration loaded from .env
3. Run with: uvicorn app.main:app --reload
4. Access API at http://localhost:8000
5. View docs at http://localhost:8000/api/docs
6. Run tests: pytest
7. Commit code to Git
```

### **Docker Development Flow**

```
1. Developer writes code
2. docker-compose up -d
3. Docker Compose starts:
   - FastAPI app (with hot reload)
   - PostgreSQL database
   - Redis cache
4. App connects to postgres and redis
5. Access at http://localhost:8000
6. Code changes auto-reload
7. docker-compose down when done
```

### **CI/CD Flow (Jenkins)**

```
1. Developer pushes code to Git
2. Git webhook triggers Jenkins
3. Jenkins Pipeline starts:
   
   Stage 1: Checkout
   ├── Clone repository
   └── Get commit info
   
   Stage 2: Build
   ├── Build Docker image
   └── Tag with build number
   
   Stage 3: Test
   ├── Run pytest in container
   ├── Generate coverage reports
   └── Publish results
   
   Stage 4: Security Scan
   ├── Trivy: Scan image vulnerabilities
   └── SonarQube: Code quality analysis
   
   Stage 5: Push
   ├── Login to Docker registry
   ├── Push versioned image
   └── Push latest tag
   
   Stage 6: Deploy
   ├── Update Kubernetes deployment
   ├── Wait for rollout
   └── Verify pods
   
   Stage 7: Smoke Tests
   ├── Test health endpoints
   └── Verify app is live

4. Application is now running in Kubernetes
```

### **Kubernetes Runtime Flow**

```
1. Deployment creates 3 pod replicas
2. Each pod runs FastAPI container
3. Service load balances across pods
4. Ingress routes external traffic to service
5. ConfigMap provides configuration
6. Secret provides sensitive data
7. HPA monitors CPU/memory
8. If load increases:
   ├── HPA adds more pods (up to 10)
   └── Service automatically includes new pods
9. If load decreases:
   ├── Wait 5 minutes (stabilization)
   └── HPA removes pods (down to 3 minimum)
```

### **Request Flow (Production)**

```
User Request
    ↓
HTTPS (api.yourdomain.com)
    ↓
Ingress Controller (NGINX)
    ├── TLS Termination
    ├── Rate Limiting
    └── CORS Headers
    ↓
Ingress Rules
    ├── Route by host/path
    └── Apply annotations
    ↓
Service (fastapi-service)
    ├── Load balancing
    └── Service discovery
    ↓
Pod (one of 3-10 replicas)
    ├── Liveness probe (is alive?)
    ├── Readiness probe (can serve?)
    └── FastAPI application
        ├── Load config from ConfigMap
        ├── Load secrets from Secret
        ├── Connect to PostgreSQL
        ├── Connect to Redis
        └── Process request
    ↓
Response back to user
```

---

## 🚀 Execution Flow

### **Application Startup Sequence**

```
1. Container starts
2. Python interpreter loads
3. Import app.main
4. Load configuration (app/core/config.py)
   ├── Read environment variables
   ├── Read ConfigMap values (in K8s)
   └── Read Secret values (in K8s)
5. Initialize FastAPI app
6. Configure middleware (CORS)
7. Include routers (health, users)
8. Run startup event handlers
   ├── Connect to database
   ├── Connect to Redis
   └── Initialize resources
9. Uvicorn starts listening on port 8000
10. Health probes start checking
11. Pod marked as Ready
12. Service adds pod to endpoints
13. Application receives traffic
```

### **Request Processing Flow**

```
1. Request arrives at pod
2. Uvicorn receives HTTP request
3. FastAPI routes to endpoint
4. Pydantic validates request data
5. Endpoint function executes
   ├── May query database
   ├── May check cache (Redis)
   └── May call external APIs
6. Response generated
7. Pydantic validates response data
8. FastAPI serializes to JSON
9. Uvicorn sends HTTP response
10. Prometheus metrics updated
```

### **Deployment Update Flow**

```
1. New code pushed to Git
2. Jenkins builds new image (v124)
3. Jenkins pushes to registry
4. Jenkins updates deployment:
   kubectl set image deployment/fastapi-deployment \
     fastapi-app=registry.com/fastapi-app:v124
5. Kubernetes rolling update starts:
   
   Current state: 3 pods (v123)
   
   Step 1: Create 1 new pod (v124)
   ├── Pull new image
   ├── Start container
   ├── Wait for startup probe
   ├── Wait for readiness probe
   └── Pod ready
   
   Step 2: Terminate 1 old pod (v123)
   ├── Remove from service endpoints
   ├── Send SIGTERM
   ├── Wait for graceful shutdown
   └── Pod terminated
   
   Repeat until all pods updated
   
   Final state: 3 pods (v124)

6. Rollout complete
7. Smoke tests verify new version
```

### **Auto-Scaling Flow**

```
1. Traffic increases
2. CPU usage rises to 75%
3. HPA detects CPU > 70% threshold
4. HPA calculates desired replicas:
   desired = current * (current_cpu / target_cpu)
   desired = 3 * (75 / 70) = 3.21 → 4 pods
5. HPA scales deployment to 4 replicas
6. Deployment creates 1 new pod
7. New pod starts and becomes ready
8. Service adds new pod to endpoints
9. Load distributed across 4 pods
10. CPU usage drops to 60%
11. Wait 5 minutes (stabilization window)
12. If still low, scale down to 3 pods
```

---

## 📊 Deployment Process

### **Step 1: Prepare Environment**

```bash
# Install prerequisites
- Docker
- kubectl
- Access to Kubernetes cluster
- Access to Docker registry

# Configure kubectl
kubectl config use-context your-cluster

# Verify connection
kubectl cluster-info
```

### **Step 2: Build Image**

```bash
# Build and push
./scripts/build.sh v1.0.0

# Or manually
docker build -t registry.com/fastapi-app:v1.0.0 .
docker push registry.com/fastapi-app:v1.0.0
```

### **Step 3: Create Secrets**

```bash
# Create secrets (NEVER commit to Git)
kubectl create secret generic fastapi-secrets \
  --from-literal=DATABASE_URL='postgresql://user:pass@host:5432/db' \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=REDIS_PASSWORD='redis-pass' \
  -n fastapi-app
```

### **Step 4: Update Configuration**

```bash
# Edit k8s/base/configmap.yaml
# Update environment-specific values

# Edit k8s/base/ingress.yaml
# Update domain name

# Edit k8s/base/deployment.yaml
# Update image registry and tag
```

### **Step 5: Deploy**

```bash
# Automated deployment
./scripts/deploy.sh prod v1.0.0

# Or manual
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/base/secret.yaml
kubectl apply -f k8s/base/deployment.yaml
kubectl apply -f k8s/base/service.yaml
kubectl apply -f k8s/base/ingress.yaml
kubectl apply -f k8s/base/hpa.yaml
```

### **Step 6: Verify**

```bash
# Check pods
kubectl get pods -n fastapi-app

# Check services
kubectl get svc -n fastapi-app

# Check ingress
kubectl get ingress -n fastapi-app

# View logs
kubectl logs -f deployment/fastapi-deployment -n fastapi-app

# Test health
curl https://api.yourdomain.com/api/v1/health
```

### **Step 7: Monitor**

```bash
# Watch pods
kubectl get pods -n fastapi-app -w

# View HPA status
kubectl get hpa -n fastapi-app

# View events
kubectl get events -n fastapi-app --sort-by='.lastTimestamp'

# View metrics
kubectl top pods -n fastapi-app
```

---

## 🏗️ Architecture Diagram

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                          │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Ingress Controller (NGINX)             │    │
│  │  - TLS Termination                                  │    │
│  │  - Rate Limiting                                    │    │
│  │  - CORS                                             │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼─────────────────────────────┐    │
│  │              Ingress (fastapi-ingress)              │    │
│  │  - Routing Rules                                    │    │
│  │  - Host: api.yourdomain.com                         │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼─────────────────────────────┐    │
│  │           Service (fastapi-service)                 │    │
│  │  - Load Balancing                                   │    │
│  │  - Service Discovery                                │    │
│  │  - ClusterIP: 10.x.x.x                              │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         │                                    │
│         ┌───────────────┼───────────────┐                   │
│         │               │               │                   │
│  ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐            │
│  │   Pod 1     │ │   Pod 2    │ │   Pod 3    │            │
│  │             │ │            │ │            │            │
│  │  FastAPI    │ │  FastAPI   │ │  FastAPI   │  ← HPA     │
│  │  Container  │ │  Container │ │  Container │  (3-10)    │
│  │             │ │            │ │            │            │
│  │  Resources: │ │ Resources: │ │ Resources: │            │
│  │  CPU: 250m  │ │ CPU: 250m  │ │ CPU: 250m  │            │
│  │  Mem: 512Mi │ │ Mem: 512Mi │ │ Mem: 512Mi │            │
│  └──────┬──────┘ └─────┬──────┘ └─────┬──────┘            │
│         │              │              │                     │
│         └──────────────┼──────────────┘                     │
│                        │                                     │
│         ┌──────────────┴──────────────┐                     │
│         │                             │                     │
│  ┌──────▼──────┐              ┌──────▼──────┐              │
│  │  PostgreSQL │              │    Redis    │              │
│  │  Database   │              │    Cache    │              │
│  └─────────────┘              └─────────────┘              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              ConfigMap & Secrets                    │    │
│  │  - Application Config                               │    │
│  │  - Database Credentials                             │    │
│  │  - API Keys                                         │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### **CI/CD Pipeline Architecture**

```
┌──────────────┐
│  Developer   │
└──────┬───────┘
       │ git push
       ↓
┌──────────────┐
│ Git Repository│
│  (GitHub)    │
└──────┬───────┘
       │ webhook
       ↓
┌──────────────────────────────────────────────────────┐
│                    Jenkins                            │
│                                                       │
│  Stage 1: Checkout ──→ Clone repo                    │
│  Stage 2: Build ──────→ Docker build                 │
│  Stage 3: Test ───────→ pytest + coverage            │
│  Stage 4: Security ───→ Trivy + SonarQube            │
│  Stage 5: Push ───────→ Docker registry              │
│  Stage 6: Deploy ─────→ Kubernetes                   │
│  Stage 7: Smoke Tests → Health checks                │
│                                                       │
└──────┬───────────────────────────────────────────────┘
       │
       ├──→ Docker Registry (store images)
       │
       └──→ Kubernetes Cluster (deploy app)
```

### **Data Flow**

```
User Request
    ↓
[Ingress] ──→ TLS, Rate Limit, CORS
    ↓
[Service] ──→ Load Balance
    ↓
[Pod/Container]
    ├──→ [ConfigMap] ──→ App Config
    ├──→ [Secret] ─────→ Credentials
    ├──→ [PostgreSQL] ─→ Persistent Data
    ├──→ [Redis] ──────→ Cache/Session
    └──→ [External API] → Third-party services
    ↓
Response to User
```

---

## 🎓 Summary

This project demonstrates a **complete, production-ready FastAPI application** with:

✅ **Modern Python development** (FastAPI, Pydantic, async/await)  
✅ **Containerization** (Docker multi-stage builds)  
✅ **Orchestration** (Kubernetes with auto-scaling)  
✅ **CI/CD automation** (Jenkins pipeline)  
✅ **Security best practices** (secrets management, non-root containers)  
✅ **High availability** (multiple replicas, health checks)  
✅ **Observability** (health endpoints, metrics, logging)  
✅ **Comprehensive documentation** (every file explained)

**Every component works together** to provide a scalable, reliable, and maintainable application infrastructure suitable for enterprise production environments.

---

**For more information, see:**
- [README.md](README.md) - Quick start
- [PROJECT_SETUP.md](PROJECT_SETUP.md) - Detailed setup
- [walkthrough.md](walkthrough.md) - Component walkthrough
