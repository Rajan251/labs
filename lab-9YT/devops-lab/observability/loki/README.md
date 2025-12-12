# Loki Lab

## 1. Introduction
**Loki** is a horizontally scalable, highly available, multi-tenant log aggregation system inspired by Prometheus. It is designed to be very cost-effective and easy to operate. It does not index the contents of the logs, but rather a set of labels for each log stream.

## 2. Lab Setup

In this lab, we will deploy Loki (Monolithic mode) and configure **Fluent Bit** to collect logs from all pods and send them to Loki.

### Prerequisites
*   Kubernetes cluster.
*   MinIO deployed in `monitoring` namespace (optional, we will use filesystem for simplicity here, or MinIO if you prefer). *For this lab, we will use local filesystem to keep it lightweight.*

### Step 1: Deploy Loki
```bash
kubectl apply -f loki.yaml
```

### Step 2: Deploy Fluent Bit (Log Collector)
Fluent Bit runs as a DaemonSet (one per node) to read logs from `/var/log/containers`.
```bash
kubectl apply -f fluent-bit.yaml
```

### Step 3: Configure Grafana
1.  Go to Grafana (`http://localhost:3000`).
2.  **Configuration > Data Sources > Add data source**.
3.  Select **Loki**.
4.  **URL**: `http://loki.monitoring.svc.cluster.local:3100`
5.  **Save & Test**.

## 3. Verification
1.  **Explore Logs**:
    *   Go to **Explore** in Grafana.
    *   Select **Loki** datasource.
    *   Select a label filter, e.g., `{namespace="monitoring"}`.
    *   You should see logs streaming in.

2.  **Correlate with Metrics**:
    *   Split the view.
    *   Left: Prometheus (`up`).
    *   Right: Loki (`{app="prometheus"}`).
    *   See how metrics and logs align.

## 4. Cleanup
```bash
kubectl delete -f fluent-bit.yaml
kubectl delete -f loki.yaml
```
