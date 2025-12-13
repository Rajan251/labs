# Advanced Kubernetes Features

This section covers advanced Kubernetes concepts and features for extending and customizing the cluster.

## Directory Structure

```
02-advanced/
├── examples/
│   ├── crds/                # Custom Resource Definitions
│   ├── rbac/                # Role-Based Access Control
│   ├── scheduling/          # Advanced Scheduling (Affinity, Taints)
│   └── hpa-vpa/             # Autoscaling (HPA, VPA)
├── labs/
│   ├── lab-01-rbac.md
│   └── lab-02-crds.md
└── documentation/
    └── advanced-concepts.md
```

## Topics

### Custom Resource Definitions (CRDs)
Extend the Kubernetes API with your own resource types.
- **Operators**: Controllers that manage CRDs.
- **Validation**: OpenAPI schema validation.

### RBAC (Role-Based Access Control)
Control who can do what in the cluster.
- **Role/ClusterRole**: Define permissions.
- **RoleBinding/ClusterRoleBinding**: Assign permissions to users/groups/SAs.

### Advanced Scheduling
- **Taints & Tolerations**: Repel pods from nodes.
- **Node Affinity**: Attract pods to nodes.
- **Pod Affinity/Anti-Affinity**: Co-locate or separate pods.

### Autoscaling
- **HPA**: Horizontal Pod Autoscaler (replicas).
- **VPA**: Vertical Pod Autoscaler (resources).
- **Cluster Autoscaler**: Add/remove nodes.
