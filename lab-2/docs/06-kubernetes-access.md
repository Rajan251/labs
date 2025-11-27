# 6. Kubernetes Access Configuration

## Overview

This guide covers installing kubectl and Helm, and configuring Jenkins to access your Kubernetes cluster for deployments.

## Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- Cluster admin access
- Jenkins installed with Kubernetes plugin

## Step 1: Install kubectl

### Download kubectl

```bash
# Download latest stable version
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Download specific version
curl -LO "https://dl.k8s.io/release/v1.28.0/bin/linux/amd64/kubectl"

# Verify checksum (optional)
curl -LO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check
```

### Install kubectl

```bash
# Install kubectl
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify installation
kubectl version --client
```

**Expected output**:
```
Client Version: v1.28.0
Kustomize Version: v5.0.4-0.20230601165947-6ce0bf390ce3
```

### Install for Jenkins User

```bash
# Install for jenkins user
sudo -u jenkins mkdir -p /var/lib/jenkins/.local/bin
sudo cp kubectl /var/lib/jenkins/.local/bin/
sudo chown jenkins:jenkins /var/lib/jenkins/.local/bin/kubectl
```

## Step 2: Install Helm

### Method 1: Using Script (Recommended)

```bash
# Download and install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify installation
helm version
```

### Method 2: Manual Installation

```bash
# Download Helm
wget https://get.helm.sh/helm-v3.13.0-linux-amd64.tar.gz

# Extract
tar -zxvf helm-v3.13.0-linux-amd64.tar.gz

# Move to bin
sudo mv linux-amd64/helm /usr/local/bin/helm

# Verify
helm version
```

## Step 3: Configure Kubernetes Access

### Option 1: Using kubeconfig File

#### Get kubeconfig from Cluster

**For cloud providers**:

```bash
# AWS EKS
aws eks update-kubeconfig --region us-east-1 --name my-cluster

# Google GKE
gcloud container clusters get-credentials my-cluster --region us-central1

# Azure AKS
az aks get-credentials --resource-group myResourceGroup --name myAKSCluster
```

**For self-hosted**:

```bash
# Copy from master node
scp user@k8s-master:~/.kube/config ~/.kube/config
```

#### Configure for Jenkins

```bash
# Create .kube directory for jenkins user
sudo -u jenkins mkdir -p /var/lib/jenkins/.kube

# Copy kubeconfig
sudo cp ~/.kube/config /var/lib/jenkins/.kube/config

# Set ownership
sudo chown jenkins:jenkins /var/lib/jenkins/.kube/config

# Test access
sudo -u jenkins kubectl get nodes
```

### Option 2: Service Account with Token

#### Create Service Account

Create `jenkins-sa.yaml`:

```yaml
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
```

Apply:

```bash
kubectl apply -f jenkins-sa.yaml
```

#### Get Service Account Token

**For Kubernetes 1.24+**:

```bash
# Create token (valid for 10 years)
kubectl create token jenkins -n default --duration=87600h

# Or create secret manually
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: jenkins-token
  namespace: default
  annotations:
    kubernetes.io/service-account.name: jenkins
type: kubernetes.io/service-account-token
EOF

# Get token
kubectl get secret jenkins-token -n default -o jsonpath='{.data.token}' | base64 -d
```

**For Kubernetes < 1.24**:

```bash
# Get token from service account
kubectl get secret $(kubectl get sa jenkins -n default -o jsonpath='{.secrets[0].name}') -n default -o jsonpath='{.data.token}' | base64 -d
```

#### Get Cluster CA Certificate

```bash
kubectl get secret jenkins-token -n default -o jsonpath='{.data.ca\.crt}' | base64 -d > ca.crt
```

#### Get API Server URL

```bash
kubectl cluster-info | grep 'Kubernetes control plane'
```

## Step 4: Configure Jenkins Credentials

### Add Kubeconfig Credential

1. **Manage Jenkins** → **Manage Credentials**
2. Click **(global)** domain
3. **Add Credentials**
4. **Kind**: Secret file
5. **File**: Upload kubeconfig file
6. **ID**: `kubeconfig`
7. **Description**: Kubernetes Config
8. **Create**

### Add Token Credential

1. **Manage Jenkins** → **Manage Credentials**
2. **Add Credentials**
3. **Kind**: Secret text
4. **Secret**: Paste token
5. **ID**: `k8s-token`
6. **Description**: Kubernetes Token
7. **Create**

### Add Certificate Credential

