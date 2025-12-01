# ArgoCD GitOps Integration

This directory contains all ArgoCD configurations and Kubernetes manifests for GitOps-based continuous deployment.

## 📁 Directory Structure

```
argocd-gitops/
├── applications/           # ArgoCD Application definitions
│   └── my-app.yaml        # Application manifest
├── manifests/             # Kubernetes manifests per environment
│   ├── dev/
│   │   └── deployment.yaml
│   ├── qa/
│   │   └── deployment.yaml
│   └── prod/
│       └── deployment.yaml
└── scripts/               # Setup and management scripts
    ├── setup-argocd.sh    # Install ArgoCD
    └── create-app.sh      # Create ArgoCD application
```

## 🚀 Quick Start

### 1. Install ArgoCD

```bash
cd scripts
chmod +x setup-argocd.sh
./setup-argocd.sh
```

### 2. Access ArgoCD UI

```bash
# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Access UI at: https://argocd.company.com
# Username: admin
# Password: (from above command)
```

### 3. Create Application

```bash
chmod +x create-app.sh
export ARGOCD_PASSWORD="your-password"
./create-app.sh my-app dev https://github.com/your-org/gitops-repo.git manifests/dev
```

## 📝 How It Works

### GitOps Workflow

```
[Developer] → [Git Push] → [Jenkins CI] → [Build & Test] → [Push to Artifactory]
                                                ↓
                                    [Update GitOps Repo]
                                                ↓
                                    [ArgoCD Detects Change]
                                                ↓
                                    [Auto Sync to Kubernetes]
```

### Jenkins Integration

Your Jenkins pipeline should:
1. Build and test the application
2. Build Docker image
3. Push image to Artifactory
4. Update image tag in GitOps repository
5. ArgoCD automatically syncs the changes

Example Jenkins stage:

```groovy
stage('Update GitOps Repo') {
    steps {
        script {
            sh """
                git clone https://github.com/your-org/gitops-repo.git
                cd gitops-repo
                sed -i 's|image: .*|image: artifactory.company.com/docker-local/my-app:${VERSION}|g' manifests/dev/deployment.yaml
                git add manifests/dev/deployment.yaml
                git commit -m "Update my-app to version ${VERSION}"
                git push origin main
            """
        }
    }
}
```

## 🔧 Configuration

### ArgoCD Application Manifest

Located in `applications/my-app.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/gitops-repo.git
    targetRevision: main
    path: manifests/dev
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Kubernetes Manifests

Each environment has its own manifest:
- `manifests/dev/deployment.yaml` - Development (2 replicas)
- `manifests/qa/deployment.yaml` - QA (3 replicas)
- `manifests/prod/deployment.yaml` - Production (5 replicas + HPA)

## 🎯 Best Practices

### 1. Separate Git Repositories
- **Application Code**: `app-repo` (Jenkins builds from here)
- **GitOps Config**: `gitops-repo` (ArgoCD syncs from here)

### 2. Environment Isolation
- Use separate namespaces: `dev`, `qa`, `prod`
- Different resource limits per environment
- Separate ArgoCD applications per environment

### 3. Automated Sync
- Enable `automated` sync policy
- Use `prune: true` to remove deleted resources
- Use `selfHeal: true` to auto-fix drift

### 4. Image Pull from Artifactory
Create secret for Artifactory:

```bash
kubectl create secret docker-registry artifactory-secret \
  --docker-server=artifactory.company.com \
  --docker-username=your-user \
  --docker-password=your-password \
  -n dev
```

## 📊 Monitoring

### Check Application Status

```bash
# Via CLI
argocd app get my-app

# Via kubectl
kubectl get application my-app -n argocd
```

### View Sync History

```bash
argocd app history my-app
```

### Rollback to Previous Version

```bash
argocd app rollback my-app <revision-number>
```

## 🔄 Manual Operations

### Force Sync

```bash
argocd app sync my-app
```

### Refresh Application

```bash
argocd app refresh my-app
```

### Delete Application

```bash
argocd app delete my-app
```

## 🛡️ Security

### RBAC Configuration

ArgoCD supports RBAC for fine-grained access control:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.csv: |
    p, role:developer, applications, get, */*, allow
    p, role:developer, applications, sync, */dev/*, allow
    g, developer-group, role:developer
```

## 📚 Additional Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitOps Principles](https://www.gitops.tech/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

---

**Created for GitOps-based CD** 🚀
