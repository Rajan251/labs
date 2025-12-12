# Kasten K10 Lab

## 1. Introduction
**Kasten K10** by Veeam is a purpose-built data management platform for Kubernetes. It provides enterprise-grade backup/restore, disaster recovery, and mobility.

## 2. Lab Setup

In this lab, we will install the free edition of Kasten K10.

### Prerequisites
*   Kubernetes cluster.
*   Helm.

### Step 1: Install Kasten K10
```bash
helm repo add kasten https://charts.kasten.io/
helm repo update
kubectl create namespace kasten-io
helm install k10 kasten/k10 --namespace=kasten-io
```

### Step 2: Access Dashboard
1.  Port forward:
    ```bash
    kubectl --namespace kasten-io port-forward service/gateway 8080:8000
    ```
2.  Open `http://localhost:8080/k10/`.

### Step 3: Configure Backup Policy
1.  In the UI, create a "Profile" pointing to an S3 bucket (you can use MinIO).
2.  Create a "Policy" to backup a namespace (e.g., `default`) every hour.
3.  Click "Run Once" to trigger a backup.

## 3. Cleanup
```bash
helm uninstall k10 -n kasten-io
kubectl delete ns kasten-io
```
