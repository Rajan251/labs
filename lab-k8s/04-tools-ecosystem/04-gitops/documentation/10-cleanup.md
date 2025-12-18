# Cleanup Guide

## Overview

This guide covers how to properly clean up all resources created during the GitOps lab.

## Quick Cleanup

### Using the Cleanup Script

The easiest way to clean up is using the provided script:

```bash
cd /home/rk/Documents/labs/lab-k8s/04-tools-ecosystem/04-gitops

# Make script executable (if not already)
chmod +x scripts/cleanup.sh

# Run cleanup
./scripts/cleanup.sh
```

The script will:
1. Delete all ArgoCD applications
2. Remove application namespaces (guestbook-dev, guestbook-staging, guestbook-prod, wordpress)
3. Optionally remove ArgoCD
4. Optionally delete the Kubernetes cluster
5. Clean up temporary files

## Manual Cleanup

### Step 1: Delete ArgoCD Applications

```bash
# List all applications
argocd app list

# Delete specific application
argocd app delete guestbook-dev
argocd app delete guestbook-staging
argocd app delete guestbook-prod

# Or delete all applications
kubectl delete applications --all -n argocd
```

### Step 2: Delete Application Namespaces

```bash
# Delete guestbook namespaces
kubectl delete namespace guestbook-dev
kubectl delete namespace guestbook-staging
kubectl delete namespace guestbook-prod

# Delete wordpress namespace (if created)
kubectl delete namespace wordpress

# Verify deletion
kubectl get namespaces | grep guestbook
```

### Step 3: Delete ArgoCD (Optional)

```bash
# If installed via Helm
helm uninstall argocd -n argocd

# Delete ArgoCD namespace
kubectl delete namespace argocd

# Verify deletion
kubectl get namespace argocd
# Should return: Error from server (NotFound)
```

### Step 4: Delete Kubernetes Cluster (Optional)

#### For Minikube:
```bash
# List clusters
minikube profile list

# Delete specific cluster
minikube delete --profile gitops-lab

# Or delete all clusters
minikube delete --all
```

#### For Kind:
```bash
# List clusters
kind get clusters

# Delete specific cluster
kind delete cluster --name gitops-lab
```

#### For K3d:
```bash
# List clusters
k3d cluster list

# Delete specific cluster
k3d cluster delete gitops-lab
```

### Step 5: Clean Up Docker Images (Optional)

```bash
# List Docker images
docker images | grep guestbook

# Remove specific image
docker rmi <image-id>

# Prune unused images
docker image prune -a

# Clean up build cache
docker builder prune
```

### Step: 6: Clean Up Temporary Files

```bash
# Remove ArgoCD credentials file
rm -f /tmp/argocd-credentials.txt

# Remove Kind config (if exists)
rm -f /tmp/kind-config.yaml

# Remove any kubectl port-forward PIDs
pkill -f "kubectl port-forward"
```

## Verification

### Verify Applications Removed

```bash
# Check ArgoCD applications
kubectl get applications -n argocd
# Should return: No resources found or error

# Check application pods
kubectl get pods --all-namespaces | grep guestbook
# Should return nothing
```

### Verify Namespaces Removed

```bash
# List all namespaces
kubectl get namespaces

# Should NOT see:
# - guestbook-dev
# - guestbook-staging
# - guestbook-prod
# - wordpress
```

### Verify ArgoCD Removed

```bash
# Check ArgoCD namespace
kubectl get namespace argocd
# Should return: Error from server (NotFound)

# Check ArgoCD pods
kubectl get pods -n argocd
# Should return error or nothing
```

### Verify Cluster Status

```bash
# Check current context
kubectl config current-context

# If cluster deleted, this should fail:
kubectl get nodes
```

## Partial Cleanup Scenarios

### Keep ArgoCD, Remove Applications

```bash
# Delete applications only
kubectl delete applications --all -n argocd

# Delete application namespaces
kubectl delete namespace guestbook-dev guestbook-staging guestbook-prod

# ArgoCD remains for future use
```

### Keep Cluster, Remove All GitOps Resources

```bash
# Delete ArgoCD applications
kubectl delete applications --all -n argocd

# Delete application namespaces
kubectl delete namespace guestbook-dev guestbook-staging guestbook-prod

# Delete ArgoCD
kubectl delete namespace argocd

# Cluster remains running
```

## Troubleshooting Cleanup

### Application Won't Delete

```bash
# Force delete ArgoCD application
kubectl patch application <app-name> -n argocd \
  -p '{"metadata":{"finalizers":[]}}' --type=merge
  
kubectl delete application <app-name> -n argocd --force --grace-period=0
```

### Namespace Stuck in Terminating

```bash
# Get namespace details
kubectl get namespace <namespace> -o json > /tmp/ns.json

# Remove finalizers
cat /tmp/ns.json | jq '.spec.finalizers = []' > /tmp/ns-fixed.json

# Apply the fix
kubectl replace --raw "/api/v1/namespaces/<namespace>/finalize" \
  -f /tmp/ns-fixed.json
```

### Port Forward Still Running

```bash
# Find port-forward processes
ps aux | grep "kubectl port-forward"

# Kill specific process
kill <PID>

# Kill all kubectl port-forwards
pkill -f "kubectl port-forward"
```

### Docker Containers Still Running

```bash
# List running containers
docker ps | grep k8s

# Stop all containers
docker stop $(docker ps -aq)

# Remove all containers
docker rm $(docker ps -aq)
```

## Reset to Fresh State

If you want to start completely fresh:

```bash
# 1. Run full cleanup
./scripts/cleanup.sh
# Answer 'y' to all prompts

# 2. Verify everything is clean
docker ps -a
kubectl config get-contexts
minikube profile list  # or kind get clusters, or k3d cluster list

# 3. Remove kubectl context (optional)
kubectl config delete-context <context-name>

# 4. Start fresh setup
./scripts/setup-cluster.sh
./scripts/install-argocd.sh
```

## Cleanup Checklist

Before considering cleanup complete, verify:

- [ ] All ArgoCD applications deleted
- [ ] Application namespaces removed (guestbook-*, wordpress)
- [ ] ArgoCD namespace removed (if intended)
- [ ] No port-forward processes running
- [ ] Kubernetes cluster deleted (if intended)
- [ ] Temporary files cleaned up
- [ ] Docker images pruned (if intended)
- [ ] kubectl context removed (if cluster deleted)

## Re-Setup After Cleanup

To set up the lab again after cleanup:

```bash
# 1. Setup cluster
./scripts/setup-cluster.sh

# 2. Install ArgoCD
./scripts/install-argocd.sh

# 3. Deploy applications
kubectl apply -f examples/argocd-apps/guestbook-dev.yaml
```

## Next Steps

After cleanup:
- Try different cluster types (Minikube → Kind → K3d)
- Experiment with different configurations
- Practice the labs again with variations
- Set up on a different machine

## Support

If you encounter issues during cleanup:

1. Check logs: `kubectl logs -n argocd <pod-name>`
2. Review events: `kubectl get events --all-namespaces`
3. Consult [Troubleshooting Guide](09-troubleshooting.md)
4. Force delete if necessary (see troubleshooting section above)

---

**Remember**: Always verify cleanup completion before starting fresh!
