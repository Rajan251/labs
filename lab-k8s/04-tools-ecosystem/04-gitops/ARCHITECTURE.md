# GitOps Lab Architecture & Design

## System Architecture Overview

### High-Level Architecture

```mermaid
graph TB
    subgraph "Developer Workspace"
        DEV[Developer]
        GIT_CLIENT[Git Client]
    end
    
    subgraph "Git Repository GitHub"
        REPO[GitOps Repository]
        MANIFESTS[Kubernetes Manifests]
        WORKFLOWS[GitHub Actions]
    end
    
    subgraph "CI Pipeline"
        GHA[GitHub Actions]
        BUILD[Build & Test]
        PUSH[Push to Registry]
        UPDATE[Update Manifests]
    end
    
    subgraph "Container Registry"
        REGISTRY[Docker Hub/GHCR]
        IMAGES[Container Images]
    end
    
    subgraph "Kubernetes Cluster"
        ARGOCD[ArgoCD Controller]
        
        subgraph "Dev Environment"
            DEV_NS[guestbook-dev]
            DEV_PODS[Application Pods]
        end
        
        subgraph "Staging Environment"
            STAGING_NS[guestbook-staging]
            STAGING_PODS[Application Pods]
        end
        
        subgraph "Production Environment"
            PROD_NS[guestbook-prod]
            PROD_PODS[Application Pods]
            HPA[Horizontal Pod Autoscaler]
        end
    end
    
    subgraph "Monitoring"
        PROMETHEUS[Prometheus]
        GRAFANA[Grafana]
        ALERTS[Alert Manager]
    end
    
    DEV -->|1. Write Code| GIT_CLIENT
    GIT_CLIENT -->|2. Push| REPO
    REPO -->|3. Trigger| GHA
    GHA --> BUILD
    BUILD -->|4. Build Image| PUSH
    PUSH -->|5. Push Image| REGISTRY
    PUSH -->|6. Update Tag| MANIFESTS
    
    ARGOCD -.->|7. Poll Every 3min| REPO
    ARGOCD -->|8. Detect Changes| MANIFESTS
    ARGOCD -->|9. Sync| DEV_NS
    ARGOCD -->|9. Sync| STAGING_NS
    ARGOCD -->|9. Sync| PROD_NS
    
    DEV_PODS -.->|10. Pull| REGISTRY
    STAGING_PODS -.->|10. Pull| REGISTRY
    PROD_PODS -.->|10. Pull| REGISTRY
    
    HPA -->|Scale| PROD_PODS
    
    PROMETHEUS -->|Scrape| ARGOCD
    PROMETHEUS -->|Scrape| DEV_PODS
    PROMETHEUS -->|Scrape| STAGING_PODS
    PROMETHEUS -->|Scrape| PROD_PODS
    GRAFANA -->|Query| PROMETHEUS
    ALERTS -->|Notify| DEV
```

## GitOps Flow Detailed

### 1. Development Workflow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as Git Repo
    participant CI as GitHub Actions
    participant Reg as Container Registry
    participant CD as ArgoCD
    participant K8s as Kubernetes
    
    Dev->>Git: 1. Commit code changes
    activate Git
    Git->>CI: 2. Webhook trigger
    deactivate Git
    
    activate CI
    CI->>CI: 3. Run tests
    CI->>CI: 4. Build container
    CI->>Reg: 5. Push image (tag: commit-sha)
    CI->>Git: 6. Update manifest (new tag)
    deactivate CI
    
    loop Every 3 minutes
        CD->>Git: 7a. Poll for changes
    end
    
    Note over CD: Alternative: Webhook
    Git-->>CD: 7b. Webhook notification
    
    activate CD
    CD->>CD: 8. Detect manifest change
    CD->>Git: 9. Fetch manifests
    CD->>K8s: 10. Apply manifests
    deactivate CD
    
    activate K8s
    K8s->>Reg: 11. Pull new image
    K8s->>K8s: 12. Rolling update pods
    deactivate K8s
    
    loop Continuous
        CD->>K8s: 13. Monitor state
        CD->>Git: 14. Compare desired state
        alt Drift detected
            CD->>K8s: 15. Auto-heal (revert)
        end
    end
