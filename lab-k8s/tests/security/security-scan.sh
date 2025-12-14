#!/bin/bash

# Security Scan Script
# This script uses Trivy to scan container images and Kubernetes manifests for vulnerabilities.

IMAGE_NAME="nginx:latest"
MANIFEST_DIR="../../01-fundamentals/01-pods/examples/01-basic-pods"

echo "Starting Security Scan..."

# Check if Trivy is installed
if ! command -v trivy &> /dev/null; then
    echo "Error: Trivy is not installed. Please install it first."
    exit 1
fi

# 1. Scan Container Image
echo "Scanning Image: $IMAGE_NAME"
trivy image --severity HIGH,CRITICAL $IMAGE_NAME

# 2. Scan Kubernetes Manifests
echo "Scanning Manifests in: $MANIFEST_DIR"
trivy config $MANIFEST_DIR --severity HIGH,CRITICAL

echo "Security Scan Completed."
