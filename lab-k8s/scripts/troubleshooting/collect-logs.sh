#!/bin/bash
# Troubleshooting helper script

echo "Collecting cluster info..."
kubectl cluster-info
kubectl get nodes
kubectl get pods -A | grep -v Running

echo "Troubleshooting info collected."
