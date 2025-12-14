# GitOps Concepts

## Core Principles

### 1. Declarative Description
The entire system is described declaratively (e.g., Kubernetes manifests, Helm charts). The "desired state" is versioned in Git.

### 2. Canonical Desired State
Git is the single source of truth. If it's not in Git, it shouldn't be in the cluster.

### 3. Automated Sync
Software agents (like ArgoCD) automatically pull the desired state from Git and apply it to the cluster.

### 4. Continuous Reconciliation
The agent continuously monitors the cluster. If the live state drifts from the desired state (e.g., someone manually deletes a pod), the agent detects and corrects it.

## Advanced Concepts

### Push vs. Pull Architecture
- **Push (CI-driven)**: CI pipeline runs `kubectl apply`. Requires CI to have cluster credentials (security risk).
- **Pull (GitOps agent)**: Agent runs *inside* the cluster and pulls changes. No external credentials needed. Better security.

### Sync Waves and Hooks
ArgoCD allows ordering resources during a sync.
- **Sync Waves**: `argocd.argoproj.io/sync-wave: "5"`. Lower numbers apply first.
- **Hooks**: `argocd.argoproj.io/hook: PreSync`. Run jobs before the main sync (e.g., database migrations).

### App of Apps Pattern
A root Application that points to a folder containing *other* Application manifests. This allows you to manage the GitOps configuration itself using GitOps.

### Drift Detection
The ability to detect when the live cluster state differs from Git. ArgoCD shows this visually as "OutOfSync".
