
# Production-Ready GitLab CI/CD Pipeline Guide

> **Comprehensive guide to implementing end-to-end GitLab CI/CD pipelines with Auto DevOps, security scanning, Container Registry, and deployment automation**

---

## Table of Contents

1. [Executive Summary & Goals](#1-executive-summary--goals)
2. [Prerequisites & Assumptions](#2-prerequisites--assumptions)
3. [Architecture & Workflow Diagram](#3-architecture--workflow-diagram)
4. [GitLab CI Fundamentals Recap](#4-gitlab-ci-fundamentals-recap)
5. [Runners: Setup & Recommended Executors](#5-runners-setup--recommended-executors)
6. [Enabling & Customizing Auto DevOps](#6-enabling--customizing-auto-devops)
7. [Container Registry Usage & Policies](#7-container-registry-usage--policies)
8. [Security Scanning Integration](#8-security-scanning-integration)
9. [Full Sample .gitlab-ci.yml](#9-full-sample-gitlab-ciyml)
10. [Docker Build & Push Job Examples](#10-docker-build--push-job-examples)
11. [Kubernetes Deployment Example](#11-kubernetes-deployment-example)
12. [Secrets & Credentials Management](#12-secrets--credentials-management)
13. [Pipeline Optimization & Scaling](#13-pipeline-optimization--scaling)
14. [Observability: Logs, Monitoring & Alerts](#14-observability-logs-monitoring--alerts)
15. [Governance, Permissions & Approvals](#15-governance-permissions--approvals)
16. [CI/CD for Monorepos & Multi-Project Pipelines](#16-cicd-for-monorepos--multi-project-pipelines)
17. [Testing the Pipeline & Local Debugging](#17-testing-the-pipeline--local-debugging)
18. [Common Problems & Solutions](#18-common-problems--solutions)
19. [Compliance & Security Lifecycle](#19-compliance--security-lifecycle)
20. [Example Repository Layout & Deliverables](#20-example-repository-layout--deliverables)
21. [Example MR Checklist](#21-example-mr-checklist)
22. [Rollback & Release Strategies](#22-rollback--release-strategies)
23. [Maintenance & Housekeeping](#23-maintenance--housekeeping)
24. [Advanced Topics / Optional Add-ons](#24-advanced-topics--optional-add-ons)
25. [Final Deliverables & File List](#25-final-deliverables--file-list)
26. [Next Steps & Summary](#26-next-steps--summary)

---

## 1. Executive Summary & Goals

### What This Guide Delivers

This guide provides a **complete, production-ready GitLab CI/CD pipeline** that automates your software delivery from commit to production. The pipeline flow covers:

```
Commit → Build → Test → Security Scans → Container Image → Registry Push → Deploy → Monitor
```

You'll learn to leverage GitLab's integrated features including:
- **Auto DevOps** for zero-config CI/CD
- **Security scanning** (SAST, DAST, Dependency, Container)
- **GitLab Container Registry** for artifact storage
- **Kubernetes & VM deployments** with review apps
- **Vulnerability management** and compliance workflows

### Primary Objectives

1. **Fast Feedback Loops** - Developers get build, test, and security results in minutes
2. **Secure Delivery** - Automated vulnerability detection before code reaches production
3. **Auto DevOps Integration** - Leverage GitLab's built-in templates where appropriate
4. **Container Registry** - Store and manage Docker images with promotion strategies
5. **Vulnerability Management** - Track, triage, and remediate security findings
6. **Production Readiness** - Deploy with confidence using automated testing and rollback capabilities

### Who This Guide Is For

Experienced developers and DevOps engineers comfortable with:
- Linux command line and shell scripting
- Docker and containerization concepts
- Git workflows and branching strategies
- Basic Kubernetes knowledge (for K8s deployments)

You may be new to GitLab's advanced CI/CD features - this guide will bring you up to speed with hands-on, runnable examples.

---

## 2. Prerequisites & Assumptions

### GitLab Edition

This guide covers both **GitLab Community Edition (CE)** and **Enterprise Edition (EE)**. Feature differences are noted where relevant:

| Feature | CE | EE |
|---------|----|----|
| Basic CI/CD pipelines | ✅ | ✅ |
| Container Registry | ✅ | ✅ |
| SAST scanning | ✅ | ✅ |
| Dependency scanning | ✅ | ✅ |
| Container scanning | ✅ | ✅ |
| DAST scanning | ✅ | ✅ |
| Security Dashboard | ❌ | ✅ |
| Vulnerability Management | ❌ | ✅ |
| Merge Request Approvals (advanced) | ❌ | ✅ |
| Multiple Approval Rules | ❌ | ✅ |
| Code Quality (full features) | ❌ | ✅ |

> **Note**: GitLab.com (SaaS) offers many EE features on free tier. Self-hosted CE has more limitations.

### Required Permissions

- **Project Maintainer or Owner** role for CI/CD configuration
- **Runner administration** rights (for self-hosted runners)
- **Kubernetes cluster admin** (if deploying to K8s)
- **Registry write access** for pushing images

### Required Tools & Accounts

#### Essential
- **GitLab Project** - GitLab.com or self-hosted instance (v15.0+ recommended)
- **Git Client** - v2.30+
- **Docker** - v20.10+ (for local testing and runner)
- **GitLab Runner** - v15.0+ (matching GitLab version)

#### For Kubernetes Deployments
- **kubectl** - v1.24+ (matching cluster version ±1)
- **Helm** - v3.10+ (optional, for Helm deployments)
- **Kubernetes Cluster** - v1.24+ with RBAC enabled
- **kubeconfig** - with appropriate namespace access

#### For VM Deployments
- **SSH access** to target servers
- **Ansible** - v2.12+ (optional, for configuration management)

### Recommended Versions

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| GitLab | 15.0 | 16.5+ | Security features improve with versions |
| GitLab Runner | 15.0 | Match GitLab | Version mismatch can cause issues |
| Docker | 20.10 | 24.0+ | For runner and local testing |
| Kubernetes | 1.24 | 1.28+ | Older versions lack security features |
| kubectl | 1.24 | Match cluster | ±1 version skew supported |
| Helm | 3.8 | 3.13+ | Helm 2 is deprecated |

> **Version Compatibility**: Always try to match GitLab Runner version with GitLab instance version. Minor version differences are usually acceptable, but major version gaps can cause compatibility issues.

### Assumptions

This guide assumes:
- You have a GitLab project (new or existing)
- You can create/register GitLab Runners (or have access to shared runners)
- You have basic familiarity with YAML syntax
- You understand Docker basics (images, containers, registries)
- You have a target deployment environment (K8s cluster or VMs)

---

## 3. Architecture & Workflow Diagram

### High-Level Pipeline Architecture

```
┌─────────────┐
│  Developer  │
│  Workstation│
└──────┬──────┘
       │ git push
       ▼
┌────────────────────────────────────────────────────────────────┐
│                         GitLab Instance                        │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │   Source   │  │  CI/CD       │  │  Container Registry    │  │
│  │  Repository│──│  Pipeline    │──│  (Artifacts Storage)   │  │
│  └────────────┘  └──────┬───────┘  └────────────────────────┘  │
└────────────────────────┼───────────────────────────────────────┘
                         │
                         │ Job execution
                         ▼
              ┌──────────────────────┐
              │   GitLab Runner(s)   │
              │  ┌────────────────┐  │
              │  │  Build Stage   │  │
              │  ├────────────────┤  │
              │  │  Test Stage    │  │
              │  ├────────────────┤  │
              │  │ Security Scans │  │
              │  │ • SAST         │  │
              │  │ • Dependency   │  │
              │  │ • Container    │  │
              │  │ • DAST         │  │
              │  ├────────────────┤  │
              │  │ Image Build    │  │
              │  └────────────────┘  │
              └──────────┬───────────┘
                         │
                         │ Push image
                         ▼
              ┌──────────────────────┐
              │  Container Registry  │
              │  • Dev images        │
              │  • Staging images    │
              │  • Production images │
              └──────────┬───────────┘
                         │
                         │ Deploy
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Review    │  │   Staging   │  │ Production  │
│    Apps     │  │ Environment │  │ Environment │
│ (K8s/VMs)   │  │ (K8s/VMs)   │  │ (K8s/VMs)   │
└─────────────┘  └─────────────┘  └─────────────┘
       │                │                │
       └────────────────┴────────────────┘
                        │
                        ▼
              ┌──────────────────────┐
              │    Monitoring        │
              │  • Prometheus        │
              │  • Grafana           │
              │  • GitLab Metrics    │
              └──────────────────────┘
```

### Pipeline Stages Flow

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ PREPARE  │──▶│  BUILD   │──▶│   TEST   │──▶│ SECURITY │──▶│  PACKAGE │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                                    │
                                                                    ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ CLEANUP  │◀──│  DEPLOY  │◀──│  REVIEW  │◀──│   PUSH   │◀──│  IMAGE   │
│          │   │   PROD   │   │   APPS   │   │ REGISTRY │   │  BUILD   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

### Branching Model & Pipeline Triggers

```
feature/xyz ──┐
              ├──▶ Merge Request ──▶ Pipeline (Build, Test, SAST, Review App)
main ─────────┘                                    │
                                                   │ Approved & Merged
                                                   ▼
main ─────────────────────────────────────▶ Pipeline (Full + Deploy Staging)
                                                   │
                                                   │ Tag created
                                                   ▼
v1.2.3 (tag) ──────────────────────────────▶ Pipeline (Full + Deploy Production)
```

### Pipeline Execution by Event

| Event | Stages Executed | Environments |
|-------|----------------|--------------|
| **Push to feature branch** | prepare, build, test, security | None |
| **Merge Request created** | prepare, build, test, security, image-build, push, deploy-review | Review app (ephemeral) |
| **Push to main branch** | All stages | Staging |
| **Tag created (v*)** | All stages | Production |
| **Manual trigger** | Configurable | Configurable |

### Security Scanning Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Stage                           │
│                                                             │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   SAST   │  │  Dependency  │  │  Container   │           │
│  │ (Static) │  │   Scanning   │  │   Scanning   │           │
│  └────┬─────┘  └──────┬───────┘  └──────┬───────┘           │
│       │               │                  │                  │
│       └───────────────┴──────────────────┘                  │
│                       │                                     │
│                       ▼                                     │
│              ┌────────────────┐                             │
│              │ Security Report│                             │
│              │  (JSON/SARIF)  │                             │
│              └────────┬───────┘                             │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │  Merge Request UI   │
              │  • Security Widget  │
              │  • Vulnerability    │
              │    Summary          │
              │  • Block on Critical│
              └─────────────────────┘
```

---

## 4. GitLab CI Fundamentals Recap

### .gitlab-ci.yml Structure

GitLab CI/CD pipelines are defined in `.gitlab-ci.yml` at the repository root.

```yaml
# Global settings
image: ubuntu:22.04
variables:
  GLOBAL_VAR: "value"

# Define stages (execution order)
stages:
  - build
  - test
  - deploy

# Job definitions
build_job:
  stage: build
  script:
    - echo "Building application"
    - make build
  artifacts:
    paths:
      - build/

test_job:
  stage: test
  script:
    - echo "Running tests"
    - make test
  dependencies:
    - build_job

deploy_job:
  stage: deploy
  script:
    - echo "Deploying application"
  environment:
    name: production
  when: manual
```

### Key Concepts

#### Stages
Stages define the execution order. Jobs in the same stage run in parallel; stages run sequentially.

```yaml
stages:
  - prepare    # Runs first
  - build      # Runs after prepare completes
  - test       # Runs after build completes
  - deploy     # Runs after test completes
```

#### Jobs
Jobs are the basic building blocks. Each job:
- Runs in an isolated environment
- Has a script to execute
- Belongs to a stage
- Can produce artifacts

```yaml
job_name:
  stage: build
  image: node:18
  before_script:
    - npm install
  script:
    - npm run build
  after_script:
    - echo "Job completed"
```

#### Variables

**Predefined CI Variables** (commonly used):

| Variable | Description | Example |
|----------|-------------|---------|
| `CI_COMMIT_SHA` | Full commit SHA | `a1b2c3d4...` |
| `CI_COMMIT_SHORT_SHA` | Short commit SHA | `a1b2c3d4` |
| `CI_COMMIT_REF_NAME` | Branch or tag name | `main`, `v1.0.0` |
| `CI_COMMIT_TAG` | Tag name (if pipeline triggered by tag) | `v1.0.0` |
| `CI_PIPELINE_ID` | Unique pipeline ID | `12345` |
| `CI_PROJECT_PATH` | Project path | `group/project` |
| `CI_PROJECT_NAME` | Project name | `project` |
| `CI_REGISTRY` | GitLab Container Registry URL | `registry.gitlab.com` |
| `CI_REGISTRY_IMAGE` | Full image path | `registry.gitlab.com/group/project` |
| `CI_REGISTRY_USER` | Registry username | `gitlab-ci-token` |
| `CI_REGISTRY_PASSWORD` | Registry password | `<token>` |
| `CI_JOB_TOKEN` | Job-specific token | `<token>` |
| `CI_ENVIRONMENT_NAME` | Environment name | `production` |
| `CI_ENVIRONMENT_SLUG` | URL-safe environment name | `production` |
| `GITLAB_USER_LOGIN` | User who triggered pipeline | `john.doe` |

**Custom Variables**:

```yaml
variables:
  # Global variables
  DOCKER_DRIVER: overlay2
  APP_VERSION: "1.0.0"

job_name:
  variables:
    # Job-specific variables
    DEPLOY_ENV: "staging"
  script:
    - echo "Deploying version $APP_VERSION to $DEPLOY_ENV"
```

#### Artifacts

Artifacts are files produced by jobs and passed to subsequent jobs or made available for download.

```yaml
build_job:
  script:
    - make build
  artifacts:
    paths:
      - build/
      - dist/
    expire_in: 1 week
    reports:
      junit: test-results.xml
```

**Artifact Types**:
- `paths` - Files/directories to preserve
- `reports` - Special reports (junit, coverage, security, etc.)
- `expire_in` - How long to keep artifacts (default: 30 days)

#### Cache

Cache speeds up jobs by preserving dependencies between pipeline runs.

```yaml
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - node_modules/
    - .npm/

build_job:
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
    policy: pull-push  # Default: download and upload
  script:
    - npm install
    - npm run build

test_job:
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
    policy: pull  # Only download, don't upload
  script:
    - npm test
```

**Cache vs Artifacts**:
- **Cache**: For dependencies (node_modules, pip cache) - optimization
- **Artifacts**: For build outputs - required for pipeline functionality

#### Services

Services run additional containers alongside your job (e.g., databases, Redis).

```yaml
test_job:
  image: python:3.11
  services:
    - postgres:15
    - redis:7
  variables:
    POSTGRES_DB: testdb
    POSTGRES_USER: user
    POSTGRES_PASSWORD: password
  script:
    - pytest tests/
```

#### Rules

Rules determine when jobs run (replaces `only`/`except`).

```yaml
deploy_staging:
  script:
    - deploy.sh staging
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: always
    - when: never

deploy_production:
  script:
    - deploy.sh production
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v[0-9]+\.[0-9]+\.[0-9]+$/'
      when: manual
    - when: never
```

**Common Rule Patterns**:

```yaml
# Run on merge requests
rules:
  - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'

# Run on main branch
rules:
  - if: '$CI_COMMIT_BRANCH == "main"'

# Run on tags
rules:
  - if: '$CI_COMMIT_TAG'

# Run on specific file changes
rules:
  - changes:
      - src/**/*
      - Dockerfile
```

#### Needs (DAG - Directed Acyclic Graph)

`needs` allows jobs to start before the entire previous stage completes.

```yaml
stages:
  - build
  - test
  - deploy

build_app:
  stage: build
  script:
    - make build

build_docs:
  stage: build
  script:
    - make docs

test_app:
  stage: test
  needs: [build_app]  # Only waits for build_app, not build_docs
  script:
    - make test

deploy:
  stage: deploy
  needs: [test_app]
  script:
    - make deploy
```

#### Dependencies

`dependencies` controls which artifacts are downloaded.

```yaml
build_job:
  stage: build
  script:
    - make build
  artifacts:
    paths:
      - build/

test_job:
  stage: test
  dependencies:
    - build_job  # Only download artifacts from build_job
  script:
    - test build/
```

#### Parallel

Run multiple instances of a job in parallel.

```yaml
test:
  script:
    - bundle exec rspec
  parallel: 5  # Run 5 instances

# Or with matrix
test:
  script:
    - bundle exec rspec
  parallel:
    matrix:
      - RUBY_VERSION: ['2.7', '3.0', '3.1']
        RAILS_VERSION: ['6.1', '7.0']
```

#### Tags

Tags match jobs to specific runners.

```yaml
deploy_production:
  tags:
    - production
    - docker
  script:
    - deploy.sh
```

---

## 5. Runners: Setup & Recommended Executors

### Runner Types

GitLab Runners execute CI/CD jobs. There are three types:

1. **Shared Runners** - Available to all projects (GitLab.com provides these)
2. **Group Runners** - Available to all projects in a group
3. **Specific Runners** - Dedicated to specific projects

### Executor Comparison

| Executor | Use Case | Pros | Cons |
|----------|----------|------|------|
| **Shell** | Simple scripts, direct access | Fast, simple | No isolation, security risk |
| **Docker** | Containerized builds | Isolated, reproducible | Requires Docker |
| **Docker+Machine** | Auto-scaling | Scales automatically | Complex setup, cloud costs |
| **Kubernetes** | Cloud-native, K8s deployments | Highly scalable, native K8s | Requires K8s cluster |
| **VirtualBox/Parallels** | Full VM isolation | Complete isolation | Slow, resource-heavy |

**Recommended Executors**:
- **Development/Testing**: Docker
- **Production Deployments**: Docker or Kubernetes
- **Auto-scaling**: Docker+Machine or Kubernetes

### Installing GitLab Runner

#### Linux (Ubuntu/Debian)

```bash
# Add GitLab repository
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash

# Install runner
sudo apt-get update
sudo apt-get install gitlab-runner

# Verify installation
gitlab-runner --version
```

#### Using Docker

```bash
# Run runner in Docker container
docker run -d --name gitlab-runner --restart always \
  -v /srv/gitlab-runner/config:/etc/gitlab-runner \
  -v /var/run/docker.sock:/var/run/docker.sock \
  gitlab/gitlab-runner:latest
```

### Registering a Runner

#### Interactive Registration

```bash
sudo gitlab-runner register
```

You'll be prompted for:
1. **GitLab URL**: `https://gitlab.com/` or your instance URL
2. **Registration token**: Found in Settings > CI/CD > Runners
3. **Description**: `my-docker-runner`
4. **Tags**: `docker,linux,production`
5. **Executor**: `docker`
6. **Default Docker image**: `alpine:latest`

#### Non-Interactive Registration

```bash
sudo gitlab-runner register \
  --non-interactive \
  --url "https://gitlab.com/" \
  --registration-token "YOUR_TOKEN" \
  --executor "docker" \
  --docker-image "alpine:latest" \
  --description "docker-runner" \
  --tag-list "docker,linux" \
  --run-untagged="true" \
  --locked="false" \
  --docker-privileged="true" \
  --docker-volumes "/certs/client" \
  --docker-volumes "/cache"
```

### Recommended config.toml Settings

Location: `/etc/gitlab-runner/config.toml`

```toml
concurrent = 4  # Number of jobs to run concurrently

check_interval = 0  # Check for new jobs (0 = default 3s)

[session_server]
  session_timeout = 1800

[[runners]]
  name = "docker-runner"
  url = "https://gitlab.com/"
  token = "YOUR_RUNNER_TOKEN"
  executor = "docker"
  
  # Docker executor settings
  [runners.docker]
    tls_verify = false
    image = "alpine:latest"
    privileged = true  # Required for Docker-in-Docker
    disable_entrypoint_overwrite = false
    oom_kill_disable = false
    disable_cache = false
    volumes = ["/cache", "/certs/client"]
    shm_size = 0
    
    # Resource limits
    cpus = "2"
    memory = "4g"
    memory_swap = "4g"
    memory_reservation = "2g"
  
  # Cache settings
  [runners.cache]
    Type = "s3"
    Shared = true
    [runners.cache.s3]
      ServerAddress = "s3.amazonaws.com"
      AccessKey = "YOUR_ACCESS_KEY"
      SecretKey = "YOUR_SECRET_KEY"
      BucketName = "gitlab-runner-cache"
      BucketLocation = "us-east-1"
    
    # Or use local cache
    # Type = "local"
    # [runners.cache.local]
    #   Path = "/cache"
```

### Docker-in-Docker (DinD) Configuration

For building Docker images inside CI jobs:

```toml
[[runners]]
  [runners.docker]
    privileged = true
    volumes = ["/certs/client", "/cache"]
```

In your `.gitlab-ci.yml`:

```yaml
build_image:
  image: docker:24.0
  services:
    - docker:24.0-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
    DOCKER_DRIVER: overlay2
  before_script:
    - docker info
  script:
    - docker build -t myimage:latest .
```

### Kubernetes Executor Configuration

```toml
[[runners]]
  name = "kubernetes-runner"
  url = "https://gitlab.com/"
  token = "YOUR_RUNNER_TOKEN"
  executor = "kubernetes"
  
  [runners.kubernetes]
    host = ""
    namespace = "gitlab-runner"
    privileged = true
    
    # Resource limits
    cpu_limit = "2"
    memory_limit = "4Gi"
    service_cpu_limit = "1"
    service_memory_limit = "2Gi"
    helper_cpu_limit = "500m"
    helper_memory_limit = "256Mi"
    
    # Resource requests
    cpu_request = "1"
    memory_request = "2Gi"
    service_cpu_request = "500m"
    service_memory_request = "1Gi"
    helper_cpu_request = "100m"
    helper_memory_request = "128Mi"
    
    # Node selector
    [runners.kubernetes.node_selector]
      "node-role.kubernetes.io/runner" = "true"
```

### Security Best Practices

#### 1. Isolate Production Runners

```bash
# Register production runner with specific tags
sudo gitlab-runner register \
  --tag-list "production,deploy" \
  --locked="true" \
  --run-untagged="false"
```

#### 2. Use Protected Runners

In GitLab: Settings > CI/CD > Runners > Edit Runner
- ✅ Protected (only runs on protected branches)
- ✅ Lock to current projects

#### 3. Runner Token Rotation

```bash
# Unregister old runner
sudo gitlab-runner unregister --name old-runner

# Register new runner with new token
sudo gitlab-runner register --name new-runner
```

#### 4. Resource Limits

Always set CPU and memory limits to prevent resource exhaustion:

```toml
[runners.docker]
  cpus = "2"
  memory = "4g"
```

#### 5. Network Isolation

For sensitive runners, use network policies or firewall rules:

```bash
# Example: Restrict runner to only access GitLab and specific registries
sudo ufw allow from <gitlab-ip>
sudo ufw allow to registry.gitlab.com
```

### Runner Monitoring

```bash
# Check runner status
sudo gitlab-runner status

# View runner logs
sudo gitlab-runner --debug run

# List registered runners
sudo gitlab-runner list

# Verify runner configuration
sudo gitlab-runner verify
```

### Troubleshooting Runners

See [Section 18: Common Problems & Solutions](#18-common-problems--solutions) for detailed troubleshooting.

Quick checks:

```bash
# Check if runner is running
sudo gitlab-runner status

# Test runner connectivity
sudo gitlab-runner verify

# Check runner logs
sudo journalctl -u gitlab-runner -f

# Restart runner
sudo gitlab-runner restart
```

---

## 6. Enabling & Customizing Auto DevOps

### What is Auto DevOps?

Auto DevOps is GitLab's **zero-configuration CI/CD** that automatically:
- Builds your application
- Runs tests
- Performs security scans (SAST, Dependency, Container, DAST)
- Builds and pushes Docker images
- Deploys to Kubernetes
- Monitors applications

It uses **opinionated templates** that work out-of-the-box for common application types.

### When to Use Auto DevOps

✅ **Use Auto DevOps when**:
- Starting a new project and want CI/CD quickly
- Your application fits standard patterns (web app, API, static site)
- You're deploying to Kubernetes
- You want GitLab's recommended best practices

❌ **Use Custom Pipelines when**:
- You have complex build requirements
- You need fine-grained control over stages
- You're deploying to non-Kubernetes targets
- You have legacy applications with specific needs

### Enabling Auto DevOps

#### Project Level

1. Go to **Settings > CI/CD > Auto DevOps**
2. Check **Default to Auto DevOps pipeline**
3. (Optional) Set **Deployment strategy**: Continuous, Manual, or Timed incremental
4. Save changes

#### Group Level

1. Go to **Group > Settings > CI/CD > Auto DevOps**
2. Enable for all projects in group
3. Projects can override this setting

#### Via .gitlab-ci.yml

```yaml
# Enable Auto DevOps explicitly
include:
  - template: Auto-DevOps.gitlab-ci.yml
```

### Auto DevOps Variables

Control Auto DevOps behavior with CI/CD variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTO_DEVOPS_ENABLE` | Enable/disable Auto DevOps | `true` |
| `AUTO_DEVOPS_DOMAIN` | Domain for review apps | - |
| `KUBE_NAMESPACE` | Kubernetes namespace | `${CI_PROJECT_PATH_SLUG}` |
| `KUBE_INGRESS_BASE_DOMAIN` | Base domain for K8s ingress | - |
| `POSTGRES_ENABLED` | Enable PostgreSQL | `true` |
| `POSTGRES_VERSION` | PostgreSQL version | `11.7.0` |
| `AUTO_DEVOPS_BUILD_IMAGE_FORWARDED_CI_VARIABLES` | Forward variables to build | - |
| `AUTO_DEVOPS_CHART` | Custom Helm chart | - |
| `AUTO_DEVOPS_CHART_REPOSITORY` | Custom chart repository | - |
| `STAGING_ENABLED` | Enable staging environment | `true` |
| `INCREMENTAL_ROLLOUT_MODE` | Rollout mode | `manual` |
| `TEST_DISABLED` | Disable test job | `false` |
| `CODE_QUALITY_DISABLED` | Disable code quality | `false` |
| `SAST_DISABLED` | Disable SAST | `false` |
| `DEPENDENCY_SCANNING_DISABLED` | Disable dependency scanning | `false` |
| `CONTAINER_SCANNING_DISABLED` | Disable container scanning | `false` |
| `DAST_DISABLED` | Disable DAST | `false` |

### Customizing Auto DevOps

#### Override Specific Jobs

```yaml
# Include Auto DevOps template
include:
  - template: Auto-DevOps.gitlab-ci.yml

# Override the test job
test:
  script:
    - echo "Running custom tests"
    - npm run test:custom
  coverage: '/Coverage: \d+\.\d+%/'
```

#### Extend Auto DevOps Jobs

```yaml
include:
  - template: Auto-DevOps.gitlab-ci.yml

# Extend the build job
build:
  before_script:
    - echo "Custom pre-build steps"
    - npm install --legacy-peer-deps
```

#### Add Custom Stages

```yaml
include:
  - template: Auto-DevOps.gitlab-ci.yml

stages:
  - build
  - test
  - custom_stage  # Add custom stage
  - deploy
  - performance
  - cleanup

custom_job:
  stage: custom_stage
  script:
    - echo "Custom job in custom stage"
```

#### Disable Specific Scanners

```yaml
variables:
  SAST_DISABLED: "true"
  DAST_DISABLED: "true"
  # Keep dependency and container scanning enabled
```

#### Use Custom Helm Chart

```yaml
variables:
  AUTO_DEVOPS_CHART: "gitlab/custom-chart"
  AUTO_DEVOPS_CHART_REPOSITORY: "https://charts.example.com"
```

### Auto DevOps Templates

Auto DevOps includes these templates:

```yaml
# Main Auto DevOps template
include:
  - template: Auto-DevOps.gitlab-ci.yml

# Or include specific templates individually
include:
  - template: Jobs/Build.gitlab-ci.yml
  - template: Jobs/Test.gitlab-ci.yml
  - template: Jobs/Code-Quality.gitlab-ci.yml
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
  - template: Security/Container-Scanning.gitlab-ci.yml
  - template: Security/DAST.gitlab-ci.yml
  - template: Jobs/Deploy.gitlab-ci.yml
```

### Auto DevOps with Custom Dockerfile

Auto DevOps detects and uses your Dockerfile:

```dockerfile
# Dockerfile in repository root
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

Auto DevOps will:
1. Detect the Dockerfile
2. Build the image
3. Push to GitLab Container Registry
4. Deploy using the built image

### Review Apps with Auto DevOps

Auto DevOps automatically creates review apps for merge requests:

```yaml
variables:
  AUTO_DEVOPS_DOMAIN: "example.com"
  KUBE_INGRESS_BASE_DOMAIN: "example.com"
```

Review app URL: `https://<branch-name>-<project-id>.example.com`

### Kubernetes Integration

Auto DevOps requires Kubernetes cluster connection:

#### Using GitLab Kubernetes Agent

1. Install GitLab Agent in your cluster:

```bash
helm repo add gitlab https://charts.gitlab.io
helm repo update
helm upgrade --install gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --create-namespace \
  --set config.token=YOUR_AGENT_TOKEN \
  --set config.kasAddress=wss://kas.gitlab.com
```

2. Configure in GitLab: Infrastructure > Kubernetes clusters > Connect cluster

#### Using kubeconfig (Legacy)

Set CI/CD variables:
- `KUBE_URL`: Kubernetes API URL
- `KUBE_TOKEN`: Service account token
- `KUBE_CA_PEM`: CA certificate

### Auto DevOps Pipeline Stages

```
build → test → code_quality → sast → dependency_scanning → 
container_scanning → dast → review → staging → canary → production → 
performance → cleanup
```

### Migrating from Auto DevOps to Custom Pipeline

```yaml
# Step 1: Include Auto DevOps to see what it does
include:
  - template: Auto-DevOps.gitlab-ci.yml

# Step 2: Override jobs one by one
build:
  script:
    - echo "Custom build"

# Step 3: Eventually remove Auto DevOps include and define everything custom
```

---

## 7. Container Registry Usage & Policies

### GitLab Container Registry

GitLab includes a built-in **Docker Container Registry** for every project. It's tightly integrated with CI/CD.

**Registry URL**: `registry.gitlab.com/<namespace>/<project>`

### Accessing the Registry

#### Authentication in CI Jobs

GitLab provides automatic authentication via predefined variables:

```yaml
docker_build:
  image: docker:24.0
  services:
    - docker:24.0-dind
  before_script:
    - echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"
  script:
    - docker build -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
```

**Predefined Registry Variables**:
- `CI_REGISTRY`: `registry.gitlab.com`
- `CI_REGISTRY_IMAGE`: `registry.gitlab.com/group/project`
- `CI_REGISTRY_USER`: `gitlab-ci-token`
- `CI_REGISTRY_PASSWORD`: Temporary token for the job

#### Authentication from Local Machine

```bash
# Using personal access token
docker login registry.gitlab.com -u <username> -p <personal_access_token>

# Using deploy token
docker login registry.gitlab.com -u <deploy_token_username> -p <deploy_token>
```

### Tagging Strategy

A good tagging strategy enables traceability and rollback:

```yaml
variables:
  IMAGE_TAG_COMMIT: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  IMAGE_TAG_BRANCH: "$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG"
  IMAGE_TAG_LATEST: "$CI_REGISTRY_IMAGE:latest"
  IMAGE_TAG_SEMVER: "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG"

docker_build:
  script:
    - docker build -t "$IMAGE_TAG_COMMIT" .
    
    # Tag with branch name
    - docker tag "$IMAGE_TAG_COMMIT" "$IMAGE_TAG_BRANCH"
    
    # Tag as latest on main branch
    - |
      if [ "$CI_COMMIT_BRANCH" == "main" ]; then
        docker tag "$IMAGE_TAG_COMMIT" "$IMAGE_TAG_LATEST"
      fi
    
    # Tag with semver on release tags
    - |
      if [ -n "$CI_COMMIT_TAG" ]; then
        docker tag "$IMAGE_TAG_COMMIT" "$IMAGE_TAG_SEMVER"
      fi
    
    # Push all tags
    - docker push "$CI_REGISTRY_IMAGE" --all-tags
```

**Recommended Tags**:
- `<commit-sha>` - Immutable, traceable (e.g., `a1b2c3d4`)
- `<branch-name>` - Latest for branch (e.g., `main`, `develop`)
- `latest` - Latest production image
- `<semver>` - Release versions (e.g., `v1.2.3`, `1.2.3`)
- `<environment>` - Environment-specific (e.g., `staging`, `production`)

### Image Promotion Strategy

Promote images through environments without rebuilding:

```
Dev Registry          Staging Registry       Production Registry
    ↓                      ↓                        ↓
image:commit-sha  →  image:staging-sha  →  image:v1.2.3
```

**Implementation**:

```yaml
stages:
  - build
  - promote-staging
  - promote-production

build:
  stage: build
  script:
    - docker build -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"

promote_staging:
  stage: promote-staging
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
  script:
    - docker pull "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
    - docker tag "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" "$CI_REGISTRY_IMAGE:staging"
    - docker push "$CI_REGISTRY_IMAGE:staging"

promote_production:
  stage: promote-production
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v[0-9]+\.[0-9]+\.[0-9]+$/'
  script:
    - docker pull "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
    - docker tag "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG"
    - docker tag "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" "$CI_REGISTRY_IMAGE:latest"
    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG"
    - docker push "$CI_REGISTRY_IMAGE:latest"
```

### Registry Cleanup Policies

Prevent registry bloat with cleanup policies:

#### Configure Cleanup Policy

1. Go to **Settings > Packages & Registries > Container Registry**
2. Configure cleanup policy:

| Setting | Recommended Value | Description |
|---------|------------------|-------------|
| **Expiration interval** | 90 days | Delete tags older than this |
| **Expiration schedule** | Every day at 1:00 AM | When to run cleanup |
| **Number of tags to retain** | 10 | Keep at least this many tags |
| **Tags matching** | `.*` | Regex for tags to clean |
| **Tags exceptions** | `latest, v.*, staging, production` | Tags to never delete |

#### Via API

```bash
curl --request PUT --header "PRIVATE-TOKEN: <token>" \
  "https://gitlab.com/api/v4/projects/:id/registry/repositories/:repository_id" \
  --data "expiration_policy_enabled=true" \
  --data "expiration_policy_older_than=90d" \
  --data "expiration_policy_keep_n=10" \
  --data "expiration_policy_name_regex=.*" \
  --data "expiration_policy_name_regex_keep=latest|v.*|staging|production"
```

### Manual Registry Cleanup

```bash
# List all tags
curl --header "PRIVATE-TOKEN: <token>" \
  "https://gitlab.com/api/v4/projects/:id/registry/repositories/:repository_id/tags"

# Delete specific tag
curl --request DELETE --header "PRIVATE-TOKEN: <token>" \
  "https://gitlab.com/api/v4/projects/:id/registry/repositories/:repository_id/tags/:tag_name"

# Bulk delete using script
for tag in $(curl --header "PRIVATE-TOKEN: <token>" \
  "https://gitlab.com/api/v4/projects/:id/registry/repositories/:repository_id/tags" \
  | jq -r '.[].name' | grep -v -E 'latest|v.*|staging|production'); do
  echo "Deleting $tag"
  curl --request DELETE --header "PRIVATE-TOKEN: <token>" \
    "https://gitlab.com/api/v4/projects/:id/registry/repositories/:repository_id/tags/$tag"
done
```

### Registry Garbage Collection

For self-hosted GitLab, run garbage collection to reclaim disk space:

```bash
# Stop registry
sudo gitlab-ctl stop registry

# Run garbage collection
sudo gitlab-ctl registry-garbage-collect

# Or with dry-run
sudo gitlab-ctl registry-garbage-collect -m

# Start registry
sudo gitlab-ctl start registry
```

### Multi-Architecture Images

Build images for multiple architectures:

```yaml
build_multiarch:
  image: docker:24.0
  services:
    - docker:24.0-dind
  before_script:
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" "$CI_REGISTRY"
    - docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
    - docker buildx create --use
  script:
    - |
      docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --tag "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" \
        --push \
        .
```

### Registry Storage Limits

**GitLab.com limits** (as of 2024):
- Free tier: 5 GB per project
- Premium: 10 GB per project
- Ultimate: 10 GB per project

**Self-hosted**: Configure in `/etc/gitlab/gitlab.rb`:

```ruby
registry['storage'] = {
  's3' => {
    'accesskey' => 'YOUR_ACCESS_KEY',
    'secretkey' => 'YOUR_SECRET_KEY',
    'bucket' => 'gitlab-registry',
    'region' => 'us-east-1'
  }
}
```

### Best Practices

1. **Use immutable tags** - Tag with commit SHA for traceability
2. **Implement cleanup policies** - Prevent registry bloat
3. **Use multi-stage builds** - Reduce image size
4. **Scan images** - Enable Container Scanning (see Section 8)
5. **Use .dockerignore** - Exclude unnecessary files
6. **Minimize layers** - Combine RUN commands
7. **Use specific base images** - Avoid `latest` tag in Dockerfile
8. **Sign images** - Use Docker Content Trust for production

---

## 8. Security Scanning Integration

GitLab provides integrated security scanning that runs automatically in your CI/CD pipeline and reports vulnerabilities in the Merge Request UI.

### Security Scanners Overview

| Scanner | Type | Analyzes | Language Support |
|---------|------|----------|------------------|
| **SAST** | Static | Source code | 30+ languages |
| **Dependency Scanning** | Static | Dependencies | Package managers |
| **Container Scanning** | Static | Docker images | All images |
| **DAST** | Dynamic | Running application | Any web app |
| **Secret Detection** | Static | Secrets in code | All files |
| **License Compliance** | Static | Dependency licenses | Package managers |
| **Coverage-Guided Fuzz Testing** | Dynamic | Application inputs | C/C++, Go, Rust, etc. |

### SAST (Static Application Security Testing)

SAST analyzes source code for security vulnerabilities without executing it.

#### Enable SAST

```yaml
include:
  - template: Security/SAST.gitlab-ci.yml
```

That's it! GitLab automatically:
- Detects your programming language
- Runs appropriate analyzers
- Generates security report
- Shows findings in MR

#### Supported Languages

- JavaScript/TypeScript (ESLint, Semgrep)
- Python (Bandit, Semgrep)
- Java (SpotBugs, Semgrep)
- Go (Gosec, Semgrep)
- Ruby (Brakeman)
- PHP (phpcs-security-audit)
- C/C++ (Flawfinder)
- C# (.NET Security Guard)
- And 20+ more...

#### Customize SAST

```yaml
include:
  - template: Security/SAST.gitlab-ci.yml

variables:
  # Exclude paths from scanning
  SAST_EXCLUDED_PATHS: "spec, test, tests, tmp, node_modules"
  
  # Exclude specific analyzers
  SAST_EXCLUDED_ANALYZERS: "eslint, semgrep"
  
  # Set severity threshold (fail pipeline on critical/high)
  SAST_SEVERITY_THRESHOLD: "high"
  
  # Disable specific rules
  SAST_DISABLE_RULES: "rule1,rule2"
```

#### Advanced SAST Configuration

```yaml
include:
  - template: Security/SAST.gitlab-ci.yml

# Override SAST job
sast:
  variables:
    SEARCH_MAX_DEPTH: 20  # How deep to search for files
  before_script:
    - echo "Running custom pre-SAST steps"
```

### Dependency Scanning

Scans your dependencies (npm, pip, maven, etc.) for known vulnerabilities.

#### Enable Dependency Scanning

```yaml
include:
  - template: Security/Dependency-Scanning.gitlab-ci.yml
```

Automatically detects:
- `package.json` / `package-lock.json` (npm)
- `Gemfile.lock` (Ruby)
- `requirements.txt` / `Pipfile.lock` (Python)
- `pom.xml` / `build.gradle` (Java)
- `go.mod` (Go)
- `composer.lock` (PHP)
- And more...

#### Customize Dependency Scanning

```yaml
include:
  - template: Security/Dependency-Scanning.gitlab-ci.yml

variables:
  # Scan specific paths
  DS_DEFAULT_ANALYZERS: "gemnasium, retire-js"
  
  # Exclude paths
  DS_EXCLUDED_PATHS: "spec, test, tests, tmp"
  
  # Set severity threshold
  DS_SEVERITY_THRESHOLD: "high"
  
  # Use custom advisory database
  GEMNASIUM_DB_REMOTE_URL: "https://custom-db.example.com"
```

#### Private Dependencies

For private package registries:

```yaml
dependency_scanning:
  variables:
    PIP_INDEX_URL: "https://${PYPI_USERNAME}:${PYPI_PASSWORD}@pypi.example.com/simple"
    NPM_CONFIG_REGISTRY: "https://npm.example.com"
  before_script:
    - echo "//npm.example.com/:_authToken=${NPM_TOKEN}" > .npmrc
```

### Container Scanning

Scans Docker images for vulnerabilities in OS packages and application dependencies.

#### Enable Container Scanning

```yaml
include:
  - template: Security/Container-Scanning.gitlab-ci.yml

variables:
  CS_IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
```

Uses **Trivy** scanner by default (GitLab 14.0+).

#### Customize Container Scanning

```yaml
include:
  - template: Security/Container-Scanning.gitlab-ci.yml

variables:
  CS_IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  
  # Set severity threshold
  CS_SEVERITY_THRESHOLD: "high"
  
  # Scan specific image
  CS_DOCKERFILE_PATH: "Dockerfile.production"
  
  # Use specific scanner version
  CS_ANALYZER_IMAGE: "registry.gitlab.com/security-products/container-scanning:5"
```

#### Scan Multiple Images

```yaml
container_scanning_app:
  extends: container_scanning
  variables:
    CS_IMAGE: "$CI_REGISTRY_IMAGE/app:$CI_COMMIT_SHORT_SHA"

container_scanning_worker:
  extends: container_scanning
  variables:
    CS_IMAGE: "$CI_REGISTRY_IMAGE/worker:$CI_COMMIT_SHORT_SHA"
```

### DAST (Dynamic Application Security Testing)

DAST scans a **running application** for vulnerabilities by simulating attacks.

#### Enable DAST

```yaml
include:
  - template: Security/DAST.gitlab-ci.yml

variables:
  DAST_WEBSITE: "https://staging.example.com"
```

#### DAST with Authentication

```yaml
include:
  - template: Security/DAST.gitlab-ci.yml

variables:
  DAST_WEBSITE: "https://staging.example.com"
  DAST_AUTH_URL: "https://staging.example.com/login"
  DAST_USERNAME: "testuser"
  DAST_PASSWORD: "$DAST_PASSWORD"  # Set in CI/CD variables (masked)
  DAST_USERNAME_FIELD: "username"
  DAST_PASSWORD_FIELD: "password"
  DAST_AUTH_EXCLUDE_URLS: "https://staging.example.com/logout"
```

#### DAST API Scanning

For API endpoints:

```yaml
include:
  - template: Security/DAST-API.gitlab-ci.yml

variables:
  DAST_API_TARGET_URL: "https://api.example.com"
  DAST_API_OPENAPI: "openapi.json"  # Or swagger.yaml
```

#### Full-Featured DAST

```yaml
include:
  - template: Security/DAST.gitlab-ci.yml

variables:
  DAST_WEBSITE: "https://review-${CI_COMMIT_REF_SLUG}.example.com"
  DAST_FULL_SCAN_ENABLED: "true"  # Full scan (slower but thorough)
  DAST_SPIDER_MINS: "5"  # Spider timeout
  DAST_TARGET_AVAILABILITY_TIMEOUT: "300"  # Wait for app to be ready
  DAST_EXCLUDE_URLS: "https://example.com/admin,https://example.com/logout"
  DAST_PATHS: "/api,/products,/checkout"  # Specific paths to scan
```

### Secret Detection

Detects secrets (API keys, passwords, tokens) committed to the repository.

```yaml
include:
  - template: Security/Secret-Detection.gitlab-ci.yml
```

Detects:
- AWS keys
- GCP keys
- Azure keys
- Private keys (RSA, SSH)
- API tokens
- Database credentials
- And 100+ more patterns

### License Compliance

Scans dependencies for license compatibility issues.

```yaml
include:
  - template: Security/License-Scanning.gitlab-ci.yml

variables:
  LICENSE_FINDER_CLI_OPTS: "--decisions-file=.license-decisions.yml"
```

### Security Reports in Merge Requests

Security findings automatically appear in MR:

```
┌────────────────────────────────────────────────────┐
│  Security Scanning                                  │
│  ⚠️  3 new vulnerabilities detected                │
│                                                     │
│  Critical: 1  High: 2  Medium: 0  Low: 0           │
│                                                     │
│  📋 View full report                               │
└────────────────────────────────────────────────────┘
```

### Failing Pipelines on Vulnerabilities

```yaml
include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml

# Add a job to fail on critical vulnerabilities
security_check:
  stage: security
  script:
    - |
      if grep -q '"severity":"Critical"' gl-sast-report.json gl-dependency-scanning-report.json; then
        echo "Critical vulnerabilities found!"
        exit 1
      fi
  artifacts:
    reports:
      sast: gl-sast-report.json
      dependency_scanning: gl-dependency-scanning-report.json
  allow_failure: false
```

### Security Dashboard (EE)

GitLab EE provides a centralized Security Dashboard:

- **Project Security Dashboard**: Settings > Security & Compliance > Vulnerability Report
- **Group Security Dashboard**: Group > Security > Vulnerability Report
- **Instance Security Dashboard**: Admin Area > Security

Features:
- View all vulnerabilities across projects
- Filter by severity, status, scanner
- Create issues from vulnerabilities
- Track remediation progress

### Vulnerability Management Workflow

1. **Detection** - Scanner finds vulnerability in MR
2. **Review** - Security team reviews finding
3. **Triage** - Mark as:
   - Confirmed
   - False positive
   - Dismissed
   - Resolved
4. **Remediation** - Create issue, assign to developer
5. **Verification** - Re-scan after fix
6. **Close** - Mark as resolved

### Custom Security Scanners

Integrate custom scanners:

```yaml
custom_security_scan:
  stage: security
  script:
    - ./custom-scanner.sh > gl-custom-security-report.json
  artifacts:
    reports:
      sast: gl-custom-security-report.json  # Must match GitLab schema
```

Report must follow [GitLab Security Report Schema](https://gitlab.com/gitlab-org/security-products/security-report-schemas).

### Best Practices

1. **Enable all scanners** - SAST, Dependency, Container, DAST
2. **Run SAST early** - In build/test stages
3. **Run DAST on review apps** - Test real deployments
4. **Set severity thresholds** - Fail on critical/high
5. **Triage regularly** - Don't let vulnerabilities pile up
6. **Update scanners** - Use latest analyzer versions
7. **Exclude false positives** - Document and exclude
8. **Integrate with issues** - Create issues for tracking

---

*[Continuing in next part due to length...]*

## 9. Full Sample .gitlab-ci.yml

Below is a complete, production-ready `.gitlab-ci.yml` with all stages and best practices:

```yaml
# GitLab CI/CD Pipeline - Production Ready
# Stages: prepare → build → test → security → image-build → push → deploy

image: alpine:latest

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"
  IMAGE_TAG: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  KUBE_NAMESPACE: "$CI_PROJECT_NAME-$CI_ENVIRONMENT_SLUG"

stages:
  - prepare
  - build
  - test
  - security
  - image-build
  - push
  - deploy-review
  - deploy-staging
  - deploy-prod
  - cleanup

# ============================================================================
# PREPARE STAGE
# ============================================================================

cache-dependencies:
  stage: prepare
  image: node:18-alpine
  script:
    - npm ci --cache .npm --prefer-offline
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
      - .npm/
  artifacts:
    paths:
      - node_modules/
    expire_in: 1 hour

# ============================================================================
# BUILD STAGE
# ============================================================================

build:
  stage: build
  image: node:18-alpine
  needs: [cache-dependencies]
  script:
    - npm run build
  artifacts:
    paths:
      - dist/
      - build/
    expire_in: 1 day
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
    policy: pull

# ============================================================================
# TEST STAGE
# ============================================================================

unit-test:
  stage: test
  image: node:18-alpine
  needs: [build]
  script:
    - npm run test:unit
  coverage: '/Lines\s*:\s*(\d+\.\d+)%/'
  artifacts:
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

integration-test:
  stage: test
  image: node:18-alpine
  services:
    - postgres:15
    - redis:7
  variables:
    POSTGRES_DB: testdb
    POSTGRES_USER: testuser
    POSTGRES_PASSWORD: testpass
  needs: [build]
  script:
    - npm run test:integration

# ============================================================================
# SECURITY STAGE
# ============================================================================

include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml

# ============================================================================
# IMAGE BUILD STAGE
# ============================================================================

docker-build:
  stage: image-build
  image: docker:24.0
  services:
    - docker:24.0-dind
  needs: [build, unit-test]
  before_script:
    - echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"
  script:
    - docker build -t "$IMAGE_TAG" .
    - docker tag "$IMAGE_TAG" "$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG"
    - docker push "$IMAGE_TAG"
    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG"
  rules:
    - if: '$CI_COMMIT_BRANCH'
    - if: '$CI_COMMIT_TAG'

# Container scanning
include:
  - template: Security/Container-Scanning.gitlab-ci.yml

container_scanning:
  needs: [docker-build]
  variables:
    CS_IMAGE: "$IMAGE_TAG"

# ============================================================================
# DEPLOY REVIEW APPS
# ============================================================================

deploy-review:
  stage: deploy-review
  image: bitnami/kubectl:latest
  needs: [docker-build]
  script:
    - kubectl config use-context "$KUBE_CONTEXT"
    - |
      cat <<YAML | kubectl apply -f -
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: $CI_PROJECT_NAME
        namespace: review-$CI_COMMIT_REF_SLUG
      spec:
        replicas: 1
        selector:
          matchLabels:
            app: $CI_PROJECT_NAME
        template:
          metadata:
            labels:
              app: $CI_PROJECT_NAME
          spec:
            containers:
            - name: app
              image: $IMAGE_TAG
              ports:
              - containerPort: 3000
      YAML
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://review-$CI_COMMIT_REF_SLUG.example.com
    on_stop: stop-review
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'

stop-review:
  stage: cleanup
  image: bitnami/kubectl:latest
  script:
    - kubectl delete namespace review-$CI_COMMIT_REF_SLUG --ignore-not-found=true
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  when: manual
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'

# ============================================================================
# DEPLOY STAGING
# ============================================================================

deploy-staging:
  stage: deploy-staging
  image: bitnami/kubectl:latest
  needs: [docker-build, container_scanning]
  script:
    - kubectl config use-context "$KUBE_CONTEXT"
    - kubectl set image deployment/$CI_PROJECT_NAME app=$IMAGE_TAG -n staging
    - kubectl rollout status deployment/$CI_PROJECT_NAME -n staging
  environment:
    name: staging
    url: https://staging.example.com
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

# ============================================================================
# DEPLOY PRODUCTION
# ============================================================================

deploy-production:
  stage: deploy-prod
  image: bitnami/kubectl:latest
  needs: [docker-build, container_scanning]
  before_script:
    - docker pull "$IMAGE_TAG"
    - docker tag "$IMAGE_TAG" "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG"
    - docker tag "$IMAGE_TAG" "$CI_REGISTRY_IMAGE:latest"
    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG"
    - docker push "$CI_REGISTRY_IMAGE:latest"
  script:
    - kubectl config use-context "$KUBE_CONTEXT"
    - kubectl set image deployment/$CI_PROJECT_NAME app=$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG -n production
    - kubectl rollout status deployment/$CI_PROJECT_NAME -n production
  environment:
    name: production
    url: https://example.com
  when: manual
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v[0-9]+\.[0-9]+\.[0-9]+$/'
```

See `.gitlab-ci.yml` in this repository for the complete working example.

---

## 10. Docker Build & Push Job Examples

### Docker-in-Docker (DinD) Approach

```yaml
docker-build-dind:
  stage: build
  image: docker:24.0
  services:
    - docker:24.0-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
    DOCKER_DRIVER: overlay2
  before_script:
    - echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"
  script:
    # Build image
    - docker build 
        --build-arg VERSION=$CI_COMMIT_TAG 
        --cache-from $CI_REGISTRY_IMAGE:latest 
        -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA 
        -t $CI_REGISTRY_IMAGE:latest 
        .
    
    # Push all tags
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
    - docker push $CI_REGISTRY_IMAGE:latest
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### Kaniko Approach (No Docker Daemon Required)

Kaniko builds container images without requiring privileged mode:

```yaml
docker-build-kaniko:
  stage: build
  image:
    name: gcr.io/kaniko-project/executor:v1.9.0-debug
    entrypoint: [""]
  script:
    - mkdir -p /kaniko/.docker
    - echo "{\"auths\":{\"${CI_REGISTRY}\":{\"auth\":\"$(printf "%s:%s" "${CI_REGISTRY_USER}" "${CI_REGISTRY_PASSWORD}" | base64 | tr -d '\n')\"}}}" > /kaniko/.docker/config.json
    - /kaniko/executor
        --context "${CI_PROJECT_DIR}"
        --dockerfile "${CI_PROJECT_DIR}/Dockerfile"
        --destination "${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}"
        --destination "${CI_REGISTRY_IMAGE}:latest"
        --cache=true
        --cache-ttl=24h
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### Multi-Stage Build with Layer Caching

```yaml
docker-build-cached:
  stage: build
  image: docker:24.0
  services:
    - docker:24.0-dind
  before_script:
    - echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"
    # Pull previous image for layer caching
    - docker pull $CI_REGISTRY_IMAGE:latest || true
  script:
    - docker build 
        --cache-from $CI_REGISTRY_IMAGE:latest 
        --build-arg BUILDKIT_INLINE_CACHE=1 
        -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA 
        .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
```

### Best Practices for Docker Builds

1. **Use multi-stage builds** to reduce image size
2. **Leverage build cache** with `--cache-from`
3. **Use .dockerignore** to exclude unnecessary files
4. **Pin base image versions** (avoid `latest`)
5. **Run as non-root user**
6. **Scan images** before pushing to production

---

## 11. Kubernetes Deployment Example

### Using kubectl

```yaml
deploy-k8s-kubectl:
  stage: deploy
  image: bitnami/kubectl:latest
  before_script:
    # Configure kubectl
    - kubectl config set-cluster k8s --server="$KUBE_URL" --insecure-skip-tls-verify=true
    - kubectl config set-credentials gitlab --token="$KUBE_TOKEN"
    - kubectl config set-context default --cluster=k8s --user=gitlab --namespace="$KUBE_NAMESPACE"
    - kubectl config use-context default
  script:
    # Create namespace if not exists
    - kubectl create namespace $KUBE_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply manifests
    - kubectl apply -f k8s/deployment.yaml
    - kubectl apply -f k8s/service.yaml
    - kubectl apply -f k8s/ingress.yaml
    
    # Update image
    - kubectl set image deployment/$CI_PROJECT_NAME app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA -n $KUBE_NAMESPACE
    
    # Wait for rollout
    - kubectl rollout status deployment/$CI_PROJECT_NAME -n $KUBE_NAMESPACE --timeout=5m
  environment:
    name: production
    url: https://example.com
    kubernetes:
      namespace: $KUBE_NAMESPACE
```

### Using Helm

```yaml
deploy-k8s-helm:
  stage: deploy
  image: alpine/helm:latest
  before_script:
    - helm repo add stable https://charts.helm.sh/stable
    - helm repo update
  script:
    - helm upgrade --install $CI_PROJECT_NAME ./helm 
        --namespace $KUBE_NAMESPACE 
        --create-namespace 
        --set image.repository=$CI_REGISTRY_IMAGE 
        --set image.tag=$CI_COMMIT_SHORT_SHA 
        --set ingress.host=example.com 
        --wait 
        --timeout 5m
  environment:
    name: production
    url: https://example.com
```

### Review Apps with Dynamic Namespaces

```yaml
deploy-review-app:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - export NAMESPACE="review-$CI_COMMIT_REF_SLUG"
    - kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    - |
      cat <<EOF | kubectl apply -f -
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: $CI_PROJECT_NAME
        namespace: $NAMESPACE
      spec:
        replicas: 1
        selector:
          matchLabels:
            app: $CI_PROJECT_NAME
        template:
          metadata:
            labels:
              app: $CI_PROJECT_NAME
          spec:
            containers:
            - name: app
              image: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
              ports:
              - containerPort: 3000
              env:
              - name: ENVIRONMENT
                value: review
      ---
      apiVersion: v1
      kind: Service
      metadata:
        name: $CI_PROJECT_NAME
        namespace: $NAMESPACE
      spec:
        selector:
          app: $CI_PROJECT_NAME
        ports:
        - port: 80
          targetPort: 3000
      ---
      apiVersion: networking.k8s.io/v1
      kind: Ingress
      metadata:
        name: $CI_PROJECT_NAME
        namespace: $NAMESPACE
      spec:
        rules:
        - host: $CI_COMMIT_REF_SLUG.review.example.com
          http:
            paths:
            - path: /
              pathType: Prefix
              backend:
                service:
                  name: $CI_PROJECT_NAME
                  port:
                    number: 80
      EOF
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_COMMIT_REF_SLUG.review.example.com
    on_stop: stop-review-app
    auto_stop_in: 1 week
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'

stop-review-app:
  stage: cleanup
  image: bitnami/kubectl:latest
  script:
    - kubectl delete namespace review-$CI_COMMIT_REF_SLUG --ignore-not-found=true
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  when: manual
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```

---

## 12. Secrets & Credentials Management

### GitLab CI/CD Variables

Store sensitive data in **Settings > CI/CD > Variables**:

```
Variable: DATABASE_PASSWORD
Value: super_secret_password
Type: Variable
Protected: ✅ (only available on protected branches)
Masked: ✅ (hidden in job logs)
```

**Variable Types**:
- **Variable** - Available as environment variable
- **File** - Written to temporary file, path in `$VARIABLE_NAME`

### Protected & Masked Variables

```yaml
deploy_production:
  script:
    - deploy.sh --db-password "$DATABASE_PASSWORD"
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'  # Protected variable available
```

**Best Practices**:
- ✅ Mark production credentials as **Protected**
- ✅ Mark all secrets as **Masked**
- ✅ Use **File** type for certificates/keys
- ❌ Never hardcode secrets in `.gitlab-ci.yml`

### HashiCorp Vault Integration

```yaml
secrets:
  DATABASE_PASSWORD:
    vault: production/db/password@secret
    file: false

deploy:
  secrets:
    DATABASE_PASSWORD:
      vault: production/db/password@secret
  script:
    - echo "Password: $DATABASE_PASSWORD"
```

### Kubernetes Secrets

```yaml
deploy:
  script:
    - kubectl create secret generic app-secrets 
        --from-literal=db-password="$DATABASE_PASSWORD" 
        --namespace=$KUBE_NAMESPACE 
        --dry-run=client -o yaml | kubectl apply -f -
```

### SSH Keys for Deployment

```yaml
deploy_vm:
  before_script:
    - 'which ssh-agent || ( apt-get update -y && apt-get install openssh-client -y )'
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - chmod 700 ~/.ssh
    - ssh-keyscan $DEPLOY_SERVER >> ~/.ssh/known_hosts
  script:
    - scp -r dist/ user@$DEPLOY_SERVER:/var/www/app/
    - ssh user@$DEPLOY_SERVER 'systemctl restart app'
```

### Docker Registry Credentials

```yaml
deploy:
  before_script:
    - echo "$DOCKER_HUB_PASSWORD" | docker login -u "$DOCKER_HUB_USERNAME" --password-stdin
  script:
    - docker pull myapp:latest
```

### Secret Rotation

1. Create new secret in GitLab CI/CD variables
2. Update application to use new secret
3. Deploy and verify
4. Remove old secret

---

## 13. Pipeline Optimization & Scaling

### Caching Strategies

```yaml
# Global cache
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - node_modules/
    - .npm/

# Job-specific cache
build:
  cache:
    key: build-cache
    paths:
      - node_modules/
    policy: pull-push  # Download and upload

test:
  cache:
    key: build-cache
    paths:
      - node_modules/
    policy: pull  # Only download
```

### Using `needs` for DAG Pipelines

```yaml
stages:
  - build
  - test
  - deploy

build:app:
  stage: build
  script: make build-app

build:docs:
  stage: build
  script: make build-docs

test:unit:
  stage: test
  needs: [build:app]  # Start immediately after build:app
  script: make test

deploy:
  stage: deploy
  needs: [test:unit]  # Don't wait for build:docs
  script: make deploy
```

### Parallel Jobs

```yaml
test:
  script: rspec
  parallel: 5  # Run 5 instances

# Matrix builds
test:
  parallel:
    matrix:
      - RUBY_VERSION: ['2.7', '3.0', '3.1']
        RAILS_VERSION: ['6.1', '7.0']
  script:
    - bundle install
    - bundle exec rspec
```

### Artifact Management

```yaml
build:
  artifacts:
    paths:
      - dist/
    expire_in: 1 week  # Auto-delete after 1 week
    
test:
  dependencies: [build]  # Only download build artifacts
  artifacts:
    when: on_failure  # Only save on failure
    paths:
      - logs/
```

### Resource Groups (Prevent Concurrent Deploys)

```yaml
deploy_production:
  resource_group: production
  script:
    - deploy.sh
```

Only one job in the `production` resource group runs at a time.

### Auto-Scaling Runners

**Docker+Machine** for cloud auto-scaling:

```toml
[[runners]]
  [runners.machine]
    IdleCount = 2
    IdleTime = 600
    MaxBuilds = 100
    MachineDriver = "amazonec2"
    MachineName = "gitlab-runner-%s"
    [runners.machine.amazonec2]
      region = "us-east-1"
      instance-type = "t3.medium"
```

---

## 14. Observability: Logs, Monitoring & Alerts

### Accessing Pipeline Logs

- **Job logs**: Click on job in pipeline view
- **Download logs**: Job page > Download button
- **API access**:

```bash
curl --header "PRIVATE-TOKEN: <token>" \
  "https://gitlab.com/api/v4/projects/:id/jobs/:job_id/trace"
```

### Prometheus Integration

GitLab can scrape Prometheus metrics from deployed apps:

```yaml
# In your app, expose metrics endpoint
GET /metrics
```

Configure in GitLab: **Operations > Metrics**

### Application Performance Monitoring

```yaml
deploy:
  script:
    - deploy.sh
  environment:
    name: production
    url: https://example.com
    metrics:
      - name: throughput
        query: 'rate(http_requests_total[5m])'
      - name: latency
        query: 'histogram_quantile(0.95, http_request_duration_seconds_bucket)'
```

### Pipeline Failure Alerts

**Email Notifications**: Settings > Integrations > Emails on push

**Slack Integration**:

```yaml
notify_failure:
  stage: .post
  script:
    - |
      curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"Pipeline failed: $CI_PIPELINE_URL\"}" \
        $SLACK_WEBHOOK_URL
  when: on_failure
```

### Custom Metrics

```yaml
deploy:
  after_script:
    - |
      curl -X POST https://metrics.example.com/api/v1/metrics \
        -d "pipeline_duration=$CI_PIPELINE_DURATION" \
        -d "pipeline_id=$CI_PIPELINE_ID"
```

---

## 15. Governance, Permissions & Approvals

### Protected Branches

**Settings > Repository > Protected branches**

- `main`: Maintainers can push, Developers cannot
- Require merge requests
- Require approvals before merge

### Merge Request Approvals

**Settings > Merge Requests > Approval rules**

```
Rule: Security Review
Approvals required: 2
Eligible approvers: @security-team
```

### Protected Environments

**Settings > CI/CD > Protected Environments**

```
Environment: production
Allowed to deploy: Maintainers only
Approval required: Yes
```

### Protected Variables

Variables marked as **Protected** are only available to:
- Protected branches
- Protected tags

```yaml
deploy_production:
  script:
    - deploy.sh --api-key "$PRODUCTION_API_KEY"  # Only available on protected branches
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### Deployment Approvals

```yaml
deploy_production:
  stage: deploy
  script:
    - deploy.sh
  environment:
    name: production
  when: manual  # Requires manual approval
  rules:
    - if: '$CI_COMMIT_TAG'
```

### Audit Events (EE)

**Admin Area > Monitoring > Audit Events**

Tracks:
- Variable changes
- Runner registration
- Pipeline execution
- Deployment approvals

---

## 16. CI/CD for Monorepos & Multi-Project Pipelines

### Monorepo with Path Rules

```yaml
build:frontend:
  script: cd frontend && npm run build
  rules:
    - changes:
        - frontend/**/*

build:backend:
  script: cd backend && mvn package
  rules:
    - changes:
        - backend/**/*

build:shared:
  script: cd shared && npm run build
  rules:
    - changes:
        - shared/**/*
        - frontend/**/*
        - backend/**/*
```

### Parent-Child Pipelines

```yaml
# .gitlab-ci.yml (parent)
trigger:frontend:
  trigger:
    include: frontend/.gitlab-ci.yml
    strategy: depend
  rules:
    - changes:
        - frontend/**/*

trigger:backend:
  trigger:
    include: backend/.gitlab-ci.yml
    strategy: depend
  rules:
    - changes:
        - backend/**/*
```

```yaml
# frontend/.gitlab-ci.yml (child)
stages:
  - build
  - test

build:
  script: npm run build

test:
  script: npm test
```

### Multi-Project Pipelines

Trigger pipelines in other projects:

```yaml
trigger_downstream:
  stage: deploy
  trigger:
    project: group/downstream-project
    branch: main
    strategy: depend
  variables:
    UPSTREAM_COMMIT: $CI_COMMIT_SHA
```

---

## 17. Testing the Pipeline & Local Debugging

### Local Pipeline Testing

```bash
# Install gitlab-runner locally
brew install gitlab-runner  # macOS
# or
sudo apt-get install gitlab-runner  # Linux

# Execute job locally (limited functionality)
gitlab-runner exec docker build --docker-image=node:18
```

### Validating .gitlab-ci.yml

**CI Lint Tool**: Project > CI/CD > Pipelines > CI Lint

Or via API:

```bash
curl --header "Content-Type: application/json" \
  --data '{"content": "'"$(cat .gitlab-ci.yml)"'"}' \
  "https://gitlab.com/api/v4/projects/:id/ci/lint"
```

### Debug Mode

Enable verbose logging:

```yaml
variables:
  CI_DEBUG_TRACE: "true"  # WARNING: Exposes secrets in logs!
```

Use only for debugging, never in production.

### Reproducing Job Environment Locally

```bash
# Pull the job image
docker pull node:18-alpine

# Run interactively
docker run -it --rm -v $(pwd):/app -w /app node:18-alpine sh

# Inside container, run job commands
npm install
npm run build
npm test
```

### Testing with Docker Compose

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://db/testdb
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: testdb
```

```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## 18. Common Problems & Solutions

| Problem | Cause | Diagnostic Steps | Solution |
|---------|-------|------------------|----------|
| **Runner doesn't pick up jobs** | Wrong tags / runner paused | Check runner status in Settings > CI/CD > Runners | Verify tags match job tags; ensure runner is active |
| **`docker: command not found`** | Wrong executor (shell instead of docker) | Check runner config.toml | Use docker executor or install Docker in shell executor |
| **SAST job times out** | Large codebase / slow analyzer | Check job logs for progress | Increase timeout: `timeout: 2h` or exclude paths |
| **Container image push fails** | Registry permissions / token expired | Check `docker login` output | Use deploy token or regenerate CI_JOB_TOKEN |
| **K8s deploy fails: Unauthorized** | Invalid kubeconfig / RBAC denied | `kubectl auth can-i create deployment` | Check service account permissions and role bindings |
| **Vulnerabilities block MR** | Critical findings / false positives | Review Security tab in MR | Tune analyzers, adjust severity threshold, or dismiss false positives |
| **Slow pipelines** | Sequential stages / no caching | Review pipeline graph | Use `needs:`, enable caching, parallelize jobs |
| **Artifacts fill storage** | No expiration set | Check Settings > CI/CD > Artifacts | Set `expire_in: 1 week` on artifacts |
| **Cache not working** | Wrong cache key / different runners | Check cache key in job logs | Use consistent cache keys; configure shared cache (S3) |
| **Job fails: `permission denied`** | File permissions / wrong user | `ls -la` in job | Fix file permissions or run as correct user |
| **Out of memory** | Insufficient runner resources | Check runner logs / system resources | Increase runner memory limits in config.toml |
| **`fatal: could not read Username`** | Git submodule auth failure | Check submodule URLs | Use CI_JOB_TOKEN or deploy keys for submodules |
| **Review app not accessible** | DNS not configured / ingress issue | `kubectl get ingress -n <namespace>` | Configure DNS wildcard; check ingress controller |
| **Pipeline stuck on pending** | No available runners | Check runner status | Register more runners or increase concurrency |
| **Docker build fails: `no space left`** | Disk full on runner | `df -h` on runner host | Clean up Docker: `docker system prune -a` |
| **Helm upgrade fails** | Chart syntax error / values mismatch | `helm lint ./chart` | Fix chart syntax; verify values.yaml |
| **Environment not created** | Missing `environment:` key | Check job definition | Add `environment: name: production` to job |
| **Secrets exposed in logs** | Echoing variables / debug mode | Search logs for secret values | Mark variables as masked; disable CI_DEBUG_TRACE |
| **Job fails intermittently** | Network issues / flaky tests | Re-run job multiple times | Add retry: `retry: max: 2` |
| **Cannot pull private image** | Missing registry credentials | Check `docker login` in before_script | Add registry login to before_script |

### Detailed Troubleshooting Examples

#### Problem: Runner Not Picking Up Jobs

```bash
# On runner host
sudo gitlab-runner verify
sudo gitlab-runner list
sudo journalctl -u gitlab-runner -f

# Check runner status in GitLab UI
# Settings > CI/CD > Runners
# Ensure runner is:
# - Active (not paused)
# - Has matching tags
# - Not locked to other projects
```

#### Problem: Docker Build Fails

```yaml
# Add debugging to docker build job
docker-build:
  before_script:
    - docker info  # Verify Docker is working
    - docker version
    - df -h  # Check disk space
  script:
    - docker build -t test .
  after_script:
    - docker images  # List built images
```

#### Problem: Kubernetes Deployment Unauthorized

```bash
# Test kubectl access
kubectl auth can-i create deployment --namespace=production

# Check service account
kubectl get serviceaccount gitlab -n gitlab-runner
kubectl describe serviceaccount gitlab -n gitlab-runner

# Verify role bindings
kubectl get rolebinding -n production
kubectl describe rolebinding gitlab-deploy -n production
```

---

## 19. Compliance & Security Lifecycle

### Vulnerability Workflow

1. **Detection** - Scanner finds vulnerability in MR
2. **Notification** - Security widget shows in MR UI
3. **Review** - Security team reviews finding
4. **Triage** - Mark as:
   - **Confirmed** - Real vulnerability
   - **Dismissed** - False positive / accepted risk
   - **Resolved** - Fixed in code
5. **Remediation** - Create issue, assign developer
6. **Verification** - Re-scan after fix
7. **Close** - Mark as resolved

### Creating Issues from Vulnerabilities

In MR Security tab:
1. Click on vulnerability
2. Click "Create issue"
3. Issue auto-populated with details
4. Assign to developer

### Security Policies (EE)

**Security > Policies**

Create scan execution policies:

```yaml
name: Enforce SAST and Dependency Scanning
description: Run security scans on all MRs
enabled: true
rules:
  - type: pipeline
    branches:
      - main
      - release/*
actions:
  - scan: sast
  - scan: dependency_scanning
```

### Blocking Merges on Vulnerabilities

```yaml
# Require security scans to pass
include:
  - template: Security/SAST.gitlab-ci.yml

sast:
  allow_failure: false  # Block MR if vulnerabilities found
```

Or use **Merge Request Approval Rules**:
- Require security team approval if vulnerabilities found

### Compliance Frameworks

**Settings > General > Compliance framework**

Apply frameworks like:
- SOC 2
- HIPAA
- PCI-DSS

Enforces:
- Required pipelines
- Approval rules
- Audit logging

---

## 20. Example Repository Layout & Deliverables

```
my-app/
├── .gitlab-ci.yml                 # Main CI/CD pipeline
├── .gitlab/
│   └── ci/                        # Modular CI templates
│       ├── build.yml
│       ├── test.yml
│       ├── security.yml
│       └── deploy.yml
├── Dockerfile                     # Container image definition
├── .dockerignore                  # Exclude files from image
├── docker-compose.yml             # Local development
├── k8s/                           # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
├── helm/                          # Helm chart (alternative to k8s/)
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-staging.yaml
│   ├── values-production.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── ingress.yaml
├── scripts/                       # Deployment scripts
│   ├── deploy.sh
│   ├── rollback.sh
│   └── health-check.sh
├── src/                           # Application source
├── tests/                         # Test files
├── docs/                          # Documentation
│   ├── DEPLOYMENT.md
│   ├── RUNBOOK.md
│   └── ARCHITECTURE.md
└── README.md                      # Project overview
```

---

## 21. Example MR Checklist

```markdown
## Merge Request Checklist

### Code Quality
- [ ] Code follows project style guide
- [ ] No linting errors
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Code coverage >= 80%

### Security
- [ ] SAST scan passed (no critical/high)
- [ ] Dependency scan passed (no critical/high)
- [ ] No secrets committed
- [ ] Security review completed (if required)

### Pipeline
- [ ] Pipeline passed all stages
- [ ] Build successful
- [ ] All tests passed
- [ ] Container image built and scanned
- [ ] No critical vulnerabilities in image

### Deployment
- [ ] Review app deployed successfully
- [ ] Manual testing completed on review app
- [ ] Database migrations tested (if applicable)
- [ ] Environment variables documented

### Documentation
- [ ] README updated (if needed)
- [ ] API documentation updated
- [ ] Changelog updated
- [ ] Deployment notes added

### Approvals
- [ ] Code review approved (2+ reviewers)
- [ ] Security team approved (if required)
- [ ] Product owner approved (if required)

### Pre-Merge
- [ ] Rebased on latest main
- [ ] No merge conflicts
- [ ] Squashed commits (if required)
- [ ] Descriptive commit messages
```

---

## 22. Rollback & Release Strategies

### Tagging Releases

```bash
# Create release tag
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3

# Pipeline automatically deploys tagged version
```

### Automated Rollback on Health Check Failure

```yaml
deploy_production:
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
    - kubectl rollout status deployment/app
  after_script:
    - |
      if ! curl -f https://example.com/health; then
        echo "Health check failed, rolling back"
        kubectl rollout undo deployment/app
        exit 1
      fi
```

### Manual Rollback

```yaml
rollback_production:
  stage: deploy
  script:
    - kubectl rollout undo deployment/app -n production
  environment:
    name: production
  when: manual
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### Blue/Green Deployment

```yaml
deploy_green:
  script:
    - kubectl apply -f k8s/deployment-green.yaml
    - kubectl wait --for=condition=available deployment/app-green
    - kubectl patch service app -p '{"spec":{"selector":{"version":"green"}}}'
```

### Canary Deployment

```yaml
deploy_canary:
  script:
    - helm upgrade app ./helm --set canary.enabled=true --set canary.weight=10
  environment:
    name: production/canary

deploy_full:
  script:
    - helm upgrade app ./helm --set canary.enabled=false
  when: manual
  needs: [deploy_canary]
```

---

## 23. Maintenance & Housekeeping

### Registry Cleanup

**Automated**: Settings > Packages & Registries > Cleanup policy

**Manual**:
```bash
# Delete old tags
curl --request DELETE --header "PRIVATE-TOKEN: <token>" \
  "https://gitlab.com/api/v4/projects/:id/registry/repositories/:repo_id/tags/:tag"
```

### Runner Maintenance

```bash
# Update runner
sudo gitlab-runner stop
sudo apt-get update
sudo apt-get install gitlab-runner
sudo gitlab-runner start

# Clean up Docker
docker system prune -a --volumes
```

### Artifact Retention

**Settings > CI/CD > Artifacts**

```
Default expiration: 30 days
Keep artifacts from most recent successful jobs: Yes
```

### Pipeline Retention

**Settings > CI/CD > Pipelines**

```
Delete pipelines older than: 90 days
```

### Dependency Updates

```yaml
# Scheduled pipeline for dependency updates
dependency_update:
  script:
    - npm update
    - bundle update
  rules:
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
  artifacts:
    paths:
      - package-lock.json
      - Gemfile.lock
```

### Scanner Updates

Scanners auto-update, but you can pin versions:

```yaml
include:
  - template: Security/SAST.gitlab-ci.yml

sast:
  variables:
    SAST_ANALYZER_IMAGE_TAG: "3.10.0"  # Pin specific version
```

---

## 24. Advanced Topics / Optional Add-ons

### GitOps with GitLab and ArgoCD

```yaml
# Push manifests to GitOps repo
gitops_sync:
  script:
    - git clone https://gitlab.com/myorg/gitops-repo.git
    - cd gitops-repo
    - yq eval ".image.tag = \"$CI_COMMIT_TAG\"" -i apps/myapp/values.yaml
    - git commit -am "Update myapp to $CI_COMMIT_TAG"
    - git push
```

### Infrastructure as Code Scanning

```yaml
include:
  - template: Terraform/Base.gitlab-ci.yml

terraform:
  extends: .terraform:build
  variables:
    TF_ROOT: terraform/
```

### Serverless Deployments

```yaml
deploy_lambda:
  image: node:18
  script:
    - npm install -g serverless
    - serverless deploy --stage production
  environment:
    name: production
```

### Container Scanning with Trivy

```yaml
trivy_scan:
  image: aquasec/trivy:latest
  script:
    - trivy image --severity HIGH,CRITICAL $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

### Advanced Auto DevOps Customization

```yaml
include:
  - template: Auto-DevOps.gitlab-ci.yml

# Override build job
build:
  extends: .auto-devops-build
  before_script:
    - echo "Custom build preparation"
  variables:
    AUTO_DEVOPS_BUILD_IMAGE_EXTRA_ARGS: "--build-arg NPM_TOKEN=$NPM_TOKEN"
```

---

## 25. Final Deliverables & File List

This guide includes the following files:

```
gitlab-cicd-guide/
├── README.md                          # This comprehensive guide
├── .gitlab-ci.yml                     # Full production pipeline
├── .gitlab-ci-modular.yml            # Modular pipeline example
├── ci-templates/                      # Reusable CI templates
│   ├── build.yml
│   ├── test.yml
│   ├── security.yml
│   ├── docker.yml
│   ├── deploy-k8s.yml
│   └── deploy-vm.yml
├── examples/                          # Sample application
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── app/
│   │   └── main.py
│   ├── k8s/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   └── helm/
│       ├── Chart.yaml
│       └── values.yaml
├── runner-setup/
│   ├── RUNNER-SETUP.md               # Runner installation guide
│   ├── runner-config.toml            # Recommended config
│   └── register-runner.sh            # Registration script
├── troubleshooting/
│   └── TROUBLESHOOTING.md            # Detailed troubleshooting
├── diagrams/
│   └── architecture.txt              # ASCII diagrams
└── checklists/
    ├── MR-CHECKLIST.md               # Merge request checklist
    └── DEPLOYMENT-CHECKLIST.md       # Deployment checklist
```

---

## 26. Next Steps & Summary

### Summary

You now have a complete, production-ready GitLab CI/CD pipeline that:

✅ **Automates** the entire software delivery lifecycle
✅ **Secures** your code with SAST, Dependency, Container, and DAST scanning
✅ **Deploys** to Kubernetes and VM environments
✅ **Monitors** application health and performance
✅ **Scales** with auto-scaling runners and optimized pipelines
✅ **Governs** with approvals, protected environments, and audit logs

### Quick Start

1. **Copy `.gitlab-ci.yml`** to your project root
2. **Register a GitLab Runner** (see `runner-setup/RUNNER-SETUP.md`)
3. **Configure CI/CD variables** (database passwords, API keys, etc.)
4. **Push to GitLab** and watch your pipeline run!
5. **Review security findings** in Merge Requests
6. **Deploy to staging** on main branch
7. **Tag a release** to deploy to production

### Next Actions

- [ ] Set up GitLab Runner on your infrastructure
- [ ] Configure Container Registry cleanup policies
- [ ] Enable security scanners (SAST, Dependency, Container)
- [ ] Create protected environments for production
- [ ] Set up merge request approval rules
- [ ] Configure monitoring and alerts
- [ ] Document your deployment process
- [ ] Train team on GitLab CI/CD workflows

### Learning Resources

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [GitLab CI/CD Examples](https://docs.gitlab.com/ee/ci/examples/)
- [GitLab Security Scanning](https://docs.gitlab.com/ee/user/application_security/)
- [GitLab Runner Documentation](https://docs.gitlab.com/runner/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

### Support

- **GitLab Forum**: https://forum.gitlab.com/
- **GitLab Issues**: https://gitlab.com/gitlab-org/gitlab/-/issues
- **Stack Overflow**: Tag `gitlab-ci`

---

**Happy CI/CD! 🚀**
