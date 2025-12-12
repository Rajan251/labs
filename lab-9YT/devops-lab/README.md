# Ultimate DevOps Lab Environment

Welcome to the comprehensive DevOps Lab. This repository contains hands-on labs for a wide range of industry-standard tools used in Modern DevOps, SRE, and Platform Engineering.

## 🛠 Prerequisites

To successfully run these labs, you will need the following installed on your local machine:

1.  **Docker**: Container runtime.
2.  **Kubernetes Cluster**:
    *   **Kind** (Kubernetes in Docker) - Recommended for local labs.
    *   *Or* **Minikube**.
3.  **CLI Tools**:
    *   `kubectl`: Kubernetes command-line tool.
    *   `helm`: Package manager for Kubernetes.
    *   `docker`: Docker CLI.

## 📂 Lab Structure

The labs are organized by domain:

### 1. Observability (`/observability`)
*   **Prometheus**: Metrics collection and alerting.
*   **Thanos**: High availability and long-term storage for Prometheus.
*   **Grafana**: Visualization and dashboards.
*   **OpenTelemetry**: Vendor-neutral observability data collection.
*   **Loki**: Log aggregation system.
*   **Tempo**: Distributed tracing.
*   **Pyroscope**: Continuous profiling.

### 2. Security & Governance (`/security`)
*   **Falco**: Cloud-native runtime security.
*   **Trivy**: Vulnerability scanner.
*   **Kyverno / OPA**: Policy engines for Kubernetes.
*   **External Secrets**: Managing secrets in K8s.

### 3. Networking (`/networking`)
*   **Cilium**: eBPF-based networking, security, and observability.
*   **Istio**: Service Mesh.

### 4. CI/CD & GitOps (`/cicd`)
*   **Argo CD & Rollouts**: GitOps continuous delivery and progressive delivery.
*   **Jenkins**: Automation server.
*   **GitHub Actions**: CI/CD workflows.
*   **Crossplane**: Cloud control plane.

### 5. Storage & Backup (`/storage`)
*   **Velero**: Backup and disaster recovery.
*   **etcd**: Distributed key-value store.

### 6. Infrastructure as Code (`/iac`)
*   **Terraform**: Infrastructure provisioning.

## 🚀 Getting Started

Navigate to any directory to find a dedicated `README.md` with specific instructions for that tool.

Example:
```bash
cd observability/prometheus
cat README.md
```
