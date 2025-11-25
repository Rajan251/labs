#!/bin/bash

# kubectl and Helm Installation Script
# This script installs kubectl and Helm on Ubuntu

set -e

echo "========================================="
echo "kubectl and Helm Installation Script"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Install kubectl
echo "Installing kubectl..."
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

# Verify kubectl installation
echo "Verifying kubectl installation..."
kubectl version --client

# Install Helm
echo "Installing Helm..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify Helm installation
echo "Verifying Helm installation..."
helm version

# Install for jenkins user (if exists)
if id "jenkins" &>/dev/null; then
    echo "Installing kubectl for jenkins user..."
    sudo -u jenkins mkdir -p /var/lib/jenkins/.local/bin
    cp /usr/local/bin/kubectl /var/lib/jenkins/.local/bin/
    chown jenkins:jenkins /var/lib/jenkins/.local/bin/kubectl
fi

echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "kubectl version:"
kubectl version --client
echo ""
echo "Helm version:"
helm version
echo ""
echo "========================================="
