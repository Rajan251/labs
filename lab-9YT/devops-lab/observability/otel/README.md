# OpenTelemetry Lab

## 1. Introduction
**OpenTelemetry (OTEL)** is a vendor-neutral observability framework for cloud-native software. It provides a set of APIs, libraries, agents, and collector services to capture distributed traces and metrics.

## 2. Lab Setup

In this lab, we will deploy the **OTEL Collector** to receive traces from an application and forward them to **Tempo**.

### Prerequisites
*   Kubernetes cluster.
*   Tempo deployed in `monitoring` namespace.

### Step 1: Deploy OTEL Collector
This collector is configured to:
1.  Receive data via OTLP (gRPC/HTTP).
2.  Process/Batch the data.
3.  Export traces to Tempo.
4.  Export debug info to logs.

```bash
kubectl apply -f otel-collector.yaml
```

### Step 2: Deploy Sample App (Trace Generator)
We will deploy a simple tool called `tracegen` that generates synthetic traces and sends them to our collector.
```bash
kubectl apply -f tracegen.yaml
```

## 3. Verification

1.  **Check Collector Logs**:
    ```bash
    kubectl logs -n monitoring -l app=otel-collector
    ```
    You should see logs indicating that traces are being exported.

2.  **View Traces in Grafana**:
    *   Open Grafana (`http://localhost:3000`).
    *   Go to **Explore**.
    *   Select **Tempo** datasource.
    *   Click **Search** (or run a query).
    *   You should see a list of recent traces. Click one to view the waterfall diagram.

## 4. Cleanup
```bash
kubectl delete -f tracegen.yaml
kubectl delete -f otel-collector.yaml
```
