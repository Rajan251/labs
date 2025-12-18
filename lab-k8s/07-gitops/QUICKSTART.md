# GitOps Lab - Quick Start Guide

## ⚡ Get Up and Running in 30 Minutes

This guide will help you set up a minimal but functional GitOps environment with ArgoCD and deploy your first application using the GitOps workflow.

## 📋 Prerequisites Check

Before starting, ensure you have:

```bash
# Check Docker is running
docker ps

# Check you have at least 8GB RAM and 4 CPU cores
free -h
nproc
```

## 🚀 30-Minute Setup

### Step 1: Choose Your Kubernetes Cluster (5 minutes)

**Option A: Minikube (Recommended for beginners)**

```bash
# Install Minikube (macOS)
brew install minikube

# Install Minikube (Linux)
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start cluster
minikube start --cpus=4 --memory=8192 --driver=docker

# Verify
kubectl get nodes
```

**Option B: Kind (Faster startup)**

```bash
# Install Kind (macOS/Linux)
brew install kind
# OR
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Create cluster
kind create cluster --name gitops-lab

# Verify
kubectl get nodes
```

### Step 2: Install ArgoCD (5 minutes)

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD using kubectl
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods to be ready (this takes 2-3 minutes)
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# Verify all pods are running
kubectl get pods -n argocd
```

Expected output:
```
NAME                                  READY   STATUS    RESTARTS   AGE
argocd-application-controller-0       1/1     Running   0          2m
argocd-dex-server-xxx                 1/1     Running   0          2m
argocd-redis-xxx                      1/1     Running   0          2m
argocd-repo-server-xxx                1/1     Running   0          2m
argocd-server-xxx                     1/1     Running   0          2m
```

### Step 3: Access ArgoCD UI (5 minutes)

```bash
# Port-forward ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Get initial admin password
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo "ArgoCD Password: $ARGOCD_PASSWORD"

# Save credentials
echo "Username: admin"
echo "Password: $ARGOCD_PASSWORD"
```

**Access the UI:**
1. Open browser to: https://localhost:8080
2. Accept the self-signed certificate warning
3. Login with username: `admin` and the password from above
4. You should see the ArgoCD dashboard!

### Step 4: Install ArgoCD CLI (5 minutes)

```bash
# macOS
brew install argocd

# Linux
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd

# Verify installation
argocd version

# Login via CLI
argocd login localhost:8080 --username admin --password $ARGOCD_PASSWORD --insecure

# Test CLI
argocd cluster list
```

### Step 5: Deploy Your First Application (10 minutes)

We'll deploy a simple nginx application using GitOps!

**Create Application Manifest:**

```bash
cd /home/rk/Documents/labs/lab-k8s/07-gitops

# Create a simple nginx application
cat <<EOF > /tmp/nginx-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nginx-quickstart
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: HEAD
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF

# Apply the application
kubectl apply -f /tmp/nginx-app.yaml

# Watch the sync
argocd app get nginx-quickstart --refresh
```

**Verify Deployment:**

```bash
# Check application status
argocd app list

# View application details
argocd app get nginx-quickstart

# Check pods
kubectl get pods -n default

# Port-forward to access the application
kubectl port-forward svc/guestbook-ui -n default 8081:80 &

# Open browser to http://localhost:8081
```

### Step 6: Test GitOps Workflow (5 minutes)

Now let's see GitOps in action!

**View the Status:**

```bash
# In ArgoCD UI (https://localhost:8080):
# 1. Click on the "nginx-quickstart" application
# 2. You'll see the visual representation of all resources
# 3. Click on any resource to see details