```

### 2. Multi-Environment Strategy

```mermaid
graph LR
    subgraph "Git Repository"
        MAIN[main branch]
        DEV_OVERLAY[overlays/dev]
        STAGING_OVERLAY[overlays/staging]
        PROD_OVERLAY[overlays/prod]
        
        MAIN --> DEV_OVERLAY
        MAIN --> STAGING_OVERLAY
        MAIN --> PROD_OVERLAY
    end
    
    subgraph "ArgoCD Applications"
        APP_DEV[guestbook-dev]
        APP_STAGING[guestbook-staging]
        APP_PROD[guestbook-prod]
    end
    
    subgraph "Kubernetes Cluster"
        NS_DEV[Namespace: dev<br/>Replicas: 1<br/>Resources: minimal]
        NS_STAGING[Namespace: staging<br/>Replicas: 2<br/>Resources: moderate]
        NS_PROD[Namespace: prod<br/>Replicas: 3+<br/>Resources: high<br/>HPA enabled]
    end
    
    DEV_OVERLAY -->|Auto-sync| APP_DEV
    STAGING_OVERLAY -->|Auto-sync| APP_STAGING
    PROD_OVERLAY -->|Manual sync| APP_PROD
    
    APP_DEV --> NS_DEV
    APP_STAGING --> NS_STAGING
    APP_PROD --> NS_PROD
    
    style NS_DEV fill:#90EE90
    style NS_STAGING fill:#FFD700
    style NS_PROD fill:#FF6347
```

## Directory Structure

### Complete Lab Structure

```
04-gitops/
├── README.md                          # Main entry point
├── CONCEPTS.md                        # GitOps concepts
├── BENEFITS.md                        # Business case
├── ARCHITECTURE.md                    # This file
│
├── documentation/                     # Complete guides
│   ├── 01-prerequisites-setup.md      # System setup
│   ├── 02-argocd-installation.md      # ArgoCD install
│   ├── 03-repository-structure.md     # Repo design
│   ├── 04-gitops-concepts.md          # Core concepts
│   ├── 05-sample-applications.md      # App explanations
│   ├── 06-cicd-integration.md         # CI/CD pipelines
│   ├── 07-monitoring-observability.md # Monitoring
│   ├── 08-advanced-scenarios.md       # Advanced patterns
│   ├── 09-troubleshooting.md          # Common issues
│   └── 10-cleanup.md                  # Cleanup guide
│
├── examples/                          # Sample applications
│   ├── guestbook/                     # Multi-tier app
│   │   ├── base/
│   │   │   ├── deployment.yaml        # Base deployments
│   │   │   ├── service.yaml           # Base services
│   │   │   └── kustomization.yaml     # Base kustomize
│   │   └── overlays/
│   │       ├── dev/
│   │       │   └── kustomization.yaml # Dev config
│   │       ├── staging/
│   │       │   └── kustomization.yaml # Staging config
│   │       └── prod/
│   │           ├── kustomization.yaml # Prod config
│   │           └── hpa.yaml           # Production HPA
│   │
│   ├── wordpress/                     # StatefulSet example
│   │   └── (similar structure)
│   │
│   ├── argocd-apps/                   # ArgoCD Applications
│   │   ├── guestbook-dev.yaml
│   │   ├── guestbook-staging.yaml
│   │   ├── guestbook-prod.yaml
│   │   ├── app-of-apps.yaml
│   │   └── applicationset.yaml
│   │
│   ├── github-actions/                # CI/CD workflows
│   │   ├── build-push.yaml
│   │   ├── update-manifests.yaml
│   │   └── promote-to-staging.yaml
│   │
│   └── monitoring/                    # Monitoring configs
│       ├── prometheus-values.yaml
│       ├── grafana-dashboards/
│       │   └── argocd-dashboard.json
│       └── alerts/
│           └── argocd-alerts.yaml
│
├── labs/                              # Hands-on exercises
│   ├── lab-01-first-deployment.md
│   ├── lab-02-environment-promotion.md
│   ├── lab-03-rollback.md
│   ├── lab-04-drift-detection.md
│   └── lab-05-multi-app-management.md
│
├── scripts/                           # Automation scripts
│   ├── setup-cluster.sh               # Cluster setup
│   ├── install-argocd.sh              # ArgoCD install
│   ├── deploy-samples.sh              # Deploy apps
│   ├── cleanup.sh                     # Cleanup
│   └── validate-manifests.sh          # YAML validation
│
└── setup/                             # Base configurations
    ├── argocd-values.yaml
    └── app-of-apps.yaml
