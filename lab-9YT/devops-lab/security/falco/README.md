# Falco Lab

## 1. Introduction
**Falco** is the cloud-native runtime security project. It detects unexpected application behavior and alerts on threats at runtime.

## 2. Lab Setup

In this lab, we will install Falco and trigger a security alert.

### Prerequisites
*   Kubernetes cluster.
*   Helm installed.

### Step 1: Install Falco
```bash
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update
helm install falco falcosecurity/falco --namespace falco --create-namespace \
  --set tty=true
```

### Step 2: Trigger an Alert
Falco has a default rule that alerts when a shell is spawned in a container.
1.  Run a test pod:
    ```bash
    kubectl run alpine --image=alpine --restart=Never -- sh -c "sleep 600"
    ```
2.  Exec into it (this triggers the rule):
    ```bash
    kubectl exec -it alpine -- sh
    ```
3.  Exit:
    ```bash
    exit
    ```

### Step 3: Check Logs
```bash
kubectl logs -l app.kubernetes.io/name=falco -n falco
```
You should see a JSON log entry saying "Notice A shell was spawned in a container...".

## 3. Cleanup
```bash
kubectl delete pod alpine
helm uninstall falco -n falco
```
