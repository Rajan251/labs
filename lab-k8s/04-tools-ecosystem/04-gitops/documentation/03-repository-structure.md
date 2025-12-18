# GitOps Repository Structure

## Overview

A well-organized GitOps repository is crucial for maintainability, scalability, and team collaboration. This guide covers best practices for structuring your GitOps repository.

## Repository Organization Patterns

### Pattern 1: Monorepo (Recommended for Small-Medium Projects)

Single repository containing all applications and infrastructure:

```
gitops-repo/
├── README.md
├── .github/
│   └── workflows/              # CI/CD pipelines
│       ├── ci-build.yaml
│       └── update-manifests.yaml
│
├── apps/                       # Application configurations
│   ├── frontend/
│   │   ├── base/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── ingress.yaml
│   │   │   └── kustomization.yaml
│   │   └── overlays/
│   │       ├── dev/
│   │       │   ├── kustomization.yaml
│   │       │   └── replicas-patch.yaml
│   │       ├── staging/
│   │       │   └── kustomization.yaml
│   │       └── prod/
│   │           ├── kustomization.yaml
│   │           └── resources-patch.yaml
│   │
│   ├── backend/
│   │   ├── base/
│   │   └── overlays/
│   │       ├── dev/
│   │       ├── staging/
│   │       └── prod/
│   │
│   └── database/
│       ├── base/
│       └── overlays/
│
├── infrastructure/             # Cluster infrastructure
│   ├── namespaces/
│   │   ├── dev.yaml
│   │   ├── staging.yaml
│   │   └── prod.yaml
│   │
│   ├── monitoring/
│   │   ├── prometheus/
│   │   └── grafana/
│   │
│   ├── networking/
│   │   ├── ingress-nginx/
│   │   └── network-policies/
│   │
│   └── storage/
│       └── storage-classes/
│
├── argocd/                     # ArgoCD configurations
│   ├── applications/
│   │   ├── frontend-dev.yaml
│   │   ├── frontend-staging.yaml
│   │   ├── frontend-prod.yaml
│   │   └── app-of-apps.yaml
│   │
│   └── projects/
│       ├── dev-project.yaml
│       ├── staging-project.yaml
│       └── prod-project.yaml
│
├── charts/                     # Custom Helm charts
│   ├── common/                 # Library charts
│   └── app-template/
│
└── scripts/                    # Utility scripts
    ├── generate-manifests.sh
    └── validate-yaml.sh
```

**Pros:**
- ✅ Single source of truth
- ✅ Easy to navigate
- ✅ Simplified CI/CD
- ✅ Atomic changes across apps

**Cons:**
- ❌ Can become large
- ❌ Potential for merge conflicts
- ❌ Less granular access control

### Pattern 2: Polyrepo (For Large Organizations)

Separate repositories for different concerns:

```
org/app-1-config/          # Application 1 manifests
org/app-2-config/          # Application 2 manifests
org/infrastructure-config/ # Infrastructure manifests
org/argocd-apps/          # ArgoCD Application definitions
```

**Pros:**
- ✅ Better separation of concerns
- ✅ Granular access control
- ✅ Smaller repositories
- ✅ Team ownership

**Cons:**
- ❌ Harder to track dependencies
- ❌ More complex CI/CD
- ❌ Potential version misalignment

## Kustomize vs Helm

### When to Use Kustomize

**Best for:**
- Simple applications
- Environment-specific patches
- Pure Kubernetes manifests
- When you want full control

**Example Structure:**
```
app/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   ├── replicas.yaml      # Patch: 1 replica
    │   └── resources.yaml     # Patch: minimal resources
    └── prod/
        ├── kustomization.yaml
        ├── replicas.yaml      # Patch: 5 replicas
        └── resources.yaml     # Patch: production resources
```

**base/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml

commonLabels:
  app: myapp
```

**overlays/dev/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
  - ../../base

namePrefix: dev-

replicas:
  - name: myapp
    count: 1

patchesStrategicMerge:
  - resources.yaml
```

### When to Use Helm

**Best for:**
- Complex applications
- Reusable templates
- Community charts
- Values-based configuration

**Example Structure:**
```
charts/myapp/
├── Chart.yaml
├── values.yaml          # Default values
├── values-dev.yaml      # Dev overrides
├── values-staging.yaml  # Staging overrides
├── values-prod.yaml     # Prod overrides
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    └── ingress.yaml
```

## Multi-Environment Management

### Strategy 1: Kustomize Overlays

**Directory structure:**
```
apps/myapp/
├── base/                    # Common configuration
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── dev/                 # Dev environment
    │   ├── kustomization.yaml
    │   ├── namespace.yaml
    │   └── patches/
    │       ├── replicas.yaml
    │       └── image.yaml
    ├── staging/             # Staging environment
    │   └── kustomization.yaml
    └── prod/                # Production environment
        ├── kustomization.yaml
        ├── hpa.yaml         # HPA only in prod
        └── patches/
            ├── replicas.yaml
            └── resources.yaml
```

