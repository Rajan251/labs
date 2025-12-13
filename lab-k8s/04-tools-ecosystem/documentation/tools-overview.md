# Tools Ecosystem Overview

Kubernetes is supported by a vast ecosystem of tools (CNCF Landscape).

## 1. Package Management: Helm
Helm is the "apt/yum" for Kubernetes.
- **Chart**: A package of pre-configured Kubernetes resources.
- **Release**: A specific instance of a chart running in the cluster.
- **Values**: Configuration parameters to customize the chart.

## 2. GitOps: ArgoCD
Declarative continuous delivery.
- **Single Source of Truth**: Git repository contains the desired state.
- **Controller**: ArgoCD syncs the cluster state to match Git.
- **Self-Healing**: Automatically corrects drift.

## 3. Observability
- **Prometheus**: Time-series database for metrics. Pull-based model.
- **Grafana**: Dashboarding and visualization.
- **Fluentd**: Unified logging layer.
- **Jaeger/Zipkin**: Distributed tracing.

## 4. Service Mesh: Istio
Manage traffic, security, and observability without changing code.
- **Traffic Splitting**: Canary deployments (90% v1, 10% v2).
- **mTLS**: Automatic encryption between services.