```

## Application Architecture

### Guestbook Application

```mermaid
graph TB
    subgraph "Frontend Tier"
        FE1[Frontend Pod 1]
        FE2[Frontend Pod 2]
        FE3[Frontend Pod 3]
        FE_SVC[Frontend Service<br/>ClusterIP]
    end
    
    subgraph "Cache Tier"
        MASTER[Redis Master<br/>Pod]
        REPLICA1[Redis Replica 1]
        REPLICA2[Redis Replica 2]
        REPLICA3[Redis Replica 3]
        MASTER_SVC[Redis Master Service]
        REPLICA_SVC[Redis Replica Service]
    end
    
    subgraph "Ingress"
        ING[Ingress<br/>guestbook.local]
    end
    
    subgraph "Auto Scaling"
        HPA_OBJ[HPA<br/>min: 3, max: 10<br/>CPU: 70%, Mem: 80%]
    end
    
    ING -->|Route /| FE_SVC
    FE_SVC --> FE1
    FE_SVC --> FE2
    FE_SVC --> FE3
    
    FE1 -->|Write| MASTER_SVC
    FE2 -->|Write| MASTER_SVC
    FE3 -->|Write| MASTER_SVC
    
    FE1 -->|Read| REPLICA_SVC
    FE2 -->|Read| REPLICA_SVC
    FE3 -->|Read| REPLICA_SVC
    
    MASTER_SVC --> MASTER
    REPLICA_SVC --> REPLICA1
    REPLICA_SVC --> REPLICA2
    REPLICA_SVC --> REPLICA3
    
    MASTER -.->|Replicate| REPLICA1
    MASTER -.->|Replicate| REPLICA2
    MASTER -.->|Replicate| REPLICA3
    
    HPA_OBJ -.->|Scale| FE1
    HPA_OBJ -.->|Scale| FE2
    HPA_OBJ -.->|Scale| FE3
    
    style ING fill:#4A90E2
    style FE_SVC fill:#7ED321
    style MASTER_SVC fill:#F5A623
    style REPLICA_SVC fill:#F5A623
    style HPA_OBJ fill:#BD10E0
```

## ArgoCD Architecture

### ArgoCD Components

```mermaid
graph TB
    subgraph "ArgoCD Namespace"
        SERVER[ArgoCD Server<br/>UI & API]
        CONTROLLER[Application Controller<br/>Sync Logic]
        REPO[Repo Server<br/>Git Operations]
        REDIS[Redis<br/>Cache]
        DEX[Dex<br/>SSO Optional]
        NOTIF[Notifications Controller]
    end
    
    subgraph "External Systems"
        GIT[Git Repository]
        K8S_API[Kubernetes API]
        SLACK[Slack/Email]
    end
    
    subgraph "Users"
        USER[User Browser]
        CLI[ArgoCD CLI]
    end
    
    USER -->|HTTPS| SERVER
    CLI -->|gRPC| SERVER
    
    SERVER --> REDIS
    CONTROLLER --> REDIS
    CONTROLLER -->|Fetch Manifests| REPO
    REPO -->|Clone/Pull| GIT
    
    CONTROLLER -->|Apply Resources| K8S_API
    CONTROLLER -->|Watch Resources| K8S_API
    
    NOTIF -->|Events| CONTROLLER
    NOTIF -->|Send| SLACK
    
    SERVER -.->|Optional SSO| DEX
    
    style SERVER fill:#4A90E2
    style CONTROLLER fill:#7ED321
    style REPO fill:#F5A623
