# Monitoring Stack Setup Guide

This guide details how to set up a comprehensive monitoring stack using Prometheus and Grafana on Kubernetes.

## Prerequisites
- Helm installed
- Kubernetes cluster running

## 1. Add Helm Repositories

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

## 2. Install Prometheus

We will use the official Prometheus chart with our custom configuration.

```bash
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --create-namespace \
  -f prometheus-values.yaml
```

## 3. Install Grafana

Install Grafana with pre-configured data sources and dashboards.

```bash
helm install grafana grafana/grafana \
  --namespace monitoring \
  -f grafana-values.yaml
```

## 4. Access Dashboards

Get the Grafana admin password (if not set in values):

```bash
kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
```

Port-forward to access the UI:

```bash
kubectl port-forward --namespace monitoring service/grafana 3000:80
```

Open `http://localhost:3000` in your browser.
