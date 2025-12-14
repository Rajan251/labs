# GitOps Workflow

## Overview
GitOps uses Git as the single source of truth for declarative infrastructure and applications.

## Workflow

1. **Code Change**: Developer pushes code to the application repository.
2. **CI Pipeline**: Jenkins/Tekton builds the image, pushes it to the registry, and updates the Helm chart version in the **Infrastructure Repository**.
3. **Sync**: ArgoCD detects the change in the Infrastructure Repository.
4. **Reconciliation**: ArgoCD applies the new manifest to the Kubernetes cluster, ensuring the live state matches the desired state in Git.

## App of Apps Pattern
We use the "App of Apps" pattern where a root Application manages other Applications. This allows us to manage the ArgoCD configuration itself via GitOps.
