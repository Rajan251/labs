# Prerequisites - Setting Up Your GitOps Environment

## 📋 System Requirements

Before starting, ensure your system meets these minimum requirements:

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 8GB | 16GB |
| **CPU** | 4 cores | 6+ cores |
| **Disk Space** | 30GB free | 50GB+ free |
| **OS** | macOS, Linux, Windows (WSL2) | macOS, Linux |
| **Docker** | 20.10+ | Latest |

## 🎯 Kubernetes Cluster Options

You need a local Kubernetes cluster. Here's a comparison to help you choose:

### Minikube vs Kind Comparison

| Feature | Minikube | Kind |
|---------|----------|------|
| **Startup Time** | ~2 minutes | ~30 seconds |
| **Resource Usage** | Moderate | Light |
| **Multi-node** | Yes (complex) | Yes (easy) |
| **LoadBalancer** | Built-in (`minikube tunnel`) | Requires MetalLB |
| **Ingress** | Easy (`minikube addons enable ingress`) | Manual setup |
| **Best For** | Beginners, UI tools | Fast iteration, CI/CD |
| **Driver Options** | Docker, VirtualBox, KVM | Docker only |

**Recommendation**: 
- **Minikube** for beginners and learning
- **Kind** for faster workflows and CI/CD testing

---

## 🔧 Installation Guide

### Option 1: Minikube Setup

#### macOS

```bash
# Install Minikube
brew install minikube

# Verify installation
minikube version

# Start cluster with recommended resources
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=40g \
  --driver=docker \
  --kubernetes-version=v1.28.0

# Verify cluster
kubectl get nodes

# Expected output:
# NAME       STATUS   ROLES           AGE   VERSION
# minikube   Ready    control-plane   1m    v1.28.0
```

#### Linux

```bash
# Download Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64

# Install
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Clean up
rm minikube-linux-amd64

# Verify installation
minikube version

# Start cluster
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=40g \
  --driver=docker \
  --kubernetes-version=v1.28.0

# Verify
kubectl get nodes
```

#### Windows (WSL2)

```bash
# In WSL2 terminal
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64

# Start cluster
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=40g \
  --driver=docker

# Verify
kubectl get nodes
```

**Minikube Useful Commands:**

```bash
# Get cluster status
minikube status

# Stop cluster
minikube stop

# Delete cluster
minikube delete

# Access dashboard
minikube dashboard

# Enable addons
minikube addons enable ingress
minikube addons enable metrics-server

# Set up LoadBalancer (run in separate terminal)
minikube tunnel
```

---

### Option 2: Kind Setup

#### macOS

```bash
# Install Kind
brew install kind

# Verify installation
kind version

# Create cluster with custom config
cat <<EOF > kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: gitops-lab
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
EOF

# Create cluster
kind create cluster --config kind-config.yaml

# Verify
kubectl get nodes

# Expected output:
# NAME                       STATUS   ROLES           AGE   VERSION
# gitops-lab-control-plane   Ready    control-plane   1m    v1.28.0
# gitops-lab-worker          Ready    <none>          1m    v1.28.0
# gitops-lab-worker2         Ready    <none>          1m    v1.28.0
```

#### Linux

```bash
# Install Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Verify
kind version

# Create cluster (use same kind-config.yaml from macOS section)
kind create cluster --config kind-config.yaml

# Verify
kubectl get nodes
```

#### Windows (WSL2)

```bash
# Same as Linux instructions
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Create cluster
kind create cluster --config kind-config.yaml
```

**Kind Useful Commands:**

```bash
# List clusters
kind get clusters

# Get kubeconfig
kind get kubeconfig --name gitops-lab

# Delete cluster
kind delete cluster --name gitops-lab

# Load local Docker image into cluster
kind load docker-image myapp:latest --name gitops-lab
```

---

## 🛠️ Essential Tools Installation

### kubectl (Kubernetes CLI)

#### macOS

```bash
# Install kubectl
brew install kubectl

# Verify
kubectl version --client

# Set up autocomplete (optional but recommended)
echo 'source <(kubectl completion bash)' >> ~/.bashrc
# OR for zsh:
echo 'source <(kubectl completion zsh)' >> ~/.zshrc
```

#### Linux

```bash
# Download kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify
kubectl version --client

# Set up autocomplete
echo 'source <(kubectl completion bash)' >> ~/.bashrc
source ~/.bashrc
```

#### Windows (WSL2)

```bash
# Same as Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client
```

**Test kubectl:**

```bash
# Check cluster connection
kubectl cluster-info

# Get nodes
kubectl get nodes

# Get all resources in all namespaces
kubectl get all --all-namespaces
```

---

### Helm (Kubernetes Package Manager)

#### macOS

```bash
# Install Helm
brew install helm

# Verify
helm version
```

#### Linux

```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify
helm version
```

#### Windows (WSL2)

```bash
# Same as Linux
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

**Test Helm:**

```bash
# Add a repository
helm repo add bitnami https://charts.bitnami.com/bitnami

# Update repositories
helm repo update

# Search for a chart
helm search repo nginx
```

---

### Docker

Docker should already be installed for Minikube/Kind to work.

**Verify Docker:**

```bash
# Check Docker version
docker --version

