#!/bin/bash
# Simple E2E test to verify cluster health

echo "Checking cluster status..."
kubectl get nodes

if [ $? -eq 0 ]; then
  echo "Cluster is reachable."
else
  echo "Failed to reach cluster."
  exit 1
fi

echo "Checking for running pods..."
kubectl get pods -A