1. **Add Credentials**
2. **Kind**: Secret file
3. **File**: Upload ca.crt
4. **ID**: `k8s-ca-cert`
5. **Description**: Kubernetes CA Certificate
6. **Create**

## Step 5: Install Kubernetes Plugin in Jenkins

1. **Manage Jenkins** → **Manage Plugins**
2. **Available** tab
3. Search: **Kubernetes**
4. Install:
   - Kubernetes
   - Kubernetes CLI
   - Kubernetes Credentials Provider
5. Restart Jenkins

## Step 6: Configure Kubernetes Cloud (Optional)

For dynamic Jenkins agents on Kubernetes:

1. **Manage Jenkins** → **Manage Nodes and Clouds** → **Configure Clouds**
2. **Add a new cloud** → **Kubernetes**
3. Configure:
   - **Name**: kubernetes
   - **Kubernetes URL**: https://your-k8s-api:6443
   - **Kubernetes Namespace**: jenkins
   - **Credentials**: Select k8s-token
   - **Jenkins URL**: http://jenkins:8080
4. **Test Connection**
5. **Save**

## Step 7: Test Kubernetes Access

### Create Test Pipeline

```groovy
pipeline {
    agent any
    
    stages {
        stage('Test kubectl') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh 'kubectl version'
                        sh 'kubectl get nodes'
                        sh 'kubectl get namespaces'
                    }
                }
            }
        }
    }
}
```

Run the pipeline to verify access.

## RBAC Configuration

### Namespace-Specific Access

For production, limit Jenkins to specific namespaces:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: jenkins
  namespace: production
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: jenkins
  namespace: production
rules:
- apiGroups: ["", "apps", "batch", "networking.k8s.io"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: jenkins
  namespace: production
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: jenkins
subjects:
- kind: ServiceAccount
  name: jenkins
  namespace: production
```

## Common Authentication Problems

### Problem 1: Unable to Connect to Server

**Error**:
```
Unable to connect to the server: dial tcp: lookup kubernetes.default.svc: no such host
```

**Solutions**:

```bash
# Verify API server URL
kubectl cluster-info

# Test connectivity
curl -k https://your-k8s-api:6443

# Check DNS resolution
nslookup your-k8s-api

# Verify kubeconfig
kubectl config view
```

### Problem 2: Forbidden Error

**Error**:
```
Error from server (Forbidden): pods is forbidden: User "system:serviceaccount:default:jenkins" cannot list resource "pods"
```

**Solution**: Grant proper RBAC permissions

```bash
# Check current permissions
kubectl auth can-i list pods --as=system:serviceaccount:default:jenkins

# Grant permissions
kubectl apply -f jenkins-sa.yaml
```

### Problem 3: x509 Certificate Error

**Error**:
```
x509: certificate signed by unknown authority
```

**Solutions**:

```bash
# Option 1: Add CA certificate to kubeconfig
kubectl config set-cluster my-cluster --certificate-authority=/path/to/ca.crt

# Option 2: Skip TLS verification (not recommended for production)
kubectl config set-cluster my-cluster --insecure-skip-tls-verify=true

# Option 3: Use --insecure-skip-tls-verify flag
kubectl --insecure-skip-tls-verify get nodes
```

### Problem 4: Token Expired

**Error**:
```
error: You must be logged in to the server (Unauthorized)
```

**Solution**: Regenerate token

```bash
# Create new token
kubectl create token jenkins -n default --duration=87600h

# Update credential in Jenkins
```

## Best Practices

1. ✅ **Use service accounts** instead of user credentials
2. ✅ **Implement RBAC** with least privilege
3. ✅ **Use namespace isolation** for different environments
4. ✅ **Rotate tokens** regularly
5. ✅ **Store credentials** securely in Jenkins
6. ✅ **Use separate service accounts** for different pipelines
7. ✅ **Enable audit logging** on Kubernetes
8. ✅ **Monitor API server access**

## Helm Configuration

### Add Helm Repositories

```bash
# Add common repositories
helm repo add stable https://charts.helm.sh/stable
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx

# Update repositories
helm repo update

# List repositories
helm repo list
```

### Test Helm

```bash
# Search for charts
helm search repo nginx

# Install a chart
helm install my-nginx bitnami/nginx

# List releases
helm list

# Uninstall
helm uninstall my-nginx
```

## Next Steps

Proceed to [CI/CD Pipeline](07-cicd-pipeline.md) to build complete Jenkins pipelines for Kubernetes deployments.