# Check Docker is running
docker ps

# Test Docker
docker run hello-world
```

**If Docker is not installed:**

- **macOS**: Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
- **Linux**: Follow [official Docker installation guide](https://docs.docker.com/engine/install/)
- **Windows**: Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop) and enable WSL2 backend

---

### Git

Git is required for GitOps workflows.

#### macOS

```bash
# Install Git (if not already installed)
brew install git

# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify
git --version
```

#### Linux

```bash
# Install Git
sudo apt-get update
sudo apt-get install git

# Configure
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify
git --version
```

---

## 📦 Container Registry Setup

You need a container registry to store your Docker images. Two free options:

### Option 1: Docker Hub (Recommended for beginners)

```bash
# 1. Create account at https://hub.docker.com

# 2. Login from terminal
docker login
# Enter username and password

# 3. Test by pushing an image
docker tag hello-world:latest yourusername/hello-world:test
docker push yourusername/hello-world:test

# 4. Verify on Docker Hub website
```

**Create Repository:**
- Go to https://hub.docker.com
- Click "Create Repository"
- Name: `guestbook-frontend`, `guestbook-backend`, etc.
- Visibility: Public (for this lab)

### Option 2: GitHub Container Registry

```bash
# 1. Create GitHub Personal Access Token
# Go to: Settings → Developer settings → Personal access tokens → Tokens (classic)
# Create token with 'write:packages' and 'read:packages' scopes

# 2. Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# 3. Test by pushing an image
docker tag hello-world:latest ghcr.io/YOUR_GITHUB_USERNAME/hello-world:test
docker push ghcr.io/YOUR_GITHUB_USERNAME/hello-world:test

# 4. Verify at https://github.com/YOUR_USERNAME?tab=packages
```

---

## 🔐 GitHub Repository Setup

You'll need a Git repository for your GitOps configurations.

### Create GitHub Repository

```bash
# 1. Go to https://github.com/new
# 2. Repository name: gitops-lab-config
# 3. Description: GitOps configuration for lab environment
# 4. Visibility: Public (for this lab)
# 5. Initialize with README: Yes
# 6. Click "Create repository"

# Clone the repository
git clone https://github.com/YOUR_USERNAME/gitops-lab-config.git
cd gitops-lab-config

# Create initial structure
mkdir -p apps/guestbook/{base,overlays/{dev,staging,prod}}
mkdir -p apps/wordpress/{base,overlays/{dev,staging,prod}}
mkdir -p infrastructure/{namespaces,monitoring,networking,storage}
mkdir -p argocd/applications
mkdir -p charts

# Create README
cat <<EOF > README.md
# GitOps Lab Configuration

This repository contains Kubernetes manifests managed via ArgoCD.

## Structure

- \`apps/\` - Application configurations
- \`infrastructure/\` - Cluster infrastructure
- \`argocd/\` - ArgoCD Application manifests
- \`charts/\` - Helm charts
EOF

# Commit and push
git add .
git commit -m "Initial repository structure"
git push origin main
```

---

## ✅ Verification Checklist

Run these commands to verify your setup:

```bash
# 1. Kubernetes cluster
kubectl get nodes
# ✅ Should show nodes in Ready state

# 2. kubectl
kubectl version --client
# ✅ Should show version v1.28.x or newer

# 3. Helm
helm version
# ✅ Should show version v3.x

# 4. Docker
docker ps
# ✅ Should show running containers

# 5. Git
git --version
# ✅ Should show Git version

# 6. Container registry
docker login
# ✅ Should show successful login

# 7. GitHub repository
cd gitops-lab-config && git remote -v
# ✅ Should show your GitHub repository

# 8. Cluster resources
kubectl get pods --all-namespaces
# ✅ Should show system pods running
```

---

## 🐛 Common Issues & Solutions

### Issue: Minikube fails to start

```bash
# Solution 1: Delete and recreate
minikube delete
minikube start --cpus=4 --memory=8192

# Solution 2: Change driver
minikube start --driver=virtualbox  # or --driver=kvm2

# Solution 3: Check Docker is running
docker ps
```

### Issue: kubectl cannot connect

```bash
# Check cluster is running
minikube status  # or: kind get clusters

# Verify kubeconfig
kubectl config get-contexts

# Set correct context
kubectl config use-context minikube  # or: kind-gitops-lab
```

### Issue: Docker login fails

```bash
# Clear Docker credentials
rm ~/.docker/config.json

# Login again
docker login
```

### Issue: Insufficient resources

```bash
# Check available resources
docker stats

# Increase Docker resources:
# Docker Desktop → Settings → Resources
# Increase Memory to 8GB+, CPUs to 4+
```

---

## 🎓 Next Steps

Prerequisites complete! Now you're ready to:

1. **Install ArgoCD**: [argocd/installation.md](installation.md)
2. **Quick Start**: [QUICKSTART.md](../QUICKSTART.md)
3. **Learn Concepts**: [concepts/README.md](../concepts/README.md)

---

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Kind Documentation](https://kind.sigs.k8s.io/)
- [Docker Documentation](https://docs.docker.com/)
- [Helm Documentation](https://helm.sh/docs/)
