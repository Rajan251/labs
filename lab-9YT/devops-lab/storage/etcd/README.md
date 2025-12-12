# etcd Lab

## 1. Introduction
**etcd** is a strongly consistent, distributed key-value store that provides a reliable way to store data that needs to be accessed by a distributed system or cluster of machines. It is the brain of Kubernetes.

## 2. Lab Setup

In this lab, we will learn how to interact with etcd running in a Kubernetes cluster (specifically `kind` or `minikube`) and perform a backup.

### Prerequisites
*   A running Kubernetes cluster (Kind recommended).

### Step 1: Accessing etcd
In a Kind cluster, etcd runs as a pod in the `kube-system` namespace, but it's best accessed directly from the control-plane node.

1.  **Exec into the control plane node**:
    ```bash
    docker exec -it kind-control-plane bash
    ```

2.  **Set environment variables**:
    Etcd uses mTLS. We need to tell `etcdctl` where the certs are.
    ```bash
    export ETCDCTL_API=3
    export ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt
    export ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt
    export ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key
    ```

### Step 2: Check Health
```bash
etcdctl endpoint health
```
You should see `healthy: successfully committed proposal: took = ...`

### Step 3: List Keys
See what Kubernetes has stored.
```bash
etcdctl get / --prefix --keys-only | head
```

### Step 4: Backup etcd (Critical Skill)
This is a common task for CKA exams and disaster recovery.
```bash
etcdctl snapshot save /tmp/etcd-backup.db
```
Verify the snapshot:
```bash
etcdctl snapshot status /tmp/etcd-backup.db
```

### Step 5: Restore (Theory)
To restore, you would stop the API server and run:
```bash
etcdctl snapshot restore /tmp/etcd-backup.db --data-dir /var/lib/etcd-restore
```
*Note: Don't run this in a live lab unless you want to break the cluster!*

## 3. Cleanup
Exit the container:
```bash
exit
```
