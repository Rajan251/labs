# ArgoCD Installation Guide

## 🎯 Overview

This guide covers multiple methods to install ArgoCD on your Kubernetes cluster. Choose the method that best fits your needs.

## 📋 Prerequisites

- Kubernetes cluster running (Minikube or Kind)
- kubectl configured and connected to cluster
- Helm installed (for Helm installation method)

Verify prerequisites:
```bash
kubectl get nodes
helm version
```

---

## 🚀 Installation Methods

### Method 1: kubectl Manifests (Recommended for Learning)

This method is straightforward and uses the official ArgoCD manifests.

**Step 1: Create Namespace**

```bash
kubectl create namespace argocd
```

**Step 2: Install ArgoCD**

```bash
# Install the stable release
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods to be ready (2-3 minutes)
kubectl wait --for=condition=ready pod --all -n argocd --timeout=300s
```

**Step 3: Verify Installation**

```bash
# Check all pods are running
kubectl get pods -n argocd

# Expected output (all pods should be Running):
# NAME                                  READY   STATUS    RESTARTS   AGE
# argocd-application-controller-0       1/1     Running   0          2m
# argocd-applicationset-controller-xxx  1/1     Running   0          2m
# argocd-dex-server-xxx                 1/1     Running   0          2m
# argocd-notifications-controller-xxx   1/1     Running   0          2m
# argocd-redis-xxx                      1/1     Running   0          2m
# argocd-repo-server-xxx                1/1     Running   0          2m
# argocd-server-xxx                     1/1     Running   0          2m
```

**Step 4: Access ArgoCD Server**

```bash
# Port-forward the ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Get the initial admin password
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo "ArgoCD Admin Password: $ARGOCD_PASSWORD"

# Save credentials for later
echo "admin:$ARGOCD_PASSWORD" > ~/argocd-credentials.txt
```

**Step 5: Access UI**

1. Open browser to: https://localhost:8080
2. Accept the self-signed certificate warning
3. Login with:
   - Username: `admin`
   - Password: (from previous step)

---

### Method 2: Helm Chart Installation (Production-Ready)

Helm provides more configuration options and easier upgrades.

**Step 1: Add ArgoCD Helm Repository**

```bash
# Add repository
helm repo add argo https://argoproj.github.io/argo-helm

# Update repositories
helm repo update
```

**Step 2: Create Custom Values File**

```bash
cat <<EOF > /tmp/argocd-values.yaml
# Custom ArgoCD Values

## Server configuration
server:
  service:
    type: ClusterIP
  
  ## Enable insecure mode (no TLS) for easier local access
  extraArgs:
    - --insecure
  
  ## Resource limits
  resources:
    limits:
      cpu: 200m
      memory: 256Mi
    requests:
      cpu: 100m
      memory: 128Mi

## Controller configuration
controller:
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi

## Repo server configuration
repoServer:
  resources:
    limits:
      cpu: 200m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 256Mi

## Redis configuration
redis:
  resources:
    limits:
      cpu: 200m
      memory: 256Mi
    requests:
      cpu: 100m
      memory: 128Mi

## Dex (SSO) configuration
dex:
  enabled: true

## ApplicationSet controller
applicationSet:
  enabled: true

## Notifications controller
notifications:
  enabled: true
EOF
```

**Step 3: Install ArgoCD via Helm**

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
helm install argocd argo/argo-cd \
  --namespace argocd \
  --values /tmp/argocd-values.yaml \
  --version 5.51.0

# Wait for pods
kubectl wait --for=condition=ready pod --all -n argocd --timeout=300s
```

**Step 4: Verify Installation**

```bash
# Check Helm release
helm list -n argocd

# Check pods
kubectl get pods -n argocd

# Check services
kubectl get svc -n argocd
```

**Step 5: Access ArgoCD**

```bash
# Port-forward
kubectl port-forward svc/argocd-server -n argocd 8080:80 &

# Get password (same as Method 1)
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo "Password: $ARGOCD_PASSWORD"

