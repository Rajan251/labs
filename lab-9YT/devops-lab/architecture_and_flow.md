# DevOps Lab System Architecture & Flow Design

This document details the architectural design and operational flows of the comprehensive DevOps environment we have built. It connects the individual tools into a cohesive platform.

## 1. High-Level Architecture

The platform is built on top of **Kubernetes** and is divided into logical layers.

```mermaid
graph TD
    subgraph "User / Developer"
        Dev[Developer]
        Ops[DevOps Engineer]
    end

    subgraph "CI/CD Layer"
        Git[GitHub]
        Jenkins[Jenkins CI]
        Argo[Argo CD]
        Registry[Container Registry]
    end

    subgraph "Kubernetes Cluster"
        subgraph "Ingress & Networking"
            Cilium[Cilium CNI]
            Istio[Istio Ingress / Mesh]
        end

        subgraph "Application Layer"
            App[Microservices]
            Sidecar[Envoy Sidecar]
        end

        subgraph "Observability Layer"
            Prom[Prometheus]
            Thanos[Thanos Sidecar]
            Loki[Loki]
            Tempo[Tempo]
            Otel[OTEL Collector]
            Pyro[Pyroscope]
        end

        subgraph "Security & Governance"
            Falco[Falco]
            Kyverno[Kyverno]
            ESO[External Secrets]
        end
        
        subgraph "Storage & Backup"
            MinIO[MinIO (S3)]
            Velero[Velero]
        end
    end

    subgraph "Visualization"
        Grafana[Grafana]
        Kiali[Kiali]
    end

    %% Flows
    Dev -->|Push Code| Git
    Git -->|Webhook| Jenkins
    Jenkins -->|Build & Push| Registry
    Argo -->|Watch| Git
    Argo -->|Sync| App
    
    App -->|Metrics| Prom
    Prom -->|Blocks| MinIO
    App -->|Logs| Loki
    App -->|Traces| Otel
    Otel -->|Traces| Tempo
    Tempo -->|Blocks| MinIO
    
    Grafana -->|Query| Prom
    Grafana -->|Query| Loki
    Grafana -->|Query| Tempo
    Grafana -->|Query| Pyro
```

## 2. Detailed Operational Flows

### A. The "Life of a Request" (Observability Flow)
When a user sends a request to an application running in this cluster, the following observability data is generated and processed:

1.  **Ingress**: The request hits **Istio Ingress Gateway**.
    *   *Metric*: Request count, latency.
    *   *Trace*: A trace ID is generated (B3/W3C headers).
2.  **Service Mesh**: The request travels through the **Cilium** CNI and **Envoy** sidecars.
    *   *Security*: **Falco** monitors the syscalls to ensure no malicious activity.
    *   *Policy*: **Kyverno** ensures the pod has the right labels and security context.
3.  **Application Processing**:
    *   **Logs**: The app writes logs to `stdout`. **Fluent Bit** (DaemonSet) tails these logs, enriches them with K8s metadata, and pushes them to **Loki**.
    *   **Metrics**: The app exposes a `/metrics` endpoint. **Prometheus** scrapes this every 15s. **Thanos Sidecar** uploads old blocks to **MinIO** for long-term storage.
    *   **Traces**: The app sends trace spans to the **OTEL Collector**, which batches them and sends them to **Tempo**.
    *   **Profiling**: The **Pyroscope** agent captures CPU profiles and sends them to the **Pyroscope Server**.
4.  **Visualization**:
    *   An engineer opens **Grafana**.
    *   They see a spike in latency on the **Dashboard** (Prometheus).
    *   They click the spike to see the **Trace** (Tempo).
    *   They look at the **Logs** for that specific trace ID (Loki).
    *   They check the **Flamegraph** to see which function was slow (Pyroscope).

### B. The CI/CD Pipeline Flow
How code gets from a developer's laptop to production.

1.  **Commit**: Developer pushes code to **GitHub**.
2.  **CI Trigger**: **GitHub Actions** or **Jenkins** detects the change.
    *   **Scan**: **Trivy** scans the filesystem and dependencies for vulnerabilities.
    *   **Build**: Docker image is built.
    *   **Image Scan**: **Trivy** scans the built image.
    *   **Push**: Image is pushed to the Registry.
3.  **GitOps Update**: The CI pipeline updates the Kubernetes manifest repo (e.g., `values.yaml`) with the new image tag.
4.  **Deployment**:
    *   **Argo CD** detects the drift in the manifest repo.
    *   **Argo Rollouts** starts a Blue/Green or Canary deployment.
    *   **Analysis**: Argo checks **Prometheus** metrics (e.g., error rate). If low, it promotes the rollout.
5.  **Configuration**:
    *   **External Secrets Operator** fetches the DB password from the external store and injects it as a K8s Secret.

### C. Disaster Recovery Flow
What happens when things go wrong.

1.  **Backup**: **Velero** (or **Kasten K10**) runs a scheduled backup.
    *   It takes a snapshot of **etcd** (cluster state).
    *   It takes volume snapshots of Persistent Volumes.
    *   It uploads the tarball to **MinIO**.
2.  **Failure**: A namespace is accidentally deleted.
3.  **Restore**:
    *   Admin runs `velero restore`.
    *   Velero pulls data from MinIO.
    *   Resources and PVs are recreated.

## 3. Component Deep Dive

### Observability Stack ("LGTM" + P)
*   **L**oki: Logs. Like `grep` for your cluster.
*   **G**rafana: The single pane of glass.
*   **T**empo: Traces. Finding the needle in the haystack.
*   **M**etrics (Prometheus/Thanos): The heartbeat.
*   **P**yroscope: Performance profiling.

### Security Layers
1.  **Static (Build Time)**: Trivy scans code and images.
2.  **Admission (Deploy Time)**: Kyverno blocks insecure pods (e.g., running as root).
3.  **Runtime (Run Time)**: Falco watches the kernel for suspicious behavior (e.g., shell in container).
4.  **Network**: Cilium/Istio enforce mTLS and NetworkPolicies.

## 4. Directory Map
*   `/observability`: Monitoring, Logging, Tracing.
*   `/security`: Falco, Trivy, Kyverno.
*   `/networking`: Cilium, Istio.
*   `/cicd`: Argo, Jenkins.
*   `/storage`: Velero, etcd.
*   `/iac`: Terraform.
