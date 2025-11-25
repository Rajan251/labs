#!/bin/bash

# Kubernetes Access Setup Script
# This script helps configure Kubernetes access for Jenkins

set -e

echo "========================================="
echo "Kubernetes Access Setup Script"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

echo ""
echo "This script will help you set up Kubernetes access for Jenkins."
echo ""

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "kubectl is not installed. Please install it first."
    exit 1
fi

# Option 1: Copy kubeconfig
echo "Option 1: Copy existing kubeconfig"
echo "-----------------------------------"
read -p "Do you have a kubeconfig file to copy? (y/n): " has_kubeconfig

if [ "$has_kubeconfig" = "y" ]; then
    read -p "Enter path to kubeconfig file: " kubeconfig_path
    
    if [ -f "$kubeconfig_path" ]; then
        echo "Copying kubeconfig for jenkins user..."
        sudo -u jenkins mkdir -p /var/lib/jenkins/.kube
        cp "$kubeconfig_path" /var/lib/jenkins/.kube/config
        chown jenkins:jenkins /var/lib/jenkins/.kube/config
        chmod 600 /var/lib/jenkins/.kube/config
        
        echo "Testing kubectl access..."
        sudo -u jenkins kubectl get nodes
        
        echo "✅ Kubeconfig copied successfully!"
    else
        echo "❌ File not found: $kubeconfig_path"
    fi
fi

# Option 2: Create service account
echo ""
echo "Option 2: Create Service Account"
echo "---------------------------------"
read -p "Do you want to create a Jenkins service account? (y/n): " create_sa

if [ "$create_sa" = "y" ]; then
    echo "Creating Jenkins service account..."
    
    # Create service account YAML
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: jenkins
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: jenkins
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints", "persistentvolumeclaims", "events", "configmaps", "secrets"]
  verbs: ["*"]
- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "replicasets", "statefulsets"]
  verbs: ["*"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["*"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["*"]
- apiGroups: ["autoscaling"]
  resources: ["horizontalpodautoscalers"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: jenkins
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: jenkins
subjects:
- kind: ServiceAccount
  name: jenkins
  namespace: default
---
apiVersion: v1
kind: Secret
metadata:
  name: jenkins-token
  namespace: default
  annotations:
    kubernetes.io/service-account.name: jenkins
type: kubernetes.io/service-account-token
EOF

    echo "Waiting for token to be created..."
    sleep 5
    
    # Get token
    echo ""
    echo "========================================="
    echo "Jenkins Service Account Token:"
    echo "========================================="
    kubectl get secret jenkins-token -n default -o jsonpath='{.data.token}' | base64 -d
    echo ""
    echo ""
    echo "========================================="
    echo "Kubernetes API Server:"
    echo "========================================="
    kubectl cluster-info | grep 'Kubernetes control plane'
    echo ""
    echo "========================================="
    echo ""
    echo "Save this token in Jenkins credentials as 'Secret text'"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Add credentials in Jenkins (Manage Jenkins → Manage Credentials)"
echo "2. Test access in a Jenkins pipeline"
echo ""
