# Advanced Kubernetes Concepts

This document explores advanced features that allow you to extend and customize Kubernetes.

## 1. Custom Resource Definitions (CRDs)
CRDs allow you to define your own API objects.
- **Use Case**: Implementing a "Database" resource that provisions an RDS instance.
- **Controller**: You need a custom controller (Operator) to watch the CRD and take action.

## 2. Advanced Scheduling
Kubernetes Scheduler is highly configurable.

### Taints and Tolerations
- **Taint**: Applied to a Node. "Repels" pods.
- **Toleration**: Applied to a Pod. Allows it to schedule on a tainted node.
- **Use Case**: Dedicated nodes for GPU workloads.

### Affinity
- **Node Affinity**: "Attracts" pods to nodes (e.g., "run on SSD nodes").
- **Pod Affinity**: "Attracts" pods to other pods (e.g., "run cache near webapp").
- **Pod Anti-Affinity**: "Repels" pods from other pods (e.g., "don't run two database replicas on the same node").

## 3. Autoscaling
- **HPA**: Scales replicas based on metrics (CPU, Memory, Custom).
- **VPA**: Adjusts resource requests/limits for pods.
- **Cluster Autoscaler**: Adds/removes nodes when pods are pending or nodes are underutilized.
