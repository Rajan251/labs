# Kyverno Lab

## 1. Introduction
**Kyverno** is a policy engine designed for Kubernetes. It allows you to validate, mutate, and generate Kubernetes resources using policies defined as Kubernetes resources.

## 2. Lab Setup

In this lab, we will enforce a policy that requires all pods to have a `app` label.

### Prerequisites
*   Kubernetes cluster.
*   Helm.

### Step 1: Install Kyverno
```bash
helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update
helm install kyverno kyverno/kyverno -n kyverno --create-namespace
```

### Step 2: Apply Policy
```bash
kubectl apply -f require-labels.yaml
```

### Step 3: Test Policy
1.  **Try to create a pod without the label** (Should fail):
    ```bash
    kubectl run no-label --image=nginx
    ```
    *Expected Output*: `Error from server: admission webhook "validate.kyverno.svc-fail" denied the request...`

2.  **Create a pod WITH the label** (Should succeed):
    ```bash
    kubectl run with-label --image=nginx --labels=app=nginx
    ```
    *Expected Output*: `pod/with-label created`

## 3. Cleanup
```bash
kubectl delete pod with-label
kubectl delete -f require-labels.yaml
helm uninstall kyverno -n kyverno
```