**overlays/dev/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: myapp-dev

bases:
  - ../../base

images:
  - name: myapp
    newTag: dev-latest

replicas:
  - name: myapp
    count: 1

patches:
  - path: patches/resources.yaml
```

**overlays/prod/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: myapp-prod

bases:
  - ../../base

images:
  - name: myapp
    newTag: v1.2.3  # Specific version in prod

replicas:
  - name: myapp
    count: 5

resources:
  - hpa.yaml  # Add HPA in production

patches:
  - path: patches/resources.yaml
```

### Strategy 2: Helm Values Files

**values-dev.yaml:**
```yaml
replicaCount: 1

image:
  repository: myapp
  tag: dev-latest
  pullPolicy: Always

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi

autoscaling:
  enabled: false

ingress:
  enabled: true
  hostname: myapp-dev.local
```

**values-prod.yaml:**
```yaml
replicaCount: 5

image:
  repository: myapp
  tag: v1.2.3  # Specific version
  pullPolicy: IfNotPresent

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  hostname: myapp.production.com
  tls:
    enabled: true
```

## Secret Management

### Option 1: Sealed Secrets (Recommended for GitOps)

Encrypt secrets so they can be safely stored in Git.

**Install Sealed Secrets Controller:**
```bash
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets -n kube-system
```

**Create and seal a secret:**
```bash
# Create regular secret (don't commit this!)
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password=secretpass \
  --dry-run=client -o yaml > secret.yaml

# Seal it
kubeseal -f secret.yaml -w sealed-secret.yaml

# Commit sealed-secret.yaml to Git
```

**sealed-secret.yaml:**
```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-credentials
  namespace: myapp
spec:
  encryptedData:
    username: AgBj8... # Encrypted data
    password: AgCx9... # Encrypted data
```

### Option 2: External Secrets Operator

Reference secrets from external secret managers (AWS Secrets Manager, Vault, etc.):

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: db-credentials
  data:
    - secretKey: username
      remoteRef:
        key: prod/db/credentials
        property: username
    - secretKey: password
      remoteRef:
        key: prod/db/credentials
        property: password
```

### Option 3: Git-Crypt (Simple Encryption)

Encrypt specific files in Git repository:

```bash
# Install git-crypt
brew install git-crypt  # macOS
sudo apt-get install git-crypt  # Linux

# Initialize in repo
cd gitops-repo
git-crypt init

# Add encryption pattern
echo "secrets/*.yaml filter=git-crypt diff=git-crypt" >> .gitattributes

# Add collaborator
git-crypt add-gpg-user user@example.com
```

## ArgoCD Application Manifests

### Basic Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-dev
  namespace: argocd
spec:
  project: default
  
  source:
    repoURL: https://github.com/myorg/gitops-repo.git
    targetRevision: main
    path: apps/myapp/overlays/dev
  
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp-dev
  
  syncPolicy:
    automated:
      prune: true      # Delete resources not in Git
      selfHeal: true   # Revert manual changes
    
    syncOptions:
      - CreateNamespace=true
    
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### Application with Helm

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-prod
  namespace: argocd
spec:
  project: production
  
  source:
    repoURL: https://github.com/myorg/gitops-repo.git
    targetRevision: v1.2.3  # Specific tag for prod
    path: charts/myapp
    helm:
      valueFiles:
        - values-prod.yaml
      parameters:
        - name: image.tag
          value: "v1.2.3"
  
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp-prod
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: false  # Manual intervention for prod
```

### App of Apps Pattern

Manage all applications from a single root application:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root-app
  namespace: argocd
spec:
  project: default
  
  source:
    repoURL: https://github.com/myorg/gitops-repo.git
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

## Best Practices

### 1. Use Branches for Environments

```
main → production
develop → staging
feature/* → dev
```

### 2. Tag Releases

```bash
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3
```

Reference specific tags in production ArgoCD Applications.

### 3. Separate Application and Infrastructure

```
gitops-repo/
├── apps/          # Application configurations
└── infrastructure/ # Cluster infrastructure
```

### 4. Use Meaningful Commit Messages

```bash
# Good
git commit -m "feat(frontend): update to v2.1.0"
git commit -m "fix(backend): increase memory limits"

# Bad
git commit -m "update"
git commit -m "fix"
```

### 5. Implement Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

## Validation

### Kustomize Validation

```bash
# Validate kustomize build
kustomize build apps/myapp/overlays/dev

# Dry-run apply
kustomize build apps/myapp/overlays/dev | kubectl apply --dry-run=client -f -
```

### Helm Validation

```bash
# Validate template rendering
helm template myapp charts/myapp -f charts/myapp/values-dev.yaml

# Lint chart
helm lint charts/myapp
```

## Next Steps

- [Sample Applications Guide](05-sample-applications.md)
- [CI/CD Integration](06-cicd-integration.md)
- [Lab 01 - First Deployment](../labs/lab-01-first-deployment.md)
