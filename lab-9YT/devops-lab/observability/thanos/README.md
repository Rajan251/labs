# Thanos Lab

## 1. Introduction
**Thanos** is a set of components that can be composed into a highly available metric system with unlimited storage capacity, which can be added seamlessly on top of existing Prometheus deployments.

### Key Features
*   **Global Query View**: Query across multiple Prometheus instances.
*   **Unlimited Retention**: Store metrics in object storage (S3, GCS, Azure, etc.).
*   **High Availability**: Deduplication of metrics from HA Prometheus pairs.

## 2. Architecture
*   **Sidecar**: Runs next to Prometheus, uploads data to object storage, and serves real-time data to Querier.
*   **Querier**: Aggregates data from Sidecars and Store Gateways.
*   **Store Gateway**: Serves historical data from object storage.
*   **Compactor**: Downsamples and compacts data in object storage.
*   **Ruler**: Evaluates recording and alerting rules on Thanos data.

## 3. Lab Setup

In this lab, we will simulate a "Long Term Storage" setup. We will deploy **MinIO** (S3-compatible storage) locally, then deploy Prometheus with the **Thanos Sidecar**, and finally the **Thanos Querier**.

### Prerequisites
*   A running Kubernetes cluster.
*   `kubectl` installed.

### Step 1: Create Namespace
```bash
kubectl create namespace monitoring
```

### Step 2: Deploy MinIO (Object Storage)
Thanos needs an object store. We'll use MinIO for this lab.
```bash
kubectl apply -f minio.yaml
```

### Step 3: Create Object Storage Configuration
Create a secret with the MinIO details for Thanos to use.
```bash
kubectl create secret generic thanos-objstore-config -n monitoring --from-file=thanos.yaml=thanos-storage-config.yaml
```

### Step 4: Deploy Prometheus with Thanos Sidecar
This deployment replaces the standard Prometheus. It includes the Thanos Sidecar container which uploads blocks to MinIO.
```bash
kubectl apply -f prometheus-with-sidecar.yaml
```

### Step 5: Deploy Thanos Querier
The Querier aggregates data.
```bash
kubectl apply -f thanos-querier.yaml
```

### Step 6: Deploy Thanos Store Gateway
To query historical data from MinIO.
```bash
kubectl apply -f thanos-store.yaml
```

## 4. Verification

1.  **Access Thanos Querier UI**:
    ```bash
    kubectl port-forward -n monitoring svc/thanos-querier 9091:9091
    ```
    Open `http://localhost:9091`.

2.  **Check Stores**:
    Go to **Stores** in the UI. You should see:
    *   The Sidecar (e.g., `prometheus-0:10901`)
    *   The Store Gateway (e.g., `thanos-store:10901`)

3.  **Query**:
    Execute `up`. You will see data coming from the Sidecar. Wait 2 hours (Prometheus block time) and data will appear in MinIO, accessible via the Store Gateway!

## 5. Cleanup
```bash
kubectl delete namespace monitoring
```
