# Complete Jenkins CI/CD Pipeline - Architecture Diagrams

## Table of Contents
1. [Overall System Architecture](#1-overall-system-architecture)
2. [CI/CD Pipeline Flow](#2-cicd-pipeline-flow)
3. [Jenkins Architecture](#3-jenkins-architecture)
4. [Docker Integration](#4-docker-integration)
5. [Kubernetes Deployment](#5-kubernetes-deployment)
6. [Network Architecture](#6-network-architecture)
7. [Data Flow](#7-data-flow)
8. [Component Interactions](#8-component-interactions)

---

## 1. Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE CI/CD SYSTEM                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   DEVELOPER      │
│   WORKSTATION    │
│                  │
│  - IDE/Editor    │
│  - Git Client    │
│  - Local Testing │
└────────┬─────────┘
         │
         │ git push
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SOURCE CODE REPOSITORY                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  GitHub / GitLab / Bitbucket                                       │    │
│  │  - main branch                                                     │    │
│  │  - feature branches                                                │    │
│  │  - Jenkinsfile                                                     │    │
│  │  - Dockerfile                                                      │    │
│  │  - K8s manifests                                                   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└────────┬────────────────────────────────────────────────────────────────────┘
         │
         │ webhook trigger
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          JENKINS SERVER (Ubuntu)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Jenkins Master                                                     │   │
│  │  - Port: 8080 (Web UI)                                             │   │
│  │  - Port: 50000 (Agent)                                             │   │
│  │  - Plugins: Docker, Kubernetes, Git, Pipeline                      │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │   │
│  │  │  Pipeline 1  │  │  Pipeline 2  │  │  Pipeline 3  │            │   │
│  │  │  (Dev)       │  │  (Staging)   │  │  (Prod)      │            │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │   │
│  │                                                                     │   │
│  │  Installed Tools:                                                  │   │
│  │  ✓ Docker CLI                                                      │   │
│  │  ✓ kubectl                                                         │   │
│  │  ✓ Helm                                                            │   │
│  │  ✓ Git                                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Docker Engine                                                      │   │
│  │  - Builds container images                                         │   │
│  │  - Runs build containers                                           │   │
│  │  - Socket: /var/run/docker.sock                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└────────┬────────────────────────────────────────┬───────────────────────────┘
         │                                        │
         │ docker push                            │ kubectl apply
         ▼                                        ▼
┌──────────────────────┐              ┌─────────────────────────────────────┐
│  DOCKER REGISTRY     │              │   KUBERNETES CLUSTER                │
│                      │              │                                     │
│  ┌────────────────┐  │              │  ┌──────────────────────────────┐  │
│  │  Docker Hub    │  │              │  │  Master Node                 │  │
│  │  or            │  │              │  │  - API Server                │  │
│  │  AWS ECR       │  │              │  │  - Scheduler                 │  │
│  │  or            │  │              │  │  - Controller Manager        │  │
│  │  GCR           │  │              │  │  - etcd                      │  │
│  │  or            │  │              │  └──────────────────────────────┘  │
│  │  Harbor        │  │              │                                     │
│  └────────────────┘  │              │  ┌──────────────────────────────┐  │
│                      │              │  │  Worker Nodes (3+)           │  │
│  Images:             │              │  │                              │  │
│  - myapp:v1.0.0      │◄─────────────┼──│  ┌────────────────────────┐ │  │
│  - myapp:v1.0.1      │  image pull  │  │  │  Namespaces:           │ │  │
│  - myapp:latest      │              │  │  │  - production          │ │  │
└──────────────────────┘              │  │  │  - staging             │ │  │
                                      │  │  │  - development         │ │  │
                                      │  │  │                        │ │  │
                                      │  │  │  Each namespace has:   │ │  │
                                      │  │  │  - Deployments         │ │  │
                                      │  │  │  - Services            │ │  │
                                      │  │  │  - Ingress             │ │  │
                                      │  │  │  - ConfigMaps          │ │  │
                                      │  │  │  - Secrets             │ │  │
                                      │  │  │  - HPA                 │ │  │
                                      │  │  └────────────────────────┘ │  │
                                      │  └──────────────────────────────┘  │
                                      └─────────────────┬───────────────────┘
                                                        │
                                                        │ HTTP/HTTPS
                                                        ▼
                                      ┌─────────────────────────────────────┐
                                      │         END USERS                   │
                                      │  - Web Browsers                     │
                                      │  - Mobile Apps                      │
                                      │  - API Clients                      │
                                      └─────────────────────────────────────┘
```

### Architecture Explanation

**Components:**

1. **Developer Workstation**: Where code is written and committed
2. **Git Repository**: Source of truth for code, configurations, and pipeline definitions
3. **Jenkins Server**: Orchestrates the entire CI/CD process
4. **Docker Engine**: Builds and manages container images
5. **Docker Registry**: Stores versioned container images
6. **Kubernetes Cluster**: Runs and manages containerized applications
7. **End Users**: Access the deployed application

**Flow:**
- Developer pushes code → Git webhook triggers Jenkins → Jenkins builds and tests → Docker image created → Image pushed to registry → Kubernetes pulls image → Application deployed → Users access app

---

## 2. CI/CD Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    JENKINS PIPELINE EXECUTION FLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

START
  │
  ▼
┌─────────────────────────────────────────┐
│  STAGE 1: CHECKOUT                      │
│  ┌───────────────────────────────────┐  │
│  │ - Clone Git repository            │  │
│  │ - Checkout specific branch        │  │
│  │ - Get commit hash                 │  │
│  └───────────────────────────────────┘  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  STAGE 2: BUILD APPLICATION             │
│  ┌───────────────────────────────────┐  │
│  │ Node.js:  npm install             │  │
│  │           npm run build           │  │
│  │                                   │  │
│  │ Java:     mvn clean package       │  │
│  │                                   │  │
│  │ Python:   pip install -r req.txt  │  │
│  │           python setup.py build   │  │
│  │                                   │  │
│  │ Go:       go build                │  │
│  └───────────────────────────────────┘  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 3: RUN TESTS (Parallel Execution)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Unit Tests   │  │ Integration  │  │ Lint/Code    │     │
│  │              │  │ Tests        │  │ Quality      │     │
│  │ - Fast       │  │ - DB tests   │  │ - ESLint     │     │
│  │ - Isolated   │  │ - API tests  │  │ - SonarQube  │     │
│  │ - Coverage   │  │ - E2E tests  │  │ - Security   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │            │
│         └──────────────────┴──────────────────┘            │
└────────────────────────────┬────────────────────────────────┘
                             │
                 ┌───────────┴───────────┐
                 │  All tests passed?    │
                 └───────────┬───────────┘
                             │ YES
                             ▼
┌─────────────────────────────────────────┐
│  STAGE 4: BUILD DOCKER IMAGE            │
│  ┌───────────────────────────────────┐  │
│  │ docker build -t myapp:${BUILD}    │  │
│  │                                   │  │
│  │ Multi-stage build:                │  │
│  │ 1. Builder stage                  │  │
│  │    - Install dependencies         │  │
│  │    - Compile code                 │  │
│  │                                   │  │
│  │ 2. Production stage               │  │
│  │    - Copy artifacts               │  │
│  │    - Minimal base image           │  │
│  │    - Non-root user                │  │
│  │    - Health checks                │  │
│  └───────────────────────────────────┘  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  STAGE 5: SECURITY SCAN (Optional)      │
│  ┌───────────────────────────────────┐  │
│  │ Trivy image scan                  │  │
│  │ - Check for vulnerabilities       │  │
│  │ - CVE database                    │  │
│  │ - Severity: HIGH, CRITICAL        │  │
│  └───────────────────────────────────┘  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  STAGE 6: PUSH TO REGISTRY              │
│  ┌───────────────────────────────────┐  │
│  │ docker login                      │  │
│  │ docker tag myapp:${BUILD}         │  │
│  │ docker push myapp:${BUILD}        │  │
│  │ docker push myapp:latest          │  │
│  │ docker push myapp:${GIT_COMMIT}   │  │
│  └───────────────────────────────────┘  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  STAGE 7: DEPLOY TO KUBERNETES          │
│  ┌───────────────────────────────────┐  │
│  │ Method 1: kubectl                 │  │
│  │ kubectl set image deployment/app  │  │
│  │   app=myapp:${BUILD}              │  │
│  │ kubectl rollout status            │  │
│  │                                   │  │
│  │ Method 2: Helm                    │  │
│  │ helm upgrade --install myapp      │  │
│  │   --set image.tag=${BUILD}        │  │
│  └───────────────────────────────────┘  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  STAGE 8: VERIFY DEPLOYMENT             │
│  ┌───────────────────────────────────┐  │
│  │ kubectl get pods                  │  │
│  │ kubectl get svc                   │  │
│  │ Health check endpoint             │  │
│  │ Smoke tests                       │  │
│  └───────────────────────────────────┘  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  STAGE 9: POST-DEPLOYMENT               │
│  ┌───────────────────────────────────┐  │
│  │ - Send notifications (Slack)      │  │
│  │ - Update deployment dashboard     │  │
│  │ - Tag Git release                 │  │
│  │ - Clean workspace                 │  │
│  └───────────────────────────────────┘  │
└────────────────┬────────────────────────┘
                 │
                 ▼
               SUCCESS
                 │
    ┌────────────┴────────────┐
    │  Rollback on Failure?   │
    └────────────┬────────────┘
                 │ YES
                 ▼
    ┌─────────────────────────┐
    │ kubectl rollout undo    │
    │ Notify team             │
    └─────────────────────────┘
```

### Pipeline Stage Details

| Stage | Duration | Purpose | Failure Impact |
|-------|----------|---------|----------------|
| **Checkout** | 5-10s | Get latest code | Pipeline stops |
| **Build** | 1-5min | Compile application | Pipeline stops |
| **Test** | 2-10min | Verify code quality | Pipeline stops |
| **Docker Build** | 1-3min | Create container | Pipeline stops |
| **Security Scan** | 30s-2min | Find vulnerabilities | Warning only |
| **Push** | 30s-2min | Store image | Pipeline stops |
| **Deploy** | 1-3min | Update K8s | Auto-rollback |
| **Verify** | 30s-1min | Confirm deployment | Alert team |

---

## 3. Jenkins Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        JENKINS INTERNAL ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  JENKINS SERVER (Ubuntu 22.04)                                              │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  JENKINS WEB UI (Port 8080)                                        │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │Dashboard │  │  Jobs    │  │ Plugins  │  │  Config  │          │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  JENKINS CORE                                                      │    │
│  │                                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────┐  │    │
│  │  │  Job Scheduler                                              │  │    │
│  │  │  - Monitors Git webhooks                                    │  │    │
│  │  │  - Schedules builds                                         │  │    │
│  │  │  - Manages build queue                                      │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  │                                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────┐  │    │
│  │  │  Executor Pool                                              │  │    │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │    │
│  │  │  │Executor 1│  │Executor 2│  │Executor 3│  │Executor 4│   │  │    │
│  │  │  │ (Busy)   │  │ (Idle)   │  │ (Busy)   │  │ (Idle)   │   │  │    │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  │                                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────┐  │    │
│  │  │  Plugin Manager                                             │  │    │
│  │  │  - Docker Pipeline Plugin                                   │  │    │
│  │  │  - Kubernetes Plugin                                        │  │    │
│  │  │  - Git Plugin                                               │  │    │
│  │  │  - Credentials Plugin                                       │  │    │
│  │  │  - Blue Ocean Plugin                                        │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  JENKINS HOME (/var/lib/jenkins/)                                 │    │
│  │                                                                     │    │
│  │  ├── config.xml              (Main configuration)                 │    │
│  │  ├── jobs/                   (Job definitions)                    │    │
│  │  │   ├── myapp-dev/                                               │    │
│  │  │   ├── myapp-staging/                                           │    │
│  │  │   └── myapp-prod/                                              │    │
│  │  ├── workspace/              (Build workspaces)                   │    │
│  │  ├── plugins/                (Installed plugins)                  │    │
│  │  ├── secrets/                (Credentials)                        │    │
│  │  ├── users/                  (User accounts)                      │    │
│  │  └── logs/                   (Build logs)                         │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  CREDENTIALS STORE (Encrypted)                                     │    │
│  │  - Docker Hub credentials                                          │    │
│  │  - Kubernetes kubeconfig                                           │    │
│  │  - Git SSH keys                                                    │    │
│  │  - API tokens                                                      │    │
│  │  - Secrets                                                         │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Docker Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DOCKER INTEGRATION WITH JENKINS                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  JENKINS CONTAINER (Optional Containerized Setup)                           │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  jenkins/jenkins:lts-jdk17                                         │    │
│  │                                                                     │    │
│  │  Volumes:                                                          │    │
│  │  - jenkins_home:/var/jenkins_home                                 │    │
│  │  - /var/run/docker.sock:/var/run/docker.sock                      │    │
│  │  - /usr/bin/docker:/usr/bin/docker                                │    │
│  │                                                                     │    │
│  │  Installed:                                                        │    │
│  │  ✓ Docker CLI                                                      │    │
│  │  ✓ kubectl                                                         │    │
│  │  ✓ Helm                                                            │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬─────────────────────────────────────────────────┘
                             │
                             │ Uses Docker socket
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  DOCKER ENGINE (Host)                                                       │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  Docker Daemon                                                     │    │
│  │  - Manages containers                                              │    │
│  │  - Builds images                                                   │    │
│  │  - Handles networking                                              │    │
│  │  - Manages volumes                                                 │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  BUILD PROCESS                                                     │    │
│  │                                                                     │    │
│  │  Dockerfile                                                        │    │
│  │  ┌──────────────────────────────────────────────────────────────┐ │    │
│  │  │ FROM node:18-alpine AS builder                               │ │    │
│  │  │ WORKDIR /app                                                 │ │    │
│  │  │ COPY package*.json ./                                        │ │    │
│  │  │ RUN npm install                                              │ │    │
│  │  │ COPY . .                                                     │ │    │
│  │  │ RUN npm run build                                            │ │    │
│  │  │                                                              │ │    │
│  │  │ FROM node:18-alpine                                          │ │    │
│  │  │ WORKDIR /app                                                 │ │    │
│  │  │ COPY --from=builder /app/dist ./dist                        │ │    │
│  │  │ USER node                                                    │ │    │
│  │  │ CMD ["node", "dist/server.js"]                               │ │    │
│  │  └──────────────────────────────────────────────────────────────┘ │    │
│  │                                                                     │    │
│  │  Build Stages:                                                     │    │
│  │  1. Base image pull                                                │    │
│  │  2. Layer creation                                                 │    │
│  │  3. Dependency installation                                        │    │
│  │  4. Application build                                              │    │
│  │  5. Final image assembly                                           │    │
│  │  6. Image tagging                                                  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  IMAGE STORAGE (Local)                                             │    │
│  │                                                                     │    │
│  │  myapp:123        (Build number)                                   │    │
│  │  myapp:abc123     (Git commit)                                     │    │
│  │  myapp:latest     (Latest build)                                   │    │
│  │  myapp:v1.0.0     (Version tag)                                    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬─────────────────────────────────────────────────┘
                             │
                             │ docker push
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  DOCKER REGISTRY                                                            │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  Registry Storage                                                  │    │
│  │                                                                     │    │
│  │  username/myapp                                                    │    │
│  │  ├── 123                                                           │    │
│  │  ├── abc123                                                        │    │
│  │  ├── latest                                                        │    │
│  │  └── v1.0.0                                                        │    │
│  │                                                                     │    │
│  │  Image Layers (Cached):                                            │    │
│  │  - Base OS layer                                                   │    │
│  │  - Dependencies layer                                              │    │
│  │  - Application layer                                               │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Kubernetes Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  CONTROL PLANE (Master Node)                                                │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ API Server   │  │  Scheduler   │  │ Controller   │  │    etcd      │   │
│  │              │  │              │  │  Manager     │  │              │   │
│  │ - REST API   │  │ - Pod        │  │ - Desired    │  │ - Config     │   │
│  │ - Auth       │  │   placement  │  │   state      │  │   store      │   │
│  │ - Validation │  │ - Resources  │  │ - Reconcile  │  │ - Cluster    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ kubectl commands
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  WORKER NODES (3+ nodes for HA)                                             │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  Node 1                                                            │    │
│  │  ┌──────────────────────────────────────────────────────────────┐ │    │
│  │  │  kubelet (Node agent)                                        │ │    │
│  │  └──────────────────────────────────────────────────────────────┘ │    │
│  │  ┌──────────────────────────────────────────────────────────────┐ │    │
│  │  │  kube-proxy (Network proxy)                                  │ │    │
│  │  └──────────────────────────────────────────────────────────────┘ │    │
│  │  ┌──────────────────────────────────────────────────────────────┐ │    │
│  │  │  Container Runtime (Docker/containerd)                       │ │    │
│  │  └──────────────────────────────────────────────────────────────┘ │    │
│  │                                                                     │    │
│  │  ┌──────────────────────────────────────────────────────────────┐ │    │
│  │  │  NAMESPACE: production                                       │ │    │
│  │  │                                                              │ │    │
│  │  │  ┌────────────────────────────────────────────────────────┐ │ │    │
│  │  │  │  Deployment: myapp                                     │ │ │    │
│  │  │  │  Replicas: 3                                           │ │ │    │
│  │  │  │                                                        │ │ │    │
│  │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │ │ │    │
│  │  │  │  │  Pod 1   │  │  Pod 2   │  │  Pod 3   │           │ │ │    │
│  │  │  │  │          │  │          │  │          │           │ │ │    │
│  │  │  │  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │           │ │ │    │
│  │  │  │  │ │myapp │ │  │ │myapp │ │  │ │myapp │ │           │ │ │    │
│  │  │  │  │ │:v1.0 │ │  │ │:v1.0 │ │  │ │:v1.0 │ │           │ │ │    │
│  │  │  │  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │           │ │ │    │
│  │  │  │  │          │  │          │  │          │           │ │ │    │
│  │  │  │  │ CPU: 250m│  │ CPU: 250m│  │ CPU: 250m│           │ │ │    │
│  │  │  │  │ Mem: 256M│  │ Mem: 256M│  │ Mem: 256M│           │ │ │    │
│  │  │  │  │          │  │          │  │          │           │ │ │    │
│  │  │  │  │ Status:  │  │ Status:  │  │ Status:  │           │ │ │    │
│  │  │  │  │ Running  │  │ Running  │  │ Running  │           │ │ │    │
│  │  │  │  └──────────┘  └──────────┘  └──────────┘           │ │ │    │
│  │  │  └────────────────────────────────────────────────────────┘ │ │    │
│  │  │                                                              │ │    │
│  │  │  ┌────────────────────────────────────────────────────────┐ │ │    │
│  │  │  │  Service: myapp-service                                │ │ │    │
│  │  │  │  Type: LoadBalancer                                    │ │ │    │
│  │  │  │  Port: 80 → 3000                                       │ │ │    │
│  │  │  │  Selector: app=myapp                                   │ │ │    │
│  │  │  └────────────────────────────────────────────────────────┘ │ │    │
│  │  │                                                              │ │    │
│  │  │  ┌────────────────────────────────────────────────────────┐ │ │    │
│  │  │  │  Ingress: myapp-ingress                                │ │ │    │
│  │  │  │  Host: myapp.example.com                               │ │ │    │
│  │  │  │  TLS: Enabled                                          │ │ │    │
│  │  │  └────────────────────────────────────────────────────────┘ │ │    │
│  │  │                                                              │ │    │
│  │  │  ┌────────────────────────────────────────────────────────┐ │ │    │
│  │  │  │  ConfigMap: myapp-config                               │ │ │    │
│  │  │  │  - DB_HOST                                             │ │ │    │
│  │  │  │  - LOG_LEVEL                                           │ │ │    │
│  │  │  └────────────────────────────────────────────────────────┘ │ │    │
│  │  │                                                              │ │    │
│  │  │  ┌────────────────────────────────────────────────────────┐ │ │    │
│  │  │  │  Secret: myapp-secrets                                 │ │ │    │
│  │  │  │  - DB_PASSWORD (encrypted)                             │ │ │    │
│  │  │  │  - API_KEY (encrypted)                                 │ │ │    │
│  │  │  └────────────────────────────────────────────────────────┘ │ │    │
│  │  │                                                              │ │    │
│  │  │  ┌────────────────────────────────────────────────────────┐ │ │    │
│  │  │  │  HPA: myapp-hpa                                        │ │ │    │
│  │  │  │  Min: 3, Max: 10                                       │ │ │    │
│  │  │  │  Target CPU: 70%                                       │ │ │    │
│  │  │  └────────────────────────────────────────────────────────┘ │ │    │
│  │  └──────────────────────────────────────────────────────────────┘ │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NETWORK FLOW DIAGRAM                                │
└─────────────────────────────────────────────────────────────────────────────┘

INTERNET
    │
    │ HTTPS (443)
    ▼
┌─────────────────────────────────────┐
│  Load Balancer / Ingress Controller │
│  - SSL Termination                  │
│  - Domain routing                   │
│  - Rate limiting                    │
└────────────┬────────────────────────┘
             │
             │ HTTP (80)
             ▼
┌─────────────────────────────────────┐
│  Kubernetes Service                 │
│  Type: LoadBalancer                 │
│  Port: 80 → 3000                    │
└────────────┬────────────────────────┘
             │
             │ Round-robin load balancing
             ▼
┌────────────────────────────────────────────────────────┐
│              Pod Network (CNI)                         │
│                                                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│  │  Pod 1   │    │  Pod 2   │    │  Pod 3   │        │
│  │ 10.1.1.2 │    │ 10.1.1.3 │    │ 10.1.1.4 │        │
│  │ Port:3000│    │ Port:3000│    │ Port:3000│        │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘        │
│       │               │               │               │
│       └───────────────┴───────────────┘               │
│                       │                               │
└───────────────────────┼───────────────────────────────┘
                        │
                        │ Internal communication
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Backend Services (Same cluster)                        │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Database    │  │  Redis       │  │  Message     │ │
│  │  Service     │  │  Service     │  │  Queue       │ │
│  │  (postgres)  │  │  (redis)     │  │  (rabbitmq)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘

Network Policies:
┌─────────────────────────────────────┐
│  Ingress Rules:                     │
│  - Allow from Ingress Controller    │
│  - Allow from same namespace        │
│                                     │
│  Egress Rules:                      │
│  - Allow to database                │
│  - Allow to external APIs           │
│  - Deny all other traffic           │
└─────────────────────────────────────┘
```

---

## 7. Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE DATA FLOW (End-to-End)                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Developer   │
└──────┬───────┘
       │
       │ 1. git push origin main
       ▼
┌──────────────────────┐
│  GitHub Repository   │
└──────┬───────────────┘
       │
       │ 2. Webhook POST request
       │    Payload: {commit, branch, author}
       ▼
┌──────────────────────────────────────┐
│  Jenkins (Webhook Receiver)          │
│  - Validates payload                 │
│  - Triggers pipeline                 │
└──────┬───────────────────────────────┘
       │
       │ 3. Clone repository
       ▼
┌──────────────────────────────────────┐
│  Jenkins Workspace                   │
│  /var/lib/jenkins/workspace/myapp/   │
│  - Source code                       │
│  - Jenkinsfile                       │
│  - Dockerfile                        │
└──────┬───────────────────────────────┘
       │
       │ 4. Execute build commands
       ▼
┌──────────────────────────────────────┐
│  Build Artifacts                     │
│  - Compiled code                     │
│  - Dependencies                      │
│  - Static assets                     │
└──────┬───────────────────────────────┘
       │
       │ 5. docker build
       ▼
┌──────────────────────────────────────┐
│  Docker Image (Local)                │
│  myapp:123                           │
│  Size: 150MB                         │
└──────┬───────────────────────────────┘
       │
       │ 6. docker push
       │    Authentication: Docker Hub credentials
       ▼
┌──────────────────────────────────────┐
│  Docker Registry                     │
│  docker.io/username/myapp:123        │
└──────┬───────────────────────────────┘
       │
       │ 7. kubectl set image
       │    Authentication: kubeconfig
       ▼
┌──────────────────────────────────────┐
│  Kubernetes API Server               │
│  - Validates request                 │
│  - Updates deployment spec           │
└──────┬───────────────────────────────┘
       │
       │ 8. Scheduler assigns pods
       ▼
┌──────────────────────────────────────┐
│  Worker Nodes                        │
│  - Pull new image                    │
│  - Create new pods                   │
│  - Terminate old pods (rolling)      │
└──────┬───────────────────────────────┘
       │
       │ 9. Service routes traffic
       ▼
┌──────────────────────────────────────┐
│  Running Application                 │
│  - 3 pods running                    │
│  - Health checks passing             │
│  - Serving traffic                   │
└──────┬───────────────────────────────┘
       │
       │ 10. User requests
       ▼
┌──────────────────────────────────────┐
│  End Users                           │
│  - Access via myapp.example.com      │
│  - Load balanced across pods         │
└──────────────────────────────────────┘
```

---

## 8. Component Interactions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPONENT INTERACTION MATRIX                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┬──────────────┬────────────────┬─────────────────────────────┐
│  Component  │  Interacts   │   Protocol     │  Purpose                    │
│             │  With        │                │                             │
├─────────────┼──────────────┼────────────────┼─────────────────────────────┤
│  Developer  │  Git Repo    │  HTTPS/SSH     │  Push code changes          │
├─────────────┼──────────────┼────────────────┼─────────────────────────────┤
│  Git Repo   │  Jenkins     │  Webhook/HTTP  │  Trigger builds             │
├─────────────┼──────────────┼────────────────┼─────────────────────────────┤
│  Jenkins    │  Git Repo    │  HTTPS/SSH     │  Clone repository           │
│             │  Docker      │  Socket/API    │  Build images               │
│             │  Registry    │  HTTPS         │  Push images                │
│             │  Kubernetes  │  HTTPS/API     │  Deploy applications        │
├─────────────┼──────────────┼────────────────┼─────────────────────────────┤
│  Docker     │  Registry    │  HTTPS         │  Push/pull images           │
├─────────────┼──────────────┼────────────────┼─────────────────────────────┤
│  Kubernetes │  Registry    │  HTTPS         │  Pull images                │
│             │  Pods        │  Internal      │  Manage containers          │
├─────────────┼──────────────┼────────────────┼─────────────────────────────┤
│  Pods       │  Service     │  TCP/HTTP      │  Receive traffic            │
│             │  ConfigMap   │  Volume mount  │  Read configuration         │
│             │  Secret      │  Volume mount  │  Read secrets               │
├─────────────┼──────────────┼────────────────┼─────────────────────────────┤
│  Service    │  Ingress     │  HTTP          │  Expose externally          │
├─────────────┼──────────────┼────────────────┼─────────────────────────────┤
│  Ingress    │  End Users   │  HTTPS         │  Serve application          │
└─────────────┴──────────────┴────────────────┴─────────────────────────────┘

Sequence Diagram:

Developer  Git    Jenkins  Docker  Registry  K8s    Pods    Users
    │       │        │       │        │       │       │       │
    ├──────>│        │       │        │       │       │       │
    │ push  │        │       │        │       │       │       │
    │       ├───────>│       │        │       │       │       │
    │       │webhook │       │        │       │       │       │
    │       │        ├──────>│        │       │       │       │
    │       │        │ build │        │       │       │       │
    │       │        │       ├───────>│       │       │       │
    │       │        │       │  push  │       │       │       │
    │       │        ├───────────────────────>│       │       │
    │       │        │       │        │ deploy│       │       │
    │       │        │       │        │       ├──────>│       │
    │       │        │       │        │       │ create│       │
    │       │        │       │        │<──────┤       │       │
    │       │        │       │        │  pull │       │       │
    │       │        │       │        │       │       │<──────┤
    │       │        │       │        │       │       │request│
    │       │        │       │        │       │       ├──────>│
    │       │        │       │        │       │       │response
```

---

## Summary

This comprehensive diagram set illustrates:

1. **Overall Architecture**: Complete system from developer to end user
2. **Pipeline Flow**: Detailed CI/CD stages with timing and failure handling
3. **Jenkins Architecture**: Internal components and file structure
4. **Docker Integration**: Build process and image management
5. **Kubernetes Deployment**: Cluster architecture with all resources
6. **Network Architecture**: Traffic flow and security policies
7. **Data Flow**: End-to-end request/response cycle
8. **Component Interactions**: How all pieces communicate

Each diagram provides a different perspective on the same system, helping you understand both the big picture and the detailed interactions between components.
