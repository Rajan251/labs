# 1. Project Overview

## What is This Project?

This project demonstrates building a production-ready **CI/CD pipeline** using Jenkins running on Ubuntu Server, integrated with Docker for containerization and Kubernetes for orchestration.

### Key Components

| Technology | Purpose | Why Use It |
|------------|---------|------------|
| **Jenkins** | CI/CD Orchestration | Industry standard, extensible, large plugin ecosystem |
| **Docker** | Containerization | Consistent environments, portability, isolation |
| **Kubernetes** | Orchestration | Auto-scaling, self-healing, declarative deployments |
| **Ubuntu Server** | Host OS | Stable, well-documented, wide community support |

## Why Jenkins + Docker + Kubernetes?

### Jenkins
- **Automation**: Automates build, test, and deployment processes
- **Extensibility**: 1,800+ plugins for integration with various tools
- **Pipeline as Code**: Define pipelines in Jenkinsfile (version controlled)
- **Distributed Builds**: Scale with multiple agents

### Docker
- **Consistency**: "Works on my machine" → "Works everywhere"
- **Isolation**: Each application runs in its own container
- **Efficiency**: Lightweight compared to VMs
- **Portability**: Build once, run anywhere

### Kubernetes
- **Self-Healing**: Automatically restarts failed containers
- **Auto-Scaling**: Scale based on CPU/memory usage
- **Rolling Updates**: Zero-downtime deployments
- **Service Discovery**: Built-in load balancing and DNS

## Pipeline Workflow

```
┌─────────────┐
│  Developer  │
│             │
│ Writes Code │
└──────┬──────┘
       │
       │ git push
       ▼
┌─────────────────┐
│   Git Repository│
│  (GitHub/GitLab)│
└──────┬──────────┘
       │
       │ Webhook Trigger
       ▼
┌─────────────────────────────────────────┐
│          Jenkins Pipeline               │
│                                         │
│  Stage 1: Checkout                      │
│    └─ Clone repository                  │
│                                         │
│  Stage 2: Build                         │
│    └─ Compile code (Maven/npm/pip)      │
│                                         │
│  Stage 3: Test                          │
│    └─ Run unit & integration tests      │
│                                         │
│  Stage 4: Docker Build                  │
│    └─ Build container image             │
│                                         │
│  Stage 5: Docker Push                   │
│    └─ Push to registry                  │
│                                         │
│  Stage 6: Deploy to Kubernetes          │
│    └─ kubectl apply / helm upgrade      │
│                                         │
│  Stage 7: Verify                        │
│    └─ Health checks & smoke tests       │
└──────┬──────────────────────────────────┘
       │
       │ Image pushed
       ▼
┌──────────────────┐
│ Docker Registry  │
│                  │
│ - Docker Hub     │
│ - AWS ECR        │
│ - Google GCR     │
│ - Harbor         │
└──────────────────┘
       │
       │ Pull image
       ▼
┌─────────────────────────────────────────┐
│      Kubernetes Cluster                 │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Namespace: production            │  │
│  │                                   │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  Deployment                 │  │  │
│  │  │  - Replica 1 (Pod)          │  │  │
│  │  │  - Replica 2 (Pod)          │  │  │
│  │  │  - Replica 3 (Pod)          │  │  │
│  │  └─────────────────────────────┘  │  │
│  │              │                    │  │
│  │              ▼                    │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  Service (LoadBalancer)     │  │  │
│  │  └─────────────────────────────┘  │  │
│  │              │                    │  │
│  │              ▼                    │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  Ingress Controller         │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└──────┬──────────────────────────────────┘
       │
       │ HTTP/HTTPS
       ▼
┌─────────────────┐
│   End Users     │
└─────────────────┘
```

## Detailed Workflow Steps

### 1. Code Commit
Developer commits code to Git repository (GitHub, GitLab, Bitbucket)

### 2. Webhook Trigger
Git repository sends webhook to Jenkins, triggering the pipeline

### 3. Checkout Stage
Jenkins clones the repository to the workspace

### 4. Build Stage
- **Java**: Maven/Gradle compiles code
- **Node.js**: npm install and build
- **Python**: pip install dependencies
- **Go**: go build

### 5. Test Stage
- Unit tests
- Integration tests
- Code coverage reports
- Static code analysis (SonarQube)

### 6. Docker Build Stage
- Read Dockerfile
- Build container image
- Tag with version (e.g., v1.2.3, build number)

### 7. Docker Push Stage
- Authenticate to registry
- Push image with tags
- Update image manifest

### 8. Deploy Stage
- Connect to Kubernetes cluster
- Apply manifests or Helm charts
- Rolling update deployment
- Wait for rollout completion

### 9. Verification Stage
- Check pod status
- Run health checks
- Smoke tests
- Send notifications (Slack, email)

## Benefits of This Approach

### For Developers
- ✅ **Fast Feedback**: Know immediately if code breaks
- ✅ **Consistent Environments**: Same container everywhere
- ✅ **Easy Rollbacks**: Revert to previous version quickly
- ✅ **Focus on Code**: Infrastructure handled automatically

### For Operations
- ✅ **Automated Deployments**: No manual intervention
- ✅ **Scalability**: Handle increased load automatically
- ✅ **Monitoring**: Built-in health checks and logs
- ✅ **Disaster Recovery**: Self-healing capabilities

### For Business
- ✅ **Faster Time to Market**: Deploy multiple times per day
- ✅ **Reduced Downtime**: Zero-downtime deployments
- ✅ **Cost Efficiency**: Optimize resource usage
- ✅ **Quality Assurance**: Automated testing catches bugs early

## Architecture Components

### Jenkins Server
- **Master Node**: Orchestrates pipelines, manages configuration
- **Agent Nodes** (optional): Execute builds in parallel
- **Plugins**: Extend functionality (Docker, Kubernetes, Git)

### Docker
- **Docker Engine**: Runs containers
- **Docker Registry**: Stores images
- **Docker Compose**: Multi-container applications

### Kubernetes Cluster
- **Master Node**: API server, scheduler, controller manager
- **Worker Nodes**: Run application pods
- **etcd**: Distributed key-value store
- **kubectl**: Command-line tool
- **Helm**: Package manager for Kubernetes

## Real-World Example

**Scenario**: E-commerce application with microservices

```
Frontend (React) ──┐
                   │
API Gateway ───────┼──→ Jenkins Pipeline ──→ Kubernetes
                   │
Product Service ───┤
                   │
Order Service ─────┤
                   │
Payment Service ───┘
```

Each service has:
- Own Git repository
- Own Jenkinsfile
- Own Dockerfile
- Own Kubernetes deployment

**Pipeline triggers**:
- Developer pushes to `main` branch
- Webhook triggers Jenkins
- Jenkins builds and tests service
- Docker image created and pushed
- Kubernetes deployment updated
- New pods rolled out
- Old pods terminated gracefully

## Next Steps

Proceed to [Ubuntu Server Setup](02-ubuntu-setup.md) to begin implementation.
