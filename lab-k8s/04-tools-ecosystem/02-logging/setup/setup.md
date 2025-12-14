# Logging Stack Setup Guide

This guide details how to set up the EFK (Elasticsearch, Fluentd, Kibana) stack on Kubernetes.

## Prerequisites
- Helm installed
- Kubernetes cluster running

## 1. Add Helm Repositories

```bash
helm repo add elastic https://helm.elastic.co
helm repo add fluent https://fluent.github.io/helm-charts
helm repo update
```

## 2. Install Elasticsearch

```bash
helm install elasticsearch elastic/elasticsearch \
  --namespace logging \
  --create-namespace \
  -f elasticsearch-values.yaml
```

## 3. Install Kibana

```bash
helm install kibana elastic/kibana \
  --namespace logging
```

## 4. Install Fluentd

```bash
helm install fluentd fluent/fluentd \
  --namespace logging \
  -f fluentd-values.yaml
```

## 5. Access Kibana

Port-forward to access the Kibana dashboard:

```bash
kubectl port-forward --namespace logging service/kibana-kibana 5601:5601
```

Open `http://localhost:5601` in your browser.
