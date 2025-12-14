#!/bin/bash

# Bootstrap ArgoCD
# This script installs ArgoCD, waits for it to be ready, and prints the initial admin password.

set -e

NAMESPACE="argocd"
VERSION="v2.10.0" # Pinning a version for stability

echo "Creating namespace $NAMESPACE..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo "Installing ArgoCD..."
kubectl apply -n $NAMESPACE -f https://raw.githubusercontent.com/argoproj/argo-cd/$VERSION/manifests/install.yaml

echo "Waiting for ArgoCD server to be ready..."
kubectl wait --for=condition=available deployment/argocd-server -n $NAMESPACE --timeout=300s

echo "ArgoCD is ready!"

echo "Getting initial admin password..."
PASSWORD=$(kubectl -n $NAMESPACE get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

echo "--------------------------------------------------"
echo "ArgoCD URL: https://localhost:8080 (after port-forward)"
echo "Username: admin"
echo "Password: $PASSWORD"
echo "--------------------------------------------------"
echo "Run this command to access the UI:"
echo "kubectl port-forward svc/argocd-server -n $NAMESPACE 8080:443"
