# Pods - Kubernetes Fundamentals

This section contains comprehensive examples of Kubernetes Pods, demonstrating all pod patterns and best practices.

## Overview

A Pod is the smallest deployable unit in Kubernetes. It represents a single instance of a running process in your cluster and can contain one or more containers.

## Directory Structure

```
01-pods/
├── examples/
│   ├── 01-basic-pods/           # Single and multi-container pods
│   ├── 02-init-containers/      # Init container patterns
│   ├── 03-sidecar-patterns/     # Sidecar containers
│   ├── 04-ambassador-patterns/  # Ambassador pattern
│   ├── 05-adapter-patterns/     # Adapter pattern
│   ├── 06-lifecycle-hooks/      # postStart and preStop hooks
│   ├── 07-pod-disruption/       # Pod disruption budgets
│   ├── 08-pod-priority/         # Priority and preemption
│   ├── 09-topology-spread/      # Topology spread constraints
│   └── 10-pod-security/         # Pod security standards
├── labs/
│   ├── lab-01-your-first-pod.md
│   ├── lab-02-multi-container-pods.md
│   ├── lab-03-init-containers.md
│   ├── lab-04-sidecar-logging.md
│   └── lab-05-lifecycle-management.md
└── documentation/
    └── pods-deep-dive.md
```

## Quick Start

### Deploy a Basic Pod

```bash
# Deploy a simple nginx pod
kubectl apply -f examples/01-basic-pods/simple-pod.yaml

# Check pod status
kubectl get pods

# View pod details
kubectl describe pod nginx-pod

# View logs
kubectl logs nginx-pod

# Execute command in pod
kubectl exec -it nginx-pod -- /bin/bash

# Delete pod
kubectl delete pod nginx-pod
```

## Examples Overview

### 1. Basic Pods
- **simple-pod.yaml**: Single container pod
- **multi-container-pod.yaml**: Multiple containers sharing resources
- **pod-with-resources.yaml**: Resource requests and limits
- **pod-with-labels.yaml**: Labels and selectors
- **pod-with-annotations.yaml**: Annotations for metadata

### 2. Init Containers
- **database-migration.yaml**: Run migrations before app starts
- **config-setup.yaml**: Setup configuration files
- **dependency-check.yaml**: Wait for dependencies
- **git-clone.yaml**: Clone repository before app starts

### 3. Sidecar Patterns
- **logging-sidecar.yaml**: Log aggregation sidecar
- **monitoring-sidecar.yaml**: Metrics collection sidecar
- **proxy-sidecar.yaml**: Network proxy sidecar
- **config-reload.yaml**: Configuration reload sidecar

### 4. Ambassador Patterns
- **database-ambassador.yaml**: Database connection proxy
- **cache-ambassador.yaml**: Cache proxy
- **api-ambassador.yaml**: API gateway sidecar

### 5. Adapter Patterns
- **log-adapter.yaml**: Convert log formats
- **metrics-adapter.yaml**: Convert metrics formats
- **monitoring-adapter.yaml**: Adapt monitoring data

### 6. Lifecycle Hooks
- **poststart-hook.yaml**: Execute commands after container starts
- **prestop-hook.yaml**: Graceful shutdown
- **combined-hooks.yaml**: Both postStart and preStop

### 7. Pod Disruption Budgets
- **pdb-minAvailable.yaml**: Minimum available pods
- **pdb-maxUnavailable.yaml**: Maximum unavailable pods
- **pdb-percentage.yaml**: Percentage-based PDB

### 8. Pod Priority
- **high-priority-pod.yaml**: High priority workload
- **low-priority-pod.yaml**: Low priority workload
- **priority-class.yaml**: Custom priority classes

### 9. Topology Spread
- **spread-across-zones.yaml**: Spread across availability zones
- **spread-across-nodes.yaml**: Spread across nodes
- **max-skew-constraint.yaml**: Control distribution skew

### 10. Pod Security
- **privileged-pod.yaml**: Privileged security context
- **baseline-pod.yaml**: Baseline security standard
- **restricted-pod.yaml**: Restricted security standard

## Learning Path

1. **Beginner**: Start with basic pods (01-basic-pods)
2. **Intermediate**: Learn init containers and sidecar patterns
3. **Advanced**: Explore lifecycle hooks, disruption budgets, and topology spread
4. **Expert**: Master pod security and priority/preemption

## Best Practices

### Resource Management
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

### Security Context
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
```

### Health Checks
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Labels and Annotations
```yaml
metadata:
  labels:
    app: myapp
    tier: backend
    environment: production
  annotations:
    description: "Application backend service"
    version: "1.0.0"
```

## Common Commands

```bash
# Create pod
kubectl apply -f pod.yaml

# Get pods
kubectl get pods
kubectl get pods -o wide
kubectl get pods --show-labels

# Describe pod
kubectl describe pod <pod-name>

# View logs
kubectl logs <pod-name>
kubectl logs <pod-name> -c <container-name>  # Multi-container
kubectl logs <pod-name> -f                    # Follow logs
kubectl logs <pod-name> --previous            # Previous instance

# Execute commands
kubectl exec <pod-name> -- <command>
kubectl exec -it <pod-name> -- /bin/bash

# Port forwarding
kubectl port-forward <pod-name> 8080:80

# Copy files
kubectl cp <pod-name>:/path/to/file ./local-file
kubectl cp ./local-file <pod-name>:/path/to/file

# Delete pod
kubectl delete pod <pod-name>
kubectl delete -f pod.yaml
```

## Troubleshooting

### Pod Not Starting
```bash
# Check pod events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>

# Common issues:
# - Image pull errors
# - Resource constraints
# - Configuration errors
# - Volume mount issues
```

### Pod Crashing
```bash
# View previous logs
kubectl logs <pod-name> --previous

# Check resource usage
kubectl top pod <pod-name>

# Common issues:
# - Application errors
# - Out of memory
# - Liveness probe failures
```

### Networking Issues
```bash
# Test connectivity
kubectl exec <pod-name> -- ping <target>
kubectl exec <pod-name> -- curl <url>

# Check DNS
kubectl exec <pod-name> -- nslookup kubernetes.default
```

## Related Resources

- [Kubernetes Pods Documentation](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)

## Next Steps

After mastering pods, proceed to:
- [Controllers](../02-controllers/) - Deployments, StatefulSets, DaemonSets
- [Services](../03-services/) - Service discovery and networking
- [Storage](../04-storage/) - Persistent volumes and storage
