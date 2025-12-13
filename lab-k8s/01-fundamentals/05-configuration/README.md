# Configuration Management - Kubernetes Fundamentals

This section covers ConfigMaps and Secrets for decoupling configuration from application code.

## Directory Structure

```
05-configuration/
├── examples/
│   ├── configmaps/          # ConfigMap examples
│   ├── secrets/             # Secret examples
│   └── external-secrets/    # External Secrets Operator
├── labs/
│   ├── lab-01-configmaps.md
│   └── lab-02-secrets.md
└── documentation/
    └── configuration-best-practices.md
```

## Concepts

| Resource | Description | Use Case |
|----------|-------------|----------|
| **ConfigMap** | Stores non-confidential data in key-value pairs. | Environment variables, config files, command-line args. |
| **Secret** | Stores confidential data (passwords, tokens, keys). Base64 encoded. | Database passwords, TLS certificates, API keys. |

## Best Practices
- **Immutable**: Mark ConfigMaps/Secrets as immutable for safety.
- **Volume Mounts**: Updates to ConfigMaps are reflected in volume mounts automatically (eventually).
- **Env Vars**: Updates require Pod restart.
- **External Secrets**: Use External Secrets Operator to sync with Vault/AWS Secrets Manager.

## Quick Start

```bash
# Create ConfigMap
kubectl create configmap my-config --from-literal=color=blue

# Create Secret
kubectl create secret generic my-secret --from-literal=password=secret123

# Apply YAML
kubectl apply -f examples/configmaps/app-config.yaml
```
