# Repository File Structure & Organization

This document explains the layout of the `k8s-course` repository. The structure is designed to mimic a real-world production infrastructure repository, separating learning labs from reusable patterns and documentation.

## Directory Tree

```text
k8s-course/
├── ci/                         # CI/CD pipeline configurations
│   └── github-actions/         # GitHub Actions workflows
│       └── deploy.yml          # Example workflow to build & push Docker images
├── docs/                       # Operational documentation & runbooks
│   ├── production-checklist.md # 25+ item checklist for going to production
│   ├── troubleshooting.md      # Cheat sheet for debugging common K8s issues
│   └── repo-structure.md       # This file
├── examples/                   # Advanced patterns & reference implementations
│   ├── helm-chart-example/     # Sample Helm chart structure
│   │   ├── Chart.yaml          # Chart metadata
│   │   └── values.yaml         # Default configuration values
│   └── operator-example/       # Kubernetes Operator pattern examples
│       └── website-crd.yaml    # Custom Resource Definition (CRD) example
├── labs/                       # Hands-on learning modules
│   ├── 01-getting-started/     # Module 1: Core Concepts
│   │   ├── README.md           # Lab instructions
│   │   └── manifests/          # YAML files for the lab
│   │       ├── nginx-deployment.yaml
│   │       └── nginx-service.yaml
│   ├── 03-ingress/             # Module 3: Networking
│   │   └── manifests/
│   │       └── ingress.yaml
│   └── 04-statefulsets/        # Module 4: Stateful Applications
│       └── manifests/
│           └── redis-statefulset.yaml
└── README.md                   # Entry point for the course
```

## Detailed Breakdown

### 1. `labs/`
Contains step-by-step exercises for learning Kubernetes concepts.
*   **Structure:** Each subdirectory (e.g., `01-getting-started`) represents a specific module or topic.
*   **Contents:**
    *   `README.md`: Instructions, objectives, and verification steps.
    *   `manifests/`: The raw Kubernetes YAML files needed to complete the lab.

### 2. `examples/`
Provides reference implementations for more advanced or complex patterns that might be reused across different projects.
*   **`helm-chart-example/`**: Shows how to package an application using Helm, the K8s package manager.
*   **`operator-example/`**: Demonstrates how to extend Kubernetes with Custom Resource Definitions (CRDs).

### 3. `docs/`
Contains "Runbooks" and operational guides. In a real team, this folder would hold your standard operating procedures (SOPs).
*   **`production-checklist.md`**: A critical artifact ensuring clusters are secure and resilient before launch.
*   **`troubleshooting.md`**: A quick-reference guide for on-call engineers to diagnose issues.

### 4. `ci/`
Houses configuration for Continuous Integration and Continuous Delivery systems.
*   **`github-actions/`**: Contains YAML workflows for GitHub Actions. The `deploy.yml` example shows how to automate building a Docker container and pushing it to a registry.
