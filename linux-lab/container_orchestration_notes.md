# Container Technology & Orchestration

**Level:** Expert / DevOps / SRE
**Focus:** Container internals, Docker, Kubernetes, and production patterns.

---

## 1. Container Fundamentals

### 1.1 Namespace Isolation
Linux namespaces provide process isolation.
*   **PID**: Process IDs. Container sees only its processes.
*   **NET**: Network stack. Container has its own IP, routing table.
*   **MNT**: Mount points. Container has its own filesystem view.
*   **UTS**: Hostname. Container can have different hostname.
*   **IPC**: Inter-Process Communication. Shared memory isolation.
*   **USER**: User IDs. Map container root to host non-root (security).

### 1.2 Control Groups (cgroups)
Resource limits enforcement.
```bash
# Limit container to 512MB RAM
docker run -m 512m myapp

# Limit to 1 CPU core
docker run --cpus="1.0" myapp
```

### 1.3 Union Filesystems
*   **OverlayFS**: Modern, default. Layers stack on top of each other.
*   **Image Layers**: Each Dockerfile instruction = new layer. Cached for speed.

---

## 2. Docker Deep Dive

### 2.1 Image Layer Caching
```dockerfile
# BAD: npm install runs every time code changes
COPY . /app
RUN npm install

# GOOD: Cache npm install unless package.json changes
COPY package.json /app/
RUN npm install
COPY . /app
```

### 2.2 Multi-Stage Builds
```dockerfile
# Stage 1: Build
FROM golang:1.20 AS builder
COPY . /src
RUN go build -o /app

# Stage 2: Runtime (minimal)
FROM alpine:3.18
COPY --from=builder /app /app
CMD ["/app"]
```
*   **Benefit**: Final image is tiny (no build tools).

### 2.3 Dockerfile Best Practices
*   **Use specific tags**: `FROM node:18-alpine` (not `node:latest`).
*   **Run as non-root**: `USER 1000`.
*   **Minimize layers**: Combine RUN commands with `&&`.

---

## 3. Kubernetes Architecture

### 3.1 Control Plane
*   **API Server**: REST API. All kubectl commands go here.
*   **etcd**: Distributed key-value store. Cluster state.
*   **Scheduler**: Assigns pods to nodes based on resources.
*   **Controller Manager**: Reconciliation loops (ensure desired state).

### 3.2 Node Components
*   **kubelet**: Agent on each node. Manages pods.
*   **kube-proxy**: Network proxy. Implements Services.
*   **Container Runtime**: Docker, containerd, CRI-O.

### 3.3 Networking (CNI)
*   **Calico**: L3 routing. Network policies.
*   **Flannel**: Simple overlay. Good for small clusters.
*   **Cilium**: eBPF-based. High performance.

### 3.4 Storage
*   **PV (PersistentVolume)**: Cluster-wide storage resource.
*   **PVC (PersistentVolumeClaim)**: User request for storage.
*   **StorageClass**: Dynamic provisioning (AWS EBS, GCP PD).

---

## 4. Pod Design Patterns

### 4.1 Sidecar
Logging agent alongside main app.
```yaml
containers:
- name: app
  image: myapp
- name: log-shipper
  image: fluentd
```

### 4.2 Init Containers
Run before main container. Setup tasks.
```yaml
initContainers:
- name: wait-for-db
  image: busybox
  command: ['sh', '-c', 'until nc -z db 5432; do sleep 1; done']
```

---

## 5. Security in Containers

### 5.1 Image Scanning
*   **Trivy**: `trivy image myapp:latest`.
*   Scan for CVEs before deploying.

### 5.2 Runtime Security
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
```

### 5.3 Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      app: backend
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
```

---

## 6. Monitoring Containerized Workloads

### 6.1 Metrics
*   **cAdvisor**: Built into kubelet. Container metrics.
*   **Prometheus**: Scrapes metrics. PromQL queries.

### 6.2 Logs
*   **Centralized**: Fluentd/Fluent Bit -> Elasticsearch/Loki.
*   **Structured**: JSON logs for easy parsing.

---

## 7. Troubleshooting Kubernetes

### 7.1 Pod States
*   **Pending**: Scheduler can't find node (resource constraints).
*   **CrashLoopBackOff**: Container keeps crashing. Check logs: `kubectl logs <pod>`.
*   **ImagePullBackOff**: Can't pull image. Check image name, registry auth.

### 7.2 Debugging Commands
```bash
kubectl describe pod <pod>
kubectl logs <pod> -c <container>
kubectl exec -it <pod> -- /bin/sh
kubectl get events --sort-by='.lastTimestamp'
```

---

## 8. Production Considerations

### 8.1 Resource Requests & Limits
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "500m"
  limits:
    memory: "512Mi"
    cpu: "1000m"
```
*   **Requests**: Scheduler uses this. Guaranteed resources.
*   **Limits**: Hard cap. Pod killed if exceeded (OOMKilled).

### 8.2 Scaling
*   **Horizontal (HPA)**: Add more pods. Good for stateless apps.
*   **Vertical (VPA)**: Increase pod resources. Good for stateful apps.

### 8.3 Update Strategies
*   **RollingUpdate**: Default. Gradual replacement.
*   **Recreate**: Delete all, then create new (downtime).
*   **Blue/Green**: Two environments. Switch traffic.
*   **Canary**: Route small % of traffic to new version.