```

## Sync Strategies

### Automated Sync (Dev Environment)

```mermaid
stateDiagram-v2
    [*] --> Synced: Initial State
    
    Synced --> OutOfSync: Git commit detected
    OutOfSync --> Progressing: Auto-sync triggered
    Progressing --> Synced: Sync successful
    Progressing --> Failed: Sync error
    Failed --> OutOfSync: Retry
    
    Synced --> OutOfSync: Manual cluster change
    OutOfSync --> Synced: Self-heal enabled
    
    note right of Synced
        All resources healthy
        Live state = Git state
    end note
    
    note right of OutOfSync
        Changes detected
        Auto-sync will trigger
    end note
```

### Manual Sync (Production Environment)

```mermaid
stateDiagram-v2
    [*] --> Synced: Initial State
    
    Synced --> OutOfSync: Git commit detected
    OutOfSync --> OutOfSync: Waiting for approval
    OutOfSync --> Progressing: Manual sync
    Progressing --> Synced: Sync successful
    Progressing --> Failed: Sync error
    Failed --> OutOfSync: Investigate & fix
    
    note right of OutOfSync
        Manual review required
        Admin must approve sync
    end note
```

## Resource Management Strategy

### Environment Resource Allocation

| Resource | Dev | Staging | Production |
|----------|-----|---------|------------|
| **Frontend Replicas** | 1 | 2 | 3-10 (HPA) |
| **Redis Replicas** | 1 | 2 | 3 |
| **CPU Request** | 50m | 100m | 200m |
| **CPU Limit** | 100m | 250m | 500m |
| **Memory Request** | 64Mi | 128Mi | 256Mi |
| **Memory Limit** | 128Mi | 256Mi | 512Mi |
| **Auto-Scaling** | ❌ | ❌ | ✅ |
| **Sync Policy** | Auto | Auto | Manual |
| **Self-Heal** | ✅ | ❌ | ❌ |

## GitOps Best Practices Applied

### 1. Separation of Concerns

```
Application Repository (Code)
    ↓
CI Pipeline builds image
    ↓
GitOps Repository (Config)
    ↓
ArgoCD deploys
    ↓
Kubernetes Cluster
```

### 2. Progressive Delivery

```
Commit → Dev → Tests → Staging → Validation → Production
  ↓        ↓            ↓                        ↓
Auto    Auto         Auto                    Manual
```

### 3. Drift Detection & Remediation

```mermaid
graph LR
    A[Desired State<br/>in Git] -->|Compare| C{Drift?}
    B[Actual State<br/>in Cluster] -->|Compare| C
    
    C -->|No| D[✓ Synced]
    C -->|Yes| E[OutOfSync]
    E -->|Self-Heal ON| F[Auto Remediate]
    E -->|Self-Heal OFF| G[Manual Review]
    F --> A
    G --> A
```

## Security Architecture

### RBAC Strategy

```mermaid
graph TB
    subgraph "Users & Groups"
        ADMIN[Admins]
        DEV_TEAM[Developers]
        OPS_TEAM[Operations]
    end
    
    subgraph "ArgoCD Projects"
        DEFAULT[default project]
        PROD[production project]
    end
    
    subgraph "Permissions"
        FULL[Full Access]
        READ[Read-Only]
        SYNC[Sync Permission]
    end
    
    ADMIN --> FULL
    FULL --> DEFAULT
    FULL --> PROD
    
    DEV_TEAM --> SYNC
    SYNC --> DEFAULT
    
    OPS_TEAM --> SYNC
    SYNC --> PROD
    
    DEV_TEAM --> READ
    READ --> PROD
```

### Secret Management Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Seal as Kubeseal CLI
    participant Git as Git Repo
    participant SC as Sealed Secrets Controller
    participant K8s as Kubernetes
    
    Dev->>Dev: Create plain secret.yaml
    Dev->>Seal: kubeseal secret.yaml
    Seal->>Seal: Encrypt with public key
    Seal-->>Dev: Return sealed-secret.yaml
    Dev->>Git: Commit sealed-secret
    
    ArgoCD->>Git: Fetch sealed-secret
    ArgoCD->>K8s: Apply SealedSecret
    SC->>K8s: Watch SealedSecret
    SC->>SC: Decrypt with private key
    SC->>K8s: Create plain Secret
    
    Note over K8s: Secret available<br/>to pods
```

