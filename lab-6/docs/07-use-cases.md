# Real-World Use Cases

## Use Case 1: 3-Tier Web Application

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer (ALB)                   │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐           ┌────────▼───────┐
│  Web Tier      │           │   Web Tier     │
│  (Nginx)       │           │   (Nginx)      │
│  10.0.1.10     │           │   10.0.1.11    │
└───────┬────────┘           └────────┬───────┘
        │                             │
        └──────────────┬──────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐           ┌────────▼───────┐
│  App Tier      │           │   App Tier     │
│  (Docker)      │           │   (Docker)     │
│  10.0.2.20     │           │   10.0.2.21    │
└───────┬────────┘           └────────┬───────┘
        │                             │
        └──────────────┬──────────────┘
                       │
              ┌────────▼────────┐
              │   Database      │
              │   (RDS MySQL)   │
              │   10.0.3.30     │
              └─────────────────┘
```

### Implementation

See [examples/3-tier-app/README.md](../examples/3-tier-app/README.md) for complete code.

### Benefits
- High availability with multiple instances
- Separation of concerns
- Easy to scale each tier independently
- Automated deployment and configuration

---

## Use Case 2: Kubernetes Cluster Setup

### Architecture

```
┌──────────────────────────────────────────────────┐
│              Kubernetes Cluster                   │
│                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │  Master 1   │  │  Master 2   │  │ Master 3 │ │
│  │  (Control   │  │  (Control   │  │ (Control │ │
│  │   Plane)    │  │   Plane)    │  │  Plane)  │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
│                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │  Worker 1   │  │  Worker 2   │  │ Worker 3 │ │
│  │  (Pods)     │  │  (Pods)     │  │  (Pods)  │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└──────────────────────────────────────────────────┘
```

### Implementation

See [examples/kubernetes-cluster/README.md](../examples/kubernetes-cluster/README.md)

### Benefits
- Production-ready Kubernetes cluster
- Automated node provisioning and configuration
- Easy to add/remove nodes
- Consistent cluster setup

---

## Use Case 3: CI/CD Pipeline Integration

### GitHub Actions Workflow

Complete example in [examples/ci-cd-pipeline/.github/workflows/deploy.yml](../examples/ci-cd-pipeline/.github/workflows/deploy.yml)

### Workflow
1. Code pushed to repository
2. GitHub Actions triggered
3. Terraform provisions infrastructure
4. Ansible configures servers
5. Application deployed
6. Tests run
7. Notification sent

### Benefits
- Fully automated deployments
- Consistent environments
- Version-controlled infrastructure
- Audit trail of changes

---

[← Previous: Dynamic Inventory](06-dynamic-inventory.md) | [Next: Troubleshooting →](08-troubleshooting.md)
