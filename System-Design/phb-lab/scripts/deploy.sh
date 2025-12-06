#!/bin/bash
set -e

NAMESPACE="default"
RELEASE_NAME="video-platform"
CHART_PATH="./k8s/charts/video-platform"

echo "Deploying $RELEASE_NAME to namespace $NAMESPACE..."

# Ensure Helm is installed
if ! command -v helm &> /dev/null; then
    echo "Helm could not be found"
    exit 1
fi

# Update dependencies
if [ -f "$CHART_PATH/Chart.yaml" ]; then
    helm dependency update $CHART_PATH
fi

# Install or Upgrade
helm upgrade --install $RELEASE_NAME $CHART_PATH \
    --namespace $NAMESPACE \
    --create-namespace \
    --wait

echo "Deployment complete!"
kubectl get pods -n $NAMESPACE