## Monitoring & Observability

### Metrics Collection

```mermaid
graph TB
    subgraph "ArgoCD"
        APPS[Applications]
        CONTROLLER[Controller]
        SERVER[Server]
    end
    
    subgraph "Application Pods"
        POD1[Pod Metrics]
        POD2[Pod Metrics]
        POD3[Pod Metrics]
    end
    
    subgraph "Prometheus"
        PROM[Prometheus Server]
        RULES[Alert Rules]
    end
    
    subgraph "Visualization"
        GRAFANA[Grafana Dashboards]
        ALERTS[Alert Manager]
    end
    
    APPS -->|/metrics| PROM
    CONTROLLER -->|/metrics| PROM
    SERVER -->|/metrics| PROM
    POD1 -->|/metrics| PROM
    POD2 -->|/metrics| PROM
    POD3 -->|/metrics| PROM
    
    PROM --> RULES
    RULES --> ALERTS
    PROM --> GRAFANA
    
    ALERTS -->|Notify| DEV[Slack/Email]
```

### Key Metrics Tracked

1. **ArgoCD Metrics**
   - Application sync status
   - Sync operation duration
   - Repository fetch time
   - Number of applications per state

2. **Application Metrics**
   - Pod CPU/Memory usage
   - Request rate
   - Error rate
   - Latency (p50, p95, p99)

3. **DORA Metrics**
   - Deployment frequency
   - Lead time for changes
   - Mean time to recovery (MTTR)
   - Change failure rate

## Disaster Recovery

### Backup Strategy

```mermaid
graph LR
    subgraph "Git Repository"
        INFRA[Infrastructure Code]
        APPS[Application Manifests]
        ARGOCD[ArgoCD Applications]
    end
    
    subgraph "Backup"
        GIT_BACKUP[Git Backup<br/>GitHub/GitLab]
        K8S_BACKUP[etcd Backup<br/>Velero]
    end
    
    subgraph "Recovery"
        NEW_CLUSTER[New Cluster]
        RESTORE[Restore Process]
    end
    
    INFRA -.->|Replicate| GIT_BACKUP
    APPS -.->|Replicate| GIT_BACKUP
    ARGOCD -.->|Replicate| GIT_BACKUP
    
    GIT_BACKUP -->|1. Clone| RESTORE
    K8S_BACKUP -->|2. Restore State| RESTORE
    RESTORE -->|3. Apply| NEW_CLUSTER
    
    NEW_CLUSTER -->|4. ArgoCD Syncs| APPS
```

## Scaling Considerations

### Horizontal Scaling

- **Dev**: Single replica, minimal resources
- **Staging**: Multiple replicas for testing
- **Production**: HPA-managed, auto-scales 3-10 pods

### ArgoCD Scaling

For large deployments (100+ applications):
- Increase controller replicas
- Shard applications across controllers
- Adjust sync timeout and reconciliation interval
- Use ApplicationSets for templating

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Orchestration** | Kubernetes 1.28+ | Container orchestration |
| **GitOps** | ArgoCD 2.9+ | Continuous deployment |
| **Templating** | Kustomize | Environment management |
| **CI/CD** | GitHub Actions | Build & test |
| **Registry** | Docker Hub/GHCR | Image storage |
| **Monitoring** | Prometheus | Metrics collection |
| **Visualization** | Grafana | Dashboards |
| **Secrets** | Sealed Secrets | Secret encryption |
| **Local Cluster** | Minikube/Kind/K3d | Development clusters |

## Next Steps

1. **Setup**: Follow [Quick Start](../README.md#quick-start-30-minutes)
2. **Learn**: Complete [Lab 01](../labs/lab-01-first-deployment.md)
3. **Practice**: Try all 5 hands-on labs
4. **Explore**: Read [Advanced Scenarios](08-advanced-scenarios.md)
5. **Monitor**: Setup [Monitoring Stack](07-monitoring-observability.md)

---

**This architecture provides a production-ready GitOps foundation that scales from development to enterprise deployments.**
