# GitOps Concepts

## What is GitOps?

**GitOps** is an operational framework that takes DevOps best practices used for application development (version control, collaboration, compliance, CI/CD) and applies them to infrastructure automation.

Git becomes the single source of truth for declarative infrastructure and applications.

## Core Principles

### 1. Declarative

A system managed by GitOps must have its desired state expressed declaratively.

**Example:**
```yaml
# Declarative: What you want
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 3
```

### 2. Versioned and Immutable

Desired state is stored in a way that enforces immutability, versioning, and retains a complete version history.

**Git provides:**
- Complete history
- Branching and merging
- Rollback capability
- Audit trail

### 3. Pulled Automatically

Software agents automatically pull the desired state declarations from the source.

**ArgoCD** continuously monitors Git and syncs changes to the cluster.

### 4. Continuously Reconciled

Software agents continuously observe actual system state and attempt to apply the desired state.

**Self-healing:** Manual changes are automatically reverted to match Git.

## Pull vs Push Deployment

### Traditional CI/CD (Push)

```
CI Server → [Push] → Kubernetes Cluster
```

**Issues:**
- CI server needs cluster credentials
- Security risk
- No drift detection

### GitOps (Pull)

```
Git ← [Pull] ← ArgoCD (in cluster)
```

**Benefits:**
- No external credentials
- Automatic drift detection
- Self-healing

## GitOps Workflow

```
Developer → Git Commit → CI Build → Container Registry
                ↓
        Update Manifest
                ↓
        ArgoCD Detects → Apply to Cluster → Self-Heal
```

## Key Components

### 1. Git Repository

- Single source of truth
- Version control
- Collaboration platform
- Audit trail

### 2. ArgoCD

- Continuous delivery tool
- Monitors Git
- Applies changes
- Ensures synchronization

### 3. Kubernetes Cluster

- Target environment
- Runs applications
- Monitored by ArgoCD

## Benefits

✅ **Faster deployments** - Git commit triggers deployment  
✅ **Easy rollbacks** - `git revert` to rollback  
✅ **Audit trail** - Complete history in Git  
✅ **Consistency** - Same process for all environments  
✅ **Security** - No external cluster access needed  
✅ **Collaboration** - PRs for infrastructure changes  

## Next Steps

- [Prerequisites Setup](documentation/01-prerequisites-setup.md)
- [ArgoCD Installation](documentation/02-argocd-installation.md)
- [Lab 01: First Deployment](labs/lab-01-first-deployment.md)