# Open http://localhost:8080 (note: HTTP, not HTTPS due to --insecure flag)
```

---

### Method 3: Automated Script

We've provided a script for quick installation.

```bash
cd /home/rk/Documents/labs/lab-k8s/07-gitops/scripts

# Make script executable
chmod +x setup-cluster.sh install-argocd.sh

# Run installation
./install-argocd.sh

# Follow the on-screen instructions
```

---

## 🔧 ArgoCD CLI Installation

The ArgoCD CLI allows you to manage applications from the command line.

### macOS

```bash
# Install via Homebrew
brew install argocd

# Verify
argocd version
```

### Linux

```bash
# Download latest version
curl -sSL -o /tmp/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64

# Install
sudo install -m 555 /tmp/argocd /usr/local/bin/argocd

# Clean up
rm /tmp/argocd

# Verify
argocd version
```

### Windows (WSL2)

```bash
# Same as Linux
curl -sSL -o /tmp/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 /tmp/argocd /usr/local/bin/argocd
rm /tmp/argocd
argocd version
```

### Login to ArgoCD via CLI

```bash
# Port-forward should be running (see previous steps)
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Get password
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

# Login (use --insecure for self-signed certs)
argocd login localhost:8080 \
  --username admin \
  --password $ARGOCD_PASSWORD \
  --insecure

# Test CLI
argocd cluster list
argocd app list
```

---

## 🔐 Security Configuration

### Change Default Password

**IMPORTANT**: Change the default admin password immediately!

**Via UI:**
1. Login to ArgoCD UI
2. Click on "User Info" (top right)
3. Click "Update Password"
4. Enter current and new password

**Via CLI:**

```bash
# Login first
argocd login localhost:8080 --username admin --password $ARGOCD_PASSWORD --insecure

# Update password
argocd account update-password \
  --current-password $ARGOCD_PASSWORD \
  --new-password 'YourNewSecurePassword123!'

# Delete the initial secret (optional)
kubectl -n argocd delete secret argocd-initial-admin-secret
```

### Create Additional Users (Optional)

```bash
# Edit argocd-cm ConfigMap
kubectl edit configmap argocd-cm -n argocd

# Add users section:
# data:
#   accounts.developer: apiKey, login
#   accounts.readonly: apiKey, login

# Set password for new user
argocd account update-password \
  --account developer \
  --new-password 'DeveloperPassword123!'
```

### Configure RBAC (Optional)

```bash
# Edit argocd-rbac-cm ConfigMap
kubectl edit configmap argocd-rbac-cm -n argocd

# Add RBAC policies:
# data:
#   policy.csv: |
#     p, role:developer, applications, *, */*, allow
#     p, role:readonly, applications, get, */*, allow
#     g, developer, role:developer
#     g, readonly, role:readonly
```

---

## 🌐 Access Methods

### 1. Port-Forward (Development)

```bash
# HTTP (if using --insecure flag)
kubectl port-forward svc/argocd-server -n argocd 8080:80

# HTTPS (default installation)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Access: https://localhost:8080
```

### 2. Ingress (Production)

**With Minikube:**

```bash
# Enable ingress addon
minikube addons enable ingress

# Create Ingress resource
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
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

### 3. LoadBalancer (Cloud)

```bash
# Change service type to LoadBalancer
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# Get external IP (may take a few minutes)
kubectl get svc argocd-server -n argocd

# Access using the EXTERNAL-IP
```

---

## ✅ Verification Steps

### 1. Check Pod Status

```bash
# All pods should be Running
kubectl get pods -n argocd

# Check pod logs if any issues
kubectl logs -n argocd deployment/argocd-server
kubectl logs -n argocd deployment/argocd-repo-server
kubectl logs -n argocd statefulset/argocd-application-controller
```

### 2. Test UI Access

```bash
# Ensure port-forward is running
ps aux | grep port-forward

# Try accessing UI
curl -k https://localhost:8080

# Should return HTML content
```

### 3. Test CLI

