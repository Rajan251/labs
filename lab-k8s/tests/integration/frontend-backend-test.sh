#!/bin/bash

# Integration Test: Frontend -> Backend Connectivity
# This script deploys a simple frontend and backend, then verifies connectivity.

set -e

NAMESPACE="integration-test-$(date +%s)"
echo "Starting Integration Test in namespace: $NAMESPACE"

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    kubectl delete namespace $NAMESPACE --ignore-not-found
}
trap cleanup EXIT

# 1. Create Namespace
kubectl create namespace $NAMESPACE

# 2. Deploy Backend (Nginx as a mock backend)
echo "Deploying Backend..."
kubectl run backend --image=nginx --port=80 -n $NAMESPACE --expose
kubectl wait --for=condition=ready pod/backend -n $NAMESPACE --timeout=60s

# 3. Deploy Frontend (Busybox to curl backend)
echo "Deploying Frontend..."
kubectl run frontend --image=busybox --restart=Never -n $NAMESPACE -- sleep 3600
kubectl wait --for=condition=ready pod/frontend -n $NAMESPACE --timeout=60s

# 4. Verify Connectivity
echo "Verifying Connectivity..."
kubectl exec frontend -n $NAMESPACE -- wget -qO- http://backend
if [ $? -eq 0 ]; then
    echo "SUCCESS: Frontend can reach Backend."
else
    echo "FAILURE: Frontend cannot reach Backend."
    exit 1
fi

echo "Integration Test Completed Successfully."
