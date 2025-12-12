# Tempo Lab

## 1. Introduction
**Grafana Tempo** is an open source, easy-to-use, and high-scale distributed tracing backend. It is designed to be cost-effective, requiring only object storage to operate.

## 2. Lab Setup

In this lab, we will deploy Tempo in "monolithic" mode (all components in one pod) and configure it to use MinIO for storage.

### Prerequisites
*   Kubernetes cluster.
*   MinIO deployed in `monitoring` namespace (from Thanos lab).

### Step 1: Deploy Tempo
This manifest includes the ConfigMap, Deployment, and Service.
```bash
kubectl apply -f tempo.yaml
```

### Step 2: Configure Grafana
Now we need to tell Grafana about Tempo.
1.  Go to Grafana (`http://localhost:3000`).
2.  **Configuration > Data Sources > Add data source**.
3.  Select **Tempo**.
4.  **URL**: `http://tempo.monitoring.svc.cluster.local:3200`
5.  **Save & Test**.

## 3. Verification
We need traces to verify. In the next lab (**OpenTelemetry**), we will deploy a collector and an app to send traces here.
For now, verify the pod is running:
```bash
kubectl get pods -n monitoring -l app=tempo
```

## 4. Cleanup
```bash
kubectl delete -f tempo.yaml
```