# In CLI:
argocd app get nginx-quickstart
argocd app history nginx-quickstart
```

**Test Auto-Sync:**

The application is configured to auto-sync. If you make changes in the Git repository, ArgoCD will automatically deploy them!

```bash
# Watch for changes (ArgoCD checks every 3 minutes by default)
watch -n 5 "argocd app get nginx-quickstart | grep -A 5 'Health Status'"
```

## ✅ Verification Checklist

- [ ] Kubernetes cluster is running (`kubectl get nodes`)
- [ ] ArgoCD pods are running (`kubectl get pods -n argocd`)
- [ ] ArgoCD UI is accessible (https://localhost:8080)
- [ ] ArgoCD CLI is working (`argocd version`)
- [ ] nginx-quickstart application is synced and healthy
- [ ] Application is accessible (http://localhost:8081)

## 🎉 Success!

You now have a working GitOps environment! Here's what you've accomplished:

✅ Kubernetes cluster running locally  
✅ ArgoCD installed and configured  
✅ First application deployed via GitOps  
✅ Auto-sync enabled for continuous deployment

## 🎓 What's Next?

### Learn GitOps Concepts
```bash
# Read about GitOps principles
cat concepts/README.md
```

### Try the Practice Exercises
```bash
# Start with Exercise 01
cd exercises/01-first-deployment
cat README.md
```

### Deploy Sample Applications
```bash
# Explore the guestbook multi-tier app
cd applications/guestbook
cat README.md
```

### Setup Monitoring
```bash
# Install Prometheus and Grafana
cd monitoring
cat README.md
```

## 🔧 Quick Reference Commands

```bash
# ArgoCD Application Management
argocd app list                           # List all applications
argocd app get <app-name>                 # Get application details
argocd app sync <app-name>                # Manually sync application
argocd app history <app-name>             # View sync history
argocd app rollback <app-name> <revision> # Rollback to previous version

# Kubernetes Commands
kubectl get pods -n <namespace>           # List pods
kubectl describe pod <pod-name>           # Pod details
kubectl logs <pod-name>                   # View logs
kubectl get events -n <namespace>         # View events

# ArgoCD UI Access
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Application Access
kubectl port-forward svc/<service-name> -n <namespace> 8081:80
```

## 🧹 Quick Cleanup

If you want to clean up everything:

```bash
# Delete the application
argocd app delete nginx-quickstart

# Uninstall ArgoCD
kubectl delete namespace argocd

# Delete Kubernetes cluster
minikube delete  # or: kind delete cluster --name gitops-lab
```

## 🐛 Troubleshooting

### ArgoCD Pods Not Starting

```bash
# Check pod status
kubectl describe pod -l app.kubernetes.io/name=argocd-server -n argocd

# Check logs
kubectl logs -l app.kubernetes.io/name=argocd-server -n argocd

# Common fix: Increase cluster resources
minikube delete
minikube start --cpus=4 --memory=10240
```

### Application Not Syncing

```bash
# Force refresh
argocd app get <app-name> --refresh --hard-refresh

# Check sync status
argocd app get <app-name>

# View events
kubectl get events -n argocd
```

### Cannot Access ArgoCD UI

```bash
# Check port-forward is running
ps aux | grep port-forward

# Restart port-forward
pkill -f "port-forward.*argocd-server"
kubectl port-forward svc/argocd-server -n argocd 8080:443 &
```

### Forgot ArgoCD Password

```bash
# Retrieve password again
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo
```

## 📚 Next Steps

1. **Understand the Architecture** - Read [README.md](README.md) for complete overview
2. **Learn GitOps Concepts** - Deep dive into [concepts/README.md](concepts/README.md)
3. **Follow Learning Path** - Start with beginner path in main README
4. **Practice Exercises** - Complete [exercises/01-first-deployment](exercises/01-first-deployment/)
5. **Setup Monitoring** - Install Prometheus/Grafana from [monitoring/](monitoring/)

## 💡 Pro Tips

1. **Use auto-sync cautiously** - Enable for dev, manual for prod
2. **Always use Git** - Never make manual changes to the cluster
3. **Use Kustomize overlays** - Manage environment-specific configs
4. **Monitor sync status** - Set up alerts for OutOfSync applications
5. **Version everything** - Tag your releases in Git

---

**Congratulations! You're now ready to explore the full GitOps lab!** 🚀

For detailed documentation, see [README.md](README.md)
