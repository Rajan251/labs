# Exercise 01: First GitOps Deployment

## 🎯 Objective

Deploy your first application using GitOps principles with ArgoCD. You'll learn how to:
- Create an ArgoCD Application manifest
- Deploy an application via GitOps
- Verify deployment status
- Make changes via Git
- Watch auto-sync in action

**Duration**: 30 minutes  
**Difficulty**: Beginner

## 📋 Prerequisites

- Kubernetes cluster running (Minikube or Kind)
- ArgoCD installed and accessible
- ArgoCD CLI installed (optional but recommended)

Verify:
```bash
kubectl get nodes
kubectl get pods -n argocd
argocd version
```

## 🚀 Exercise Steps

### Step 1: Fork the GitOps Repository

Since you can't modify the example repository directly, you'll work with the local guestbook configuration.

```bash
# Navigate to the gitops repo
cd /home/rk/Documents/labs/lab-k8s/07-gitops/gitops-repo

# Verify the structure
ls -la apps/guestbook/
```

### Step 2: Create a Simple nginx Application

Let's start with a simple nginx deployment before using the full guestbook.

```bash
# Create a directory for nginx app
mkdir -p apps/nginx/base
cd apps/nginx/base
```

Create `deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.21-alpine
        ports:
        - name: http
          containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

Create `service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: http
  selector:
    app: nginx
```

Create `kustomization.yaml`:
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
```

### Step 3: Create ArgoCD Application Manifest

For this exercise, we'll deploy directly from the local file system (you can later use Git).

Create this file at `/tmp/nginx-app.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nginx-demo
  namespace: argocd
spec:
  project: default
  
  # Source - using the ArgoCD example apps for now
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: HEAD
    path: guestbook
  
  # Destination
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  
  # Sync policy - auto-sync enabled
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### Step 4: Deploy the Application

**Via kubectl:**

```bash
# Apply the Application manifest
kubectl apply -f /tmp/nginx-app.yaml

# Verify Application was created
kubectl get application -n argocd
```

**Via ArgoCD CLI:**

```bash
# Alternative: Create app via CLI
argocd app create nginx-demo \
  --repo https://github.com/argoproj/argocd-example-apps.git \
  --path guestbook \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default \
  --sync-policy automated \
  --auto-prune \
  --self-heal

# Sync the application
argocd app sync nginx-demo
```

### Step 5: Verify Deployment

**Check Application Status:**

```bash
# Via CLI
argocd app get nginx-demo

# Via kubectl
kubectl get application nginx-demo -n argocd
```

**Check Deployed Resources:**

```bash
# List all resources created
kubectl get all -n default

# Expected output should show:
# - deployment.apps/guestbook-ui
# - service/guestbook-ui
# - pods running
```

**View in ArgoCD UI:**

```bash
# Ensure port-forward is running
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Open https://localhost:8080
# Navigate to Applications → nginx-demo
```

You should see:
- ✅ Status: Synced
- ✅ Health: Healthy
- 🌳 Resource tree showing all deployed resources

### Step 6: Make Your First GitOps Change

Unfortunately, we can't modify the example repository. Let's simulate what would happen:

**Scenario**: Scale the application from 1 to 3 replicas

**Traditional Way** (DON'T do this - just for comparison):
```bash
kubectl scale deployment guestbook-ui -n default --replicas=3
# This would work, but is NOT GitOps!
```

**GitOps Way** (if you owned the repo):
1. Fork the repository
2. Clone it locally
3. Edit `guestbook/guestbook-ui-deployment.yaml`
4. Change `replicas: 1` to `replicas: 3`
5. Commit and push
6. Wait for ArgoCD to auto-sync (3 minutes) or manually sync

### Step 7: Test Auto-Sync

Let's test ArgoCD's ability to detect and revert manual changes (drift detection).

**Make a manual change:**

```bash
# Manually scale the deployment
kubectl scale deployment guestbook-ui -n default --replicas=5

# Check current state
kubectl get deployment guestbook-ui -n default
# Shows 5 replicas

# Watch what happens (ArgoCD will revert this in ~3 minutes)
watch kubectl get deployment guestbook-ui -n default
```

**What you should observe:**

1. **OutOfSync Status**: ArgoCD UI shows application is OutOfSync
2. **Self-Heal**: Within 3 minutes, ArgoCD automatically reverts to 1 replica (from Git)
3. **Synced Again**: Application returns to Synced status

This is **continuous reconciliation** in action!

### Step 8: View Application History

```bash
# View sync history
argocd app history nginx-demo

# Output shows:
# ID  DATE                           REVISION
# 1   2024-12-15 10:30:00 +0000 UTC  HEAD (abc123)
# 2   2024-12-15 10:35:00 +0000 UTC  HEAD (abc123)  # Self-heal sync
```

### Step 9: Access the Application

```bash
# Port-forward to access the guestbook UI
kubectl port-forward svc/guestbook-ui -n default 8081:80 &

# Open browser to:
# http://localhost:8081

# You should see the Guestbook application!
```

### Step 10: Clean Up

```bash
# Delete the application
argocd app delete nginx-demo

# Or via kubectl
kubectl delete application nginx-demo -n argocd

# Verify resources are removed
kubectl get all -n default
```

## ✅ Verification Checklist

- [ ] ArgoCD Application created successfully
- [ ] Application status shows "Synced" and "Healthy"
- [ ] Resources deployed in the cluster
- [ ] Accessed application in browser
- [ ] Observed auto-sync (drift detection and self-heal)
- [ ] Viewed application history
- [ ] Successfully cleaned up resources

## 🎓 What You Learned

✅ **GitOps Workflow**: How applications are deployed via Git  
✅ **ArgoCD Application**: Structure and purpose  
✅ **Sync Policies**: Auto-sync, prune, self-heal  
✅ **Drift Detection**: How ArgoCD detects and reverts manual changes  
✅ **Continuous Reconciliation**: Automatic state management  

## 💡 Key Takeaways

1. **Git is the Source of Truth**: All changes should go through Git
2. **Auto-Sync**: ArgoCD automatically deploys changes from Git
3. **Self-Heal**: Manual cluster changes are automatically reverted
4. **Declarative**: You declare desired state, ArgoCD ensures it
5. **Audit Trail**: All changes tracked in Git history

## 🚀 Next Steps

- **Exercise 02**: [Environment Promotion](../02-environment-promotion/) - Deploy to dev/staging/prod
- **Explore**: Try modifying other application properties
- **Read**: [GitOps Concepts](../../concepts/README.md) for deeper understanding

## 📚 Additional Resources

- [ArgoCD Core Concepts](https://argo-cd.readthedocs.io/en/stable/core_concepts/)
- [Application CRD](https://argo-cd.readthedocs.io/en/stable/operator-manual/application.yaml)
- [Sync Options](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/)

---

**Congratulations!** 🎉 You've completed your first GitOps deployment! You now understand the foundational workflow of GitOps with ArgoCD.
