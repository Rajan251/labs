# GitOps Setup Guide (ArgoCD)

This guide details how to set up ArgoCD for GitOps, including automation scripts for common tasks.

## Concepts
Before starting, review the [GitOps Concepts](../documentation/concepts.md) and [Workflow](../documentation/gitops-flow.md).

## 1. Install ArgoCD

You can use the provided bootstrap script to install ArgoCD and get the admin password automatically:

```bash
chmod +x ../scripts/bootstrap-argocd.sh
../scripts/bootstrap-argocd.sh
```

Alternatively, install manually via Helm:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

helm install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  -f argocd-values.yaml
```

## 2. Access UI

If you used the bootstrap script, the password was printed to the console. Otherwise:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
```

Port-forward:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

## 3. Deploy Applications

Apply the "App of Apps" pattern to bootstrap your cluster applications:

```bash
kubectl apply -f app-of-apps.yaml
```

## 4. Automation Scripts

We provide helper scripts in the `scripts/` directory:

- `bootstrap-argocd.sh`: Installs ArgoCD and prints credentials.
- `sync-app.sh`: Manually triggers a sync for an app (useful for CI pipelines).
- `create-repo-secret.sh`: Adds a private Git repository to ArgoCD.

