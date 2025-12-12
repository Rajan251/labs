# Argo Lab (CD & Rollouts)

## 1. Introduction
**Argo CD** is a declarative, GitOps continuous delivery tool for Kubernetes.
**Argo Rollouts** is a Kubernetes controller and set of CRDs which provide advanced deployment capabilities such as blue-green, canary, canary analysis, experimentation, and progressive delivery features.

## 2. Lab Setup

### Prerequisites
*   Kubernetes cluster.
*   Helm.

### Part A: Argo CD (GitOps)

#### Step 1: Install Argo CD
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

#### Step 2: Access UI
1.  Get password:
    ```bash
    kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
    ```
2.  Port forward:
    ```bash
    kubectl port-forward svc/argocd-server -n argocd 8080:443
    ```
3.  Login at `https://localhost:8080` (User: `admin`).

#### Step 3: Deploy an App
Create an Application pointing to a public repo (e.g., guestbook).
```bash
kubectl apply -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/core-install.yaml
argocd app create guestbook --repo https://github.com/argoproj/argocd-example-apps.git --path guestbook --dest-server https://kubernetes.default.svc --dest-namespace default
argocd app sync guestbook
```

### Part B: Argo Rollouts (Blue/Green)

#### Step 1: Install Argo Rollouts
```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

#### Step 2: Install Kubectl Plugin
```bash
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x ./kubectl-argo-rollouts-linux-amd64
sudo mv ./kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
```

#### Step 3: Deploy a Rollout
```bash
kubectl apply -f rollout.yaml
```

#### Step 4: Watch the Rollout
```bash
kubectl argo rollouts get rollout rollouts-demo --watch
```
Update the image to trigger a rollout:
```bash
kubectl argo rollouts set image rollouts-demo rollouts-demo=argoproj/rollouts-demo:yellow
```

## 3. Cleanup
```bash
kubectl delete -f rollout.yaml
kubectl delete ns argo-rollouts
kubectl delete ns argocd
```
