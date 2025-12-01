#!/bin/bash
# ============================================================================
# ARGOCD APPLICATION CREATION SCRIPT
# ============================================================================
# File: argocd-gitops/scripts/create-app.sh
# Purpose: Create ArgoCD application using CLI
# ============================================================================

set -e

# Configuration
APP_NAME=${1:-"my-app"}
NAMESPACE=${2:-"dev"}
REPO_URL=${3:-"https://github.com/your-org/gitops-repo.git"}
PATH_IN_REPO=${4:-"manifests/dev"}

echo "========================================="
echo "CREATING ARGOCD APPLICATION"
echo "App Name: $APP_NAME"
echo "Namespace: $NAMESPACE"
echo "Repo: $REPO_URL"
echo "Path: $PATH_IN_REPO"
echo "========================================="

# Login to ArgoCD (requires ARGOCD_PASSWORD env var)
argocd login argocd.company.com --username admin --password $ARGOCD_PASSWORD --insecure

# Create application
argocd app create $APP_NAME \
  --repo $REPO_URL \
  --path $PATH_IN_REPO \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace $NAMESPACE \
  --sync-policy automated \
  --auto-prune \
  --self-heal

echo "✅ Application created successfully"

# Sync application
echo "Syncing application..."
argocd app sync $APP_NAME

# Wait for sync to complete
echo "Waiting for sync to complete..."
argocd app wait $APP_NAME --timeout 300

echo "========================================="
echo "✅ Application deployed successfully!"
echo "========================================="

# Show application status
argocd app get $APP_NAME
