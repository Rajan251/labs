# Integration Tests

This directory contains integration tests to verify the interaction between different components of the Kubernetes cluster.

## Frontend-Backend Connectivity Test

The `frontend-backend-test.sh` script verifies that a frontend service can communicate with a backend service within the cluster.

### Prerequisites
- A running Kubernetes cluster
- `kubectl` configured to communicate with the cluster

### Usage

```bash
chmod +x frontend-backend-test.sh
./frontend-backend-test.sh
```

### What it does
1. Creates a temporary namespace.
2. Deploys a mock backend (Nginx).
3. Deploys a mock frontend (Busybox).
4. Executes a `wget` command from the frontend to the backend.
5. Cleans up resources.
