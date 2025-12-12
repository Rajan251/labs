# External Secrets Operator (ESO) Lab

## 1. Introduction
**External Secrets Operator** integrates external secret management systems (AWS Secrets Manager, HashiCorp Vault, etc.) with Kubernetes. It reads secrets from the external API and injects them as Kubernetes Secrets.

## 2. Lab Setup

In this lab, we will use the **Fake** provider to simulate an external secret store, avoiding the need for real cloud credentials.

### Prerequisites
*   Kubernetes cluster.
*   Helm.

### Step 1: Install ESO
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm repo update
helm install external-secrets external-secrets/external-secrets \
    -n external-secrets \
    --create-namespace
```

### Step 2: Create a SecretStore
This tells ESO where to find the secrets. We use the `fake` provider.
```bash
kubectl apply -f secret-store.yaml
```

### Step 3: Create an ExternalSecret
This tells ESO *which* secret to fetch and what to name it in Kubernetes.
```bash
kubectl apply -f external-secret.yaml
```

### Step 4: Verify
Check if the Kubernetes Secret was created.
```bash
kubectl get secret my-k8s-secret
kubectl get secret my-k8s-secret -o jsonpath='{.data.username}' | base64 -d
```
You should see `admin`.

## 3. Cleanup
```bash
kubectl delete -f external-secret.yaml
kubectl delete -f secret-store.yaml
helm uninstall external-secrets -n external-secrets
```
