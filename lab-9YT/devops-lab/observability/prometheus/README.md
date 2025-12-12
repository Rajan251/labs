# Prometheus Lab

## 1. Introduction
**Prometheus** is an open-source systems monitoring and alerting toolkit originally built at SoundCloud. It is now a standalone open source project and maintained independently of any company.

### Key Features
*   **Multi-dimensional data model**: Time series data identified by metric name and key/value pairs.
*   **PromQL**: A flexible query language to leverage this dimensionality.
*   **Pull model**: Prometheus scrapes metrics from instrumented jobs (it pulls data, rather than data being pushed to it).
*   **Service Discovery**: Targets are discovered via service discovery or static configuration.

## 2. Architecture
*   **Prometheus Server**: Scrapes and stores time series data.
*   **Client Libraries**: For instrumenting application code.
*   **Pushgateway**: For supporting short-lived jobs.
*   **Exporters**: For exporting metrics from third-party systems (e.g., Node Exporter, MySQL Exporter).
*   **Alertmanager**: Handling alerts.

## 3. Lab Setup

In this lab, we will deploy a Prometheus server into a Kubernetes cluster and configure it to scrape metrics from itself.

### Prerequisites
*   A running Kubernetes cluster (Kind/Minikube).
*   `kubectl` installed.

### Step 1: Create the Namespace
```bash
kubectl create namespace monitoring
```

### Step 2: Deploy Prometheus Components
We will use raw Kubernetes manifests to understand the components.

1.  **RBAC**: Create the necessary permissions for Prometheus to access the Kubernetes API (to discover pods/nodes).
    ```bash
    kubectl apply -f prometheus-rbac.yaml
    ```

2.  **ConfigMap**: Define the `prometheus.yml` configuration file.
    ```bash
    kubectl apply -f prometheus-config.yaml
    ```

3.  **Deployment**: Deploy the Prometheus server.
    ```bash
    kubectl apply -f prometheus-deployment.yaml
    ```

4.  **Service**: Expose Prometheus.
    ```bash
    kubectl apply -f prometheus-service.yaml
    ```

### Step 3: Access the UI
Forward the port to your local machine:
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```
Open your browser to `http://localhost:9090`.

## 4. Verification
1.  Go to **Status > Targets** in the Prometheus UI. You should see `prometheus` as UP.
2.  Go to **Graph** and enter a query:
    ```promql
    up
    ```
    Click **Execute**. You should see a value of `1` for the prometheus instance.

## 5. Cleanup
```bash
kubectl delete namespace monitoring
```
