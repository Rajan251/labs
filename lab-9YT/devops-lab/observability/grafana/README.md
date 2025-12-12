# Grafana Lab

## 1. Introduction
**Grafana** is the open-source analytics and monitoring solution for every database. It allows you to query, visualize, alert on, and understand your metrics no matter where they are stored.

## 2. Lab Setup

In this lab, we will deploy Grafana and configure it to connect to our Prometheus instance automatically.

### Prerequisites
*   A running Kubernetes cluster.
*   Prometheus deployed (from the previous lab) in the `monitoring` namespace.

### Step 1: Create Datasource Configuration
We want Grafana to auto-discover Prometheus. We do this via a ConfigMap.
```bash
kubectl apply -f grafana-datasource-config.yaml
```

### Step 2: Deploy Grafana
```bash
kubectl apply -f grafana-deployment.yaml
```

### Step 3: Expose Grafana
```bash
kubectl apply -f grafana-service.yaml
```

### Step 4: Access Grafana
```bash
kubectl port-forward -n monitoring svc/grafana 3000:3000
```
Open `http://localhost:3000`.
*   **User**: `admin`
*   **Password**: `admin`

## 3. Verification
1.  Login to Grafana.
2.  Go to **Configuration > Data Sources**.
3.  You should see `Prometheus` already configured.
4.  Click **Test**. It should say "Data source is working".
5.  Go to **Explore**, select **Prometheus**, and run a query like `up`.

## 4. Cleanup
```bash
kubectl delete -f grafana-service.yaml
kubectl delete -f grafana-deployment.yaml
kubectl delete -f grafana-datasource-config.yaml
```