```bash
# List clusters
argocd cluster list

# List applications (should be empty initially)
argocd app list

# Get version
argocd version

# Expected output should show both client and server versions
```

### 4. Deploy Test Application

```bash
# Create a test app
argocd app create test-nginx \
  --repo https://github.com/argoproj/argocd-example-apps.git \
  --path guestbook \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default

# Sync the app
argocd app sync test-nginx

# Check status
argocd app get test-nginx

# Clean up
argocd app delete test-nginx
```

---

## 🐛 Troubleshooting

### Issue: Pods Not Starting

```bash
# Check pod events
kubectl describe pod -l app.kubernetes.io/name=argocd-server -n argocd

# Check resource availability
kubectl top nodes
kubectl describe nodes

# Solution: Increase cluster resources
minikube delete
minikube start --cpus=6 --memory=10240
```

### Issue: ImagePullBackOff

```bash
# Check pod status
kubectl get pods -n argocd

# Describe the failing pod
kubectl describe pod <pod-name> -n argocd

# Common cause: Docker rate limiting
# Solution: Wait a few minutes or use a Docker Hub account
docker login
```

### Issue: CrashLoopBackOff

```bash
# Check logs
kubectl logs -n argocd <pod-name> --previous

# Common causes:
# 1. Insufficient memory - increase cluster memory
# 2. Configuration error - check ConfigMaps
# 3. Network issues - check cluster networking

# Check configmaps
kubectl get configmap -n argocd
kubectl describe configmap argocd-cm -n argocd
```

### Issue: Cannot Access UI

```bash
# Check port-forward
ps aux | grep port-forward
# If not running, start it:
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Check service
kubectl get svc argocd-server -n argocd

# Check firewall/browser
# Try: curl -k https://localhost:8080
```

### Issue: Forgot Admin Password

```bash
# Retrieve password again
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo

# If secret was deleted, reset password:
# 1. Scale down argocd-server
kubectl scale deployment argocd-server -n argocd --replicas=0

# 2. Update password hash in argocd-secret
# (Use bcrypt to generate hash)

# 3. Scale back up
kubectl scale deployment argocd-server -n argocd --replicas=1
```

### Issue: ArgoCD Out of Sync

```bash
# Force refresh all apps
argocd app list -o name | xargs -I {} argocd app get {} --refresh

# Hard refresh (bypasses cache)
argocd app list -o name | xargs -I {} argocd app get {} --hard-refresh
```

---

## 🧹 Uninstallation

### Uninstall kubectl Installation

```bash
# Delete ArgoCD
kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Delete namespace
kubectl delete namespace argocd
```

### Uninstall Helm Installation

```bash
# Uninstall release
helm uninstall argocd -n argocd

# Delete namespace
kubectl delete namespace argocd
```

---

## 📊 Resource Usage

Typical resource usage for ArgoCD:

| Component | Memory | CPU |
|-----------|--------|-----|
| argocd-server | 128-256Mi | 100-200m |
| argocd-application-controller | 512Mi-1Gi | 500m-1000m |
| argocd-repo-server | 256-512Mi | 100-200m |
| argocd-redis | 128-256Mi | 100-200m |
| argocd-dex-server | 64-128Mi | 50-100m |
| **Total** | **~1-2Gi** | **~1-2 cores** |

---

## 🎓 Next Steps

ArgoCD is now installed! Continue with:

1. **Understand ArgoCD**: Explore the UI and familiarize yourself with concepts
2. **Deploy First App**: [exercises/01-first-deployment](../exercises/01-first-deployment/)
3. **Configure Applications**: [gitops-repo/README.md](../gitops-repo/README.md)
4. **Setup Monitoring**: [monitoring/README.md](../monitoring/README.md)

---

## 📚 Additional Resources

- [ArgoCD Official Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Getting Started Guide](https://argo-cd.readthedocs.io/en/stable/getting_started/)
- [ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
- [ArgoCD Operator Manual](https://argo-cd.readthedocs.io/en/stable/operator-manual/)
