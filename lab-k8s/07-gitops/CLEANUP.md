# Cleanup Procedures

## 🧹 Complete Lab Cleanup

This guide provides step-by-step instructions to clean up all resources created during the GitOps lab.

## ⚡ Quick Cleanup (Everything)

Run this script to remove everything:

```bash
cd /home/rk/Documents/labs/lab-k8s/07-gitops/scripts
./cleanup-all.sh
```

## 📝 Manual Cleanup Steps

If you prefer to clean up manually or selectively:

### 1. Delete ArgoCD Applications

```bash
# List all applications
argocd app list

# Delete all applications
argocd app delete --all

# Or delete individually
argocd app delete guestbook-dev
argocd app delete guestbook-staging
argocd app delete guestbook-prod

# Via kubectl
kubectl delete applications --all -n argocd
```

### 2. Uninstall ArgoCD

**If installed via kubectl:**

```bash
# Delete ArgoCD resources
kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Delete namespace
kubectl delete namespace argocd
```

**If installed via Helm:**

```bash
# Uninstall Helm release
helm uninstall argocd -n argocd

# Delete namespace
kubectl delete namespace argocd
```

### 3. Delete Application Namespaces

```bash
# Delete GitOps-created namespaces
kubectl delete namespace dev
kubectl delete namespace staging
kubectl delete namespace production

# Or delete all at once
kubectl delete namespace dev staging production
```

### 4. Delete Kubernetes Cluster

**Minikube:**

```bash
# Stop cluster
minikube stop

# Delete cluster
minikube delete

# Verify deletion
minikube status
```

**Kind:**

```bash
# Delete cluster
kind delete cluster --name gitops-lab

# Verify deletion
kind get clusters
```

### 5. Clean Up Local Files

```bash
# Remove saved credentials
rm -f ~/argocd-credentials.txt

# Remove temporary files
rm -f /tmp/nginx-app.yaml
rm -f /tmp/argocd-values.yaml

# Stop any running port-forwards
pkill -f "port-forward.*argocd-server"
pkill -f "port-forward.*guestbook"
pkill -f "port-forward.*grafana"
pkill -f "port-forward.*prometheus"
```

### 6. Clean Up Docker Resources (Optional)

```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes
docker volume prune -f

# WARNING: This removes ALL unused Docker resources
docker system prune -a -f --volumes
```

### 7. Clean Up Git Repository (if created)

If you created a Git repository for this lab:

```bash
# Navigate to the repository
cd ~/gitops-lab-config

# Remove local repository
cd ..
rm -rf gitops-lab-config

# On GitHub: Go to repository → Settings → Delete this repository
```

## 🔍 Verify Cleanup

Run these commands to ensure everything is cleaned up:

```bash
# Check Kubernetes cluster
minikube status  # Should show "host: Stopped" or error
kind get clusters  # Should not list gitops-lab

# Check ArgoCD
kubectl get namespace argocd  # Should show "not found"

# Check applications
kubectl get all -n dev  # Should show "not found"
kubectl get all -n staging  # Should show "not found"
kubectl get all -n production  # Should show "not found"

# Check port-forwards
ps aux | grep port-forward  # Should show no argocd/app port-forwards

# Check Docker containers (for local cluster)
docker ps  # Should show no minikube/kind containers
```

## 📦 Selective Cleanup

### Keep Cluster, Remove Only Applications

```bash
# Delete applications but keep ArgoCD
argocd app delete --all

# Delete application namespaces
kubectl delete namespace dev staging production
```

### Keep ArgoCD, Remove Applications

```bash
# Delete applications
argocd app delete --all

# Keep ArgoCD running for future use
```

### Reset ArgoCD (Fresh Start)

```bash
# Delete all applications
kubectl delete applications --all -n argocd

# Delete ArgoCD namespace (will reinstall later)
kubectl delete namespace argocd

# Reinstall (see installation.md)
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

## 🔄 Cleanup Script

Create an automated cleanup script:

```bash
#!/bin/bash
# cleanup-all.sh

set -e

echo "🧹 Starting GitOps Lab Cleanup..."

# 1. Delete ArgoCD applications
echo "Deleting ArgoCD applications..."
kubectl delete applications --all -n argocd 2>/dev/null || true

# 2. Delete namespaces
echo "Deleting application namespaces..."
kubectl delete namespace dev staging production 2>/dev/null || true

# 3. Uninstall ArgoCD
echo "Uninstalling ArgoCD..."
kubectl delete namespace argocd 2>/dev/null || true

# 4. Stop port-forwards
echo "Stopping port-forwards..."
pkill -f "port-forward" 2>/dev/null || true

# 5. Delete cluster
echo "Deleting Kubernetes cluster..."
if command -v minikube &> /dev/null; then
    minikube delete 2>/dev/null || true
fi
if command -v kind &> /dev/null; then
    kind delete cluster --name gitops-lab 2>/dev/null || true
fi

# 6. Clean up files
echo "Cleaning up local files..."
rm -f ~/argocd-credentials.txt
rm -f /tmp/*-app.yaml
rm -f /tmp/argocd-values.yaml

echo "✅ Cleanup complete!"
echo "Verify with: kubectl get nodes (should fail if cluster deleted)"
```

Save as `scripts/cleanup-all.sh` and make executable:
```bash
chmod +x scripts/cleanup-all.sh
./scripts/cleanup-all.sh
```

## ⚠️ Things to Note

### Data Loss Warning

Deleting the cluster will remove **all data** including:
- All deployed applications
- Persistent volumes and data
- ConfigMaps and Secrets
- All Kubernetes resources

### Docker Images

Cleanup does not remove Docker images by default. To remove images:

```bash
# List images
docker images | grep -E "guestbook|redis|argocd"

# Remove specific images
docker rmi gcr.io/google-samples/gb-frontend:v4
docker rmi redis:6.2-alpine

# Or remove all unused images
docker image prune -a -f
```

### Git Repository

If you created a dedicated Git repository:
- Delete it from GitHub/GitLab
- Remove local clone
- Revoke personal access tokens if created

## 🔧 Troubleshooting Cleanup

### Namespace Stuck in "Terminating"

```bash
# Check what's blocking
kubectl get namespace dev -o json | jq '.status'

# Force delete (use with caution)
kubectl delete namespace dev --grace-period=0 --force

# Or remove finalizers
kubectl patch namespace dev -p '{"metadata":{"finalizers":[]}}' --type=merge
```

### ArgoCD Resources Not Deleting

```bash
# Remove finalizers from applications
kubectl patch application -n argocd guestbook-dev \
  -p '{"metadata":{"finalizers":null}}' --type=merge

# Then delete
kubectl delete application guestbook-dev -n argocd
```

### Port-Forward Won't Stop

```bash
# Find the process
ps aux | grep port-forward

# Kill by PID
kill -9 <PID>

# Or kill all
pkill -9 -f "port-forward"
```

## 🎓 Next Steps After Cleanup

After cleanup, you can:

1. **Start Fresh**: Redo the lab for practice
2. **Try Variations**: Experiment with different configurations
3. **Build Real Projects**: Apply GitOps to actual projects
4. **Explore Advanced Topics**: Multi-cluster, Argo Rollouts, etc.

## 📚 Additional Resources

- [Kubernetes Resource Deletion](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/)
- [Docker Cleanup Best Practices](https://docs.docker.com/config/pruning/)
- [ArgoCD Uninstallation](https://argo-cd.readthedocs.io/en/stable/operator-manual/installation/)

---

**Cleanup complete!** You can now start fresh or move on to new topics. 🚀
