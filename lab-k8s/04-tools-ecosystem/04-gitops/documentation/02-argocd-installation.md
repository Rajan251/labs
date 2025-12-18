# ArgoCD Installation and Configuration

## Overview

This guide walks you through installing and configuring ArgoCD on your local Kubernetes cluster. ArgoCD is the GitOps continuous delivery tool that will monitor your Git repository and automatically sync changes to your cluster.

## Prerequisites

- ✅ Kubernetes cluster running (Minikube/Kind/K3d)
- ✅ kubectl configured and working
- ✅ Helm 3.0+ installed

Verify prerequisites:
```bash
kubectl get nodes
# Should show at least one node in Ready status

helm version
# Should show v3.x.x
```

## Installation Methods

We'll cover three installation methods. **Helm is recommended** for production-like setups.

### Method 1: Helm Installation (Recommended)

Helm provides easier customization and upgrades.

#### Step 1: Add Helm Repository

```bash
# Add ArgoCD Helm repository
helm repo add argo https://argoproj.github.io/argo-helm

# Update repositories
helm repo update

# Verify repository added
helm search repo argocd
```

#### Step 2: Create Namespace

```bash
kubectl create namespace argocd
```

#### Step 3: Install ArgoCD

```bash
# Install with default values
helm install argocd argo/argo-cd \
  --namespace argocd \
  --version 5.51.0

# Or install with custom values (recommended)
helm install argocd argo/argo-cd \
  --namespace argocd \
  --version 5.51.0 \
  --values ../setup/argocd-values.yaml
```

**Custom values example** (`setup/argocd-values.yaml`):
```yaml
server:
  service:
    type: ClusterIP
  
global:
  image:
    tag: "v2.9.3"
    
configs:
  params:
    server.insecure: true  # For local development
    
redis:
  enabled: true
  
dex:
  enabled: false  # Disable SSO for local setup
```

#### Step 4: Wait for Pods to be Ready

```bash
# Watch pods until all are Running
kubectl get pods -n argocd -w

# Or wait with timeout
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=argocd-server \
  -n argocd \
  --timeout=300s
```

Expected output:
```
NAME                                               READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                    1/1     Running   0          2m
argocd-applicationset-controller-xxx               1/1     Running   0          2m
argocd-dex-server-xxx                              1/1     Running   0          2m
argocd-notifications-controller-xxx                1/1     Running   0          2m
argocd-redis-xxx                                   1/1     Running   0          2m
argocd-repo-server-xxx                             1/1     Running   0          2m
argocd-server-xxx                                  1/1     Running   0          2m
```

### Method 2: kubectl Manifests

Direct installation using kubectl (less flexible):

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods
kubectl wait --for=condition=ready pod --all -n argocd --timeout=300s
```

### Method 3: Using Automation Script

We've provided an automated installation script:

```bash
cd /home/rk/Documents/labs/lab-k8s/04-tools-ecosystem/04-gitops

# Make script executable
chmod +x scripts/install-argocd.sh

# Run installation
./scripts/install-argocd.sh
```

The script will:
- Check prerequisites
- Create namespace
- Install ArgoCD via Helm
- Wait for pods to be ready
- Retrieve initial admin password
- Set up port-forwarding (optional)

## Accessing ArgoCD UI

### Option 1: Port Forward (Recommended for Local Setup)

```bash
# Forward ArgoCD server port
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Access in browser: https://localhost:8080
```

Keep this terminal open. Open a new terminal for other commands.

### Option 2: Ingress (Production-Like)

For production setups, use an Ingress controller:

```bash
# Enable Ingress addon (Minikube)
minikube addons enable ingress

# Create Ingress resource
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
spec:
  ingressClassName: nginx
  rules:
  - host: argocd.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: argocd-server
            port:
              number: 443
EOF

# Add to /etc/hosts
echo "$(minikube ip) argocd.local" | sudo tee -a /etc/hosts

# Access: https://argocd.local
```

### Option 3: LoadBalancer (For Cloud Providers)

```bash
# Patch service to LoadBalancer
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# Get external IP (may take a few minutes)
kubectl get svc argocd-server -n argocd

# Access using EXTERNAL-IP
```

## Initial Login

### Get Admin Password

```bash
# Retrieve initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
echo
```

Save this password! Example: `XyZ123AbC456`

### Login to UI

1. Open browser: https://localhost:8080 (or your Ingress/LoadBalancer URL)
2. Accept the self-signed certificate warning (for local setup)
3. Username: `admin`
4. Password: (from the command above)

### Change Admin Password

**Via UI:**
1. Click on "User Info" (top right)
2. Click "Update Password"
3. Enter old and new password

**Via CLI:**
```bash
# Login first
argocd login localhost:8080

# Update password
argocd account update-password
```

## ArgoCD CLI Installation

The CLI provides powerful management capabilities.

### Install ArgoCD CLI

```bash
# macOS
brew install argocd

