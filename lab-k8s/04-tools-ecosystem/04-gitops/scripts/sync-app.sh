#!/bin/bash

# Sync ArgoCD Application
# This script triggers a sync for a specific ArgoCD application.
# Prerequisite: argocd CLI installed and logged in.

APP_NAME=$1

if [ -z "$APP_NAME" ]; then
  echo "Usage: $0 <app-name>"
  exit 1
fi

echo "Syncing application: $APP_NAME..."
argocd app sync $APP_NAME

echo "Waiting for sync to complete..."
argocd app wait $APP_NAME --sync --health --operation

echo "Sync completed for $APP_NAME."
