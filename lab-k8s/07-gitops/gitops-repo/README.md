# GitOps Repository Structure

## 🎯 Overview

This directory demonstrates best practices for organizing a GitOps repository. It follows a structured approach to manage applications and infrastructure across multiple environments using Kustomize and Helm.

## 📁 Repository Structure

```
gitops-repo/
├── apps/                           # Application configurations
│   ├── guestbook/                  # Multi-tier guestbook application
│   │   ├── base/                   # Base manifests (common across environments)
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── configmap.yaml
│   │   │   └── kustomization.yaml
│   │   └── overlays/               # Environment-specific configs
│   │       ├── dev/
│   │       │   └── kustomization.yaml
│   │       ├── staging/
│   │       │   └── kustomization.yaml
│   │       └── prod/
│   │           └── kustomization.yaml
│   └── wordpress/                  # Stateful WordPress application
│       ├── base/
│       │   ├── wordpress-deployment.yaml
│       │   ├── mysql-statefulset.yaml
│       │   ├── pvc.yaml
│       │   └── kustomization.yaml
│       └── overlays/
│           ├── dev/
│           ├── staging/
│           └── prod/
├── infrastructure/                 # Cluster infrastructure configs
│   ├── namespaces/                 # Namespace definitions
│   │   ├── dev.yaml
│   │   ├── staging.yaml
│   │   └── prod.yaml
│   ├── monitoring/                 # Monitoring stack (Prometheus, Grafana)
│   │   ├── prometheus/
│   │   └── grafana/
│   ├── networking/                 # Network policies, Ingress
│   │   └── ingress/
│   └── storage/                    # Storage classes, PVs
│       └── local-storage.yaml
├── argocd/                         # ArgoCD configuration
│   └── applications/               # ArgoCD Application manifests
│       ├── guestbook-dev.yaml
│       ├── guestbook-staging.yaml
│       ├── guestbook-prod.yaml
│       ├── wordpress-dev.yaml
│       ├── applicationset-example.yaml
│       └── app-of-apps.yaml
├── charts/                         # Custom Helm charts
│   └── custom-app/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
└── .github/                        # CI/CD workflows
    └── workflows/
        ├── ci-build.yaml           # Build and test
        ├── update-gitops.yaml      # Update manifests with new image tags
        └── promote-environment.yaml # Promote between environments
```

## 🏗️ Design Principles

### 1. Environment Separation with Kustomize

**Base Layer**: Common configuration shared across all environments
**Overlay Layer**: Environment-specific patches and customizations

```
apps/guestbook/
├── base/                    # What's common?
│   ├── deployment.yaml      # - Deployment structure
│   ├── service.yaml         # - Service definition
│   └── kustomization.yaml   # - Base kustomization
└── overlays/
    ├── dev/                 # What's different in dev?
    │   └── kustomization.yaml  # - 1 replica, dev image tag, less resources
    ├── staging/
    │   └── kustomization.yaml  # - 2 replicas, staging tag, moderate resources
    └── prod/
        └── kustomization.yaml  # - 3+ replicas, stable tag, full resources, HPA
```