# Linux
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64

# Verify
argocd version
```

### Login via CLI

```bash
# Login (use port-forwarded endpoint)
argocd login localhost:8080

# Enter username: admin
# Enter password: (your password)

# For non-interactive login
argocd login localhost:8080 \
  --username admin \
  --password 'your-password' \
  --insecure
```

### Useful CLI Commands

```bash
# List applications
argocd app list

# Get application details
argocd app get <app-name>

# Sync application
argocd app sync <app-name>

# View application logs
argocd app logs <app-name>

# Delete application
argocd app delete <app-name>
```

## Configuration

### Configure Git Repository

Add your Git repository to ArgoCD:

**Via UI:**
1. Go to Settings → Repositories
2. Click "Connect Repo"
3. Choose connection method (HTTPS or SSH)
4. Enter repository URL
5. Add credentials if private repo
6. Click "Connect"

**Via CLI:**
```bash
# Public repository
argocd repo add https://github.com/your-username/gitops-demo-repo

# Private repository with username/password
argocd repo add https://github.com/your-username/private-repo \
  --username your-username \
  --password your-token

# Private repository with SSH
argocd repo add git@github.com:your-username/private-repo.git \
  --ssh-private-key-path ~/.ssh/id_rsa
```

### RBAC Configuration (Optional)

For multi-user setups, configure Role-Based Access Control:

```yaml
# argocd-rbac-cm ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly
  policy.csv: |
    p, role:org-admin, applications, *, */*, allow
    p, role:org-admin, clusters, get, *, allow
    p, role:org-admin, repositories, *, *, allow
    g, admin@example.com, role:org-admin
```

Apply:
```bash
kubectl apply -f rbac-config.yaml
```

## Verification

### Check Installation

```bash
# All pods should be Running
kubectl get pods -n argocd

# Service should be available
kubectl get svc -n argocd

# Check ArgoCD version
argocd version
```

### Create Test Application

```bash
# Create a simple test app
argocd app create guestbook \
  --repo https://github.com/argoproj/argocd-example-apps.git \
  --path guestbook \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default

# Sync the application
argocd app sync guestbook

# Check status
argocd app get guestbook
```

### Verify in UI

1. Go to Applications page
2. You should see "guestbook" application
3. Click on it to see the resource tree
4. All components should be "Healthy" and "Synced"

## Troubleshooting

### Common Issues

#### Issue 1: Pods in CrashLoopBackOff

**Symptoms:**
```bash
kubectl get pods -n argocd
# Some pods showing CrashLoopBackOff
```

**Solutions:**
```bash
# Check pod logs
kubectl logs -n argocd <pod-name>

# Describe pod
kubectl describe pod -n argocd <pod-name>

# Common fix: Increase resources
kubectl edit deployment argocd-server -n argocd
# Add resources.limits and resources.requests
```

#### Issue 2: Can't Access UI

**Symptoms:** Browser can't connect to localhost:8080

**Solutions:**
```bash
# Verify port-forward is running
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Check if service is available
kubectl get svc argocd-server -n argocd

# Try different port
kubectl port-forward svc/argocd-server -n argocd 9090:443
```

#### Issue 3: Initial Password Not Working

**Symptoms:** Can't login with retrieved password

**Solutions:**
```bash
# Re-retrieve password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# Reset admin password
kubectl -n argocd patch secret argocd-secret \
  -p '{"stringData": {
    "admin.password": "'$(htpasswd -nbBC 10 "" newpassword | tr -d ':\n' | sed 's/$2y/$2a/')'",
    "admin.passwordMtime": "'$(date +%FT%T%Z)'"
  }}'
```

#### Issue 4: ArgoCD Can't Connect to Git Repository

**Symptoms:** Repository connection fails

**Solutions:**
```bash
# Verify repository URL is correct
git ls-remote https://github.com/your-username/repo.git

# For private repos, ensure credentials are correct
argocd repo add https://github.com/your-username/repo.git \
  --username your-username \
  --password your-token

# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server
```

### Debug Commands

```bash
# Check all ArgoCD resources
kubectl get all -n argocd

# View controller logs (sync issues)
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller

# View server logs (UI/API issues)
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server

# View repo server logs (Git sync issues)
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server

# Check events
kubectl get events -n argocd --sort-by='.lastTimestamp'
```

## Next Steps

Now that ArgoCD is installed:

1. ✅ Read about [Repository Structure](03-repository-structure.md)
2. 🧪 Try [Lab 01 - First Deployment](../labs/lab-01-first-deployment.md)
3. 📚 Learn [Sample Applications](05-sample-applications.md)

## Additional Resources

- [ArgoCD Official Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Getting Started Guide](https://argo-cd.readthedocs.io/en/stable/getting_started/)
- [ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
