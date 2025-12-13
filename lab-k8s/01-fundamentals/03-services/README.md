# Services & Networking - Kubernetes Fundamentals

This section covers Kubernetes Services for service discovery and load balancing, as well as Network Policies for security.

## Directory Structure

```
03-services/
├── examples/
│   ├── services/            # Service types (ClusterIP, NodePort, LB)
│   ├── network-policies/    # Network Policy examples
│   ├── ingress/             # Ingress examples
│   └── dns/                 # DNS debugging
├── labs/
│   ├── lab-01-services.md
│   └── lab-02-network-policies.md
└── documentation/
    └── networking-deep-dive.md
```

## Service Types

| Type | Description | Use Case |
|------|-------------|----------|
| **ClusterIP** | Exposes service on internal IP. Reachable only within cluster. | Internal microservices, databases. Default type. |
| **NodePort** | Exposes service on each Node's IP at a static port. | Development, external access without LoadBalancer. |
| **LoadBalancer** | Exposes service externally using cloud provider's load balancer. | Production public-facing services. |
| **ExternalName** | Maps service to DNS name (CNAME). | Accessing external services (e.g., AWS RDS) via K8s DNS. |
| **Headless** | ClusterIP: None. Returns Pod IPs directly. | StatefulSets, custom service discovery. |

## Network Policies

Network Policies control traffic flow at the IP address or port level (Layer 3/4).
- **Default Deny**: Best practice to start with.
- **Allow List**: Explicitly allow traffic between specific pods/namespaces.

## Quick Start

```bash
# Create a ClusterIP service
kubectl expose deployment myapp --port=80 --target-port=8080 --name=myapp-service

# Create a NodePort service
kubectl expose deployment myapp --type=NodePort --port=80 --name=myapp-nodeport

# Apply Network Policy
kubectl apply -f examples/network-policies/deny-all.yaml
```