**Benefits**:
- ✅ DRY (Don't Repeat Yourself) - base is defined once
- ✅ Easy to see environment differences
- ✅ Consistent structure across environments
- ✅ Simple to add new environments

### 2. Application vs Infrastructure Separation

**apps/**: Application code deployments (your microservices, frontends, backends)
**infrastructure/**: Cluster-level components (monitoring, networking, storage)

**Why separate?**
- Different change frequencies (apps change often, infra rarely)
- Different approval workflows (apps = dev team, infra = platform team)
- Different sync policies (apps = auto-sync, infra = manual)

### 3. Self-Documenting Structure

Each directory has a clear purpose:
- `base/` = "What's common to all environments?"
- `overlays/dev/` = "What's unique to development?"
- `argocd/applications/` = "How is this deployed?"

## 🔑 Key Patterns

### Pattern 1: Kustomize Overlays

**Base Configuration** (`apps/guestbook/base/deployment.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: guestbook
spec:
  replicas: 1  # Will be overridden
  template:
    spec:
      containers:
      - name: guestbook
        image: gcr.io/google-samples/gb-frontend:v4  # Will be overridden
        resources:
          requests:
            memory: "64Mi"  # Will be overridden
            cpu: "100m"
```

**Dev Overlay** (`apps/guestbook/overlays/dev/kustomization.yaml`):

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
  - ../../base

namespace: dev

# Dev-specific patches
replicas:
  - name: guestbook
    count: 1

images:
  - name: gcr.io/google-samples/gb-frontend
    newTag: v4-dev

# Add dev-specific labels
commonLabels:
  environment: dev
  
# Resource patches
patches:
  - patch: |-
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/memory
        value: "32Mi"
    target:
      kind: Deployment
      name: guestbook
```

**Production Overlay** (`apps/guestbook/overlays/prod/kustomization.yaml`):

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
  - ../../base

namespace: production

replicas:
  - name: guestbook
    count: 3

images:
  - name: gcr.io/google-samples/gb-frontend
    newTag: v4.0.0  # Stable tag

commonLabels:
  environment: production

# Production gets more resources
patches:
  - patch: |-
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/memory
        value: "128Mi"
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/memory
        value: "256Mi"
    target:
      kind: Deployment
      name: guestbook

# Add HPA for prod
resources:
  - hpa.yaml
```

### Pattern 2: Secret Management

**DO NOT** commit secrets directly to Git!

**Option A: Sealed Secrets** (Recommended for this lab)

```yaml
# Create a SealedSecret (encrypted)
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: mysql-password
  namespace: production
spec:
  encryptedData:
    password: AgBqX7JMTnfP...  # Encrypted, safe to commit
```

**Option B: External Secrets**

```yaml
# Reference to external secret store (Vault, AWS Secrets Manager)
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: mysql-password
spec:
  secretStoreRef:
    name: vault-backend
  data:
  - secretKey: password
    remoteRef:
      key: database/mysql
      property: password
```

### Pattern 3: App-of-Apps Pattern

Use a parent Application to manage multiple child Applications.

**app-of-apps.yaml**:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: all-apps
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/gitops-repo
    targetRevision: main
    path: argocd/applications
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

This deploys all Applications defined in `argocd/applications/`.

## 🔄 GitOps Workflow

### Making Changes via Git

**Scenario**: Update guestbook to version v5 in production

```bash
# 1. Clone the GitOps repository
git clone https://github.com/your-org/gitops-repo
cd gitops-repo

# 2. Create a feature branch
git checkout -b update-guestbook-prod-v5

# 3. Edit the production overlay
cd apps/guestbook/overlays/prod
vim kustomization.yaml

# Change:
# images:
#   - name: gcr.io/google-samples/gb-frontend
#     newTag: v5.0.0

# 4. Test the kustomization locally
kustomize build .

# 5. Commit and push
git add kustomization.yaml
git commit -m "Update guestbook to v5.0.0 in production"
git push origin update-guestbook-prod-v5

# 6. Create Pull Request
# - Request review from team
# - Run automated tests
# - After approval, merge to main

# 7. ArgoCD automatically syncs (or manually trigger)
argocd app sync guestbook-prod
```

### Environment Promotion

Promote a successful deployment from dev → staging → prod:

```bash
# After testing in dev, promote to staging
cd apps/guestbook/overlays/staging
vim kustomization.yaml
# Update image tag to match dev

# After testing in staging, promote to prod
cd ../prod
vim kustomization.yaml
# Update image tag to match staging

# Commit all changes
git add .
git commit -m "Promote guestbook v5.0.0 dev → staging → prod"
git push origin main
```

Or use a GitHub Action (see `.github/workflows/promote-environment.yaml`).

## 🎯 Best Practices

### 1. Keep Base Minimal

Only put truly common configuration in `base/`. Anything that differs should go in overlays.

### 2. Use Semantic Versioning for Images

```yaml
# Good
images:
  - name: myapp
    newTag: v1.2.3  # Semantic version

# Avoid
images:
  - name: myapp
    newTag: latest  # Unpredictable
```

### 3. Document Environment Differences

Add comments in kustomization.yaml:

```yaml
# Production Configuration
# - 3 replicas for high availability
# - Increased resource limits
# - HPA enabled (min: 3, max: 10)
# - Production database endpoint
```

### 4. Use Namespaces for Environment Isolation

```yaml
# dev overlay
namespace: dev

# staging overlay
namespace: staging

# prod overlay
namespace: production
```

### 5. Implement Resource Limits

Always set resource requests and limits:

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

## 🧪 Testing Locally

Before committing, test your Kustomize configurations:

```bash
# Build and view the output
kustomize build apps/guestbook/overlays/dev

# Apply dry-run to check validation
kustomize build apps/guestbook/overlays/dev | kubectl apply --dry-run=client -f -

# Compare dev vs prod
diff <(kustomize build apps/guestbook/overlays/dev) \
     <(kustomize build apps/guestbook/overlays/prod)
```

## 📊 Repository Metrics

Track these metrics to ensure healthy GitOps practices:

- **Deployment Frequency**: How often do you deploy?
- **Lead Time**: Time from commit to production
- **Mean Time to Recovery (MTTR)**: How fast can you rollback?
- **Change Failure Rate**: Percentage of deployments causing issues

All these are improved with GitOps!

## 🚀 Getting Started

1. **Fork this repository**
2. **Clone locally**: `git clone https://github.com/your-org/gitops-repo`
3. **Create your apps**: Copy `apps/guestbook/` as a template
4. **Deploy with ArgoCD**: `kubectl apply -f argocd/applications/your-app.yaml`
5. **Make changes via Git**: Edit, commit, push, watch ArgoCD sync!

## 📚 Additional Resources

- [Kustomize Documentation](https://kustomize.io/)
- [ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
- [GitOps Principles](https://opengitops.dev/)

---

**Remember**: In GitOps, Git is the source of truth. Any change to your cluster should be a Git commit! 🚀
