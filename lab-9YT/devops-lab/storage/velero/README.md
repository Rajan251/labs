# Velero Lab

## 1. Introduction
**Velero** is an open source tool to safely backup and restore, perform disaster recovery, and migrate Kubernetes cluster resources and persistent volumes.

## 2. Lab Setup

In this lab, we will install Velero and use MinIO as the backup target.

### Prerequisites
*   Kubernetes cluster.
*   MinIO deployed (from Thanos lab) or a new instance.
*   `velero` CLI installed.

### Step 1: Install Velero
We will install Velero using the CLI, pointing it to our local MinIO.

1.  Create a credentials file `credentials-velero`:
    ```
    [default]
    aws_access_key_id = minio
    aws_secret_access_key = minio123
    ```

2.  Install:
    ```bash
    velero install \
      --provider aws \
      --plugins velero/velero-plugin-for-aws:v1.6.0 \
      --bucket velero \
      --secret-file ./credentials-velero \
      --use-node-agent \
      --use-volume-snapshots=false \
      --backup-location-config region=minio,s3ForcePathStyle="true",s3Url=http://minio.monitoring.svc:9000
    ```

### Step 2: Create a Backup
1.  Deploy a sample app:
    ```bash
    kubectl create ns demo
    kubectl create deployment nginx --image=nginx -n demo
    ```
2.  Backup the namespace:
    ```bash
    velero backup create demo-backup --include-namespaces demo
    ```
3.  Check status:
    ```bash
    velero backup describe demo-backup
    ```

### Step 3: Disaster!
Delete the namespace.
```bash
kubectl delete ns demo
```

### Step 4: Restore
```bash
velero restore create --from-backup demo-backup
```
Check if the namespace and pod are back:
```bash
kubectl get pods -n demo
```

## 3. Cleanup
```bash
velero uninstall
kubectl delete ns demo
```
