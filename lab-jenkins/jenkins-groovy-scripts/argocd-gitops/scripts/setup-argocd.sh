#!/bin/bash
# ============================================================================
# ARGOCD SETUP SCRIPT
# ============================================================================
# File: argocd-gitops/scripts/setup-argocd.sh
# Purpose: Install and configure ArgoCD on Kubernetes cluster
# ============================================================================

set -e

echo "========================================="
echo "ARGOCD INSTALLATION SCRIPT"
echo "========================================="

# Create argocd namespace
echo "Creating argocd namespace..."
kubectl create namespace argocd || true

# Install ArgoCD
echo "Installing ArgoCD..."
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
echo "Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get initial admin password
echo "========================================="
echo "ArgoCD Admin Password:"
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo ""
echo "========================================="

# Expose ArgoCD server (choose one method)
echo "Exposing ArgoCD server..."

# Method 1: Port Forward (for local access)
# kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Method 2: LoadBalancer (for cloud)
# kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# Method 3: Ingress (recommended for production)
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server
  namespace: argocd
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
spec:
  tls:
  - hosts:
    - argocd.company.com
    secretName: argocd-tls
  rules:
  - host: argocd.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: argocd-server
            port:
              number: 443
EOF

echo "========================================="
echo "✅ ArgoCD installed successfully!"
echo "Access ArgoCD at: https://argocd.company.com"
echo "Username: admin"
echo "Password: (shown above)"
echo "========================================="

# Install ArgoCD CLI (optional)
echo "Installing ArgoCD CLI..."
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd

echo "✅ ArgoCD CLI installed"
echo "========================================="
