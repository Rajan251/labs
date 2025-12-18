# Prerequisites and Setup Guide

## Overview

This guide covers all prerequisites and setup steps needed to run the GitOps lab environment on your local machine.

## System Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8GB 
- **Disk Space**: 20GB free
- **OS**: Linux, macOS, or Windows with WSL2

### Recommended Requirements
- **CPU**: 8 cores
- **RAM**: 16GB
- **Disk Space**: 40GB free
- **Internet**: Stable connection for downloading images

## Required Tools Installation

### 1. Docker Installation

Docker is required to run local Kubernetes clusters.

#### macOS
```bash
# Using Homebrew
brew install --cask docker

# Or download Docker Desktop from:
# https://www.docker.com/products/docker-desktop
```

#### Linux (Ubuntu/Debian)
```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Windows
Download and install Docker Desktop from: https://www.docker.com/products/docker-desktop

**Verify Installation:**
```bash
docker --version
# Expected: Docker version 20.10.0 or higher
```

### 2. kubectl Installation

kubectl is the Kubernetes command-line tool.

#### macOS
```bash
# Using Homebrew
brew install kubectl

# Or using curl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

#### Linux
```bash
# Download latest stable version
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Make it executable
chmod +x kubectl

# Move to PATH
sudo mv kubectl /usr/local/bin/

# Verify
kubectl version --client
```

#### Windows (PowerShell)
```powershell
curl.exe -LO "https://dl.k8s.io/release/v1.28.0/bin/windows/amd64/kubectl.exe"
```

**Verify Installation:**
```bash
kubectl version --client
# Expected: Client Version v1.28.0 or higher
```

### 3. Helm Installation

Helm is a package manager for Kubernetes, required for ArgoCD installation.

#### macOS
```bash
brew install helm
```

#### Linux
```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

#### Windows (PowerShell)
```powershell
choco install kubernetes-helm
```

**Verify Installation:**
```bash
helm version
# Expected: version.BuildInfo{Version:"v3.x.x", ...}
```

### 4. Git Installation

Git is required for version control.

#### macOS
```bash
brew install git
```

#### Linux
```bash
sudo apt-get install -y git
```

#### Windows
Download from: https://git-scm.com/download/win

**Verify Installation:**
```bash
git --version
# Expected: git version 2.0.0 or higher
```

### 5. Optional: ArgoCD CLI

The ArgoCD CLI provides additional functionality for managing applications.

#### macOS
```bash
brew install argocd
```

#### Linux
```bash
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64
```

#### Windows (PowerShell)
```powershell
$version = (Invoke-RestMethod https://api.github.com/repos/argoproj/argo-cd/releases/latest).tag_name
$url = "https://github.com/argoproj/argo-cd/releases/download/" + $version + "/argocd-windows-amd64.exe"
$output = "argocd.exe"
Invoke-WebRequest -Uri $url -OutFile $output
```

## Local Kubernetes Cluster Options

You need a local Kubernetes cluster. Choose one of the following:

### Option 1: Minikube (Recommended for Beginners)

**Pros:**
- Easy to use
- Well-documented
- Multiple driver options
- Addons for monitoring, ingress, etc.

**Cons:**
- Single-node cluster only
- Higher resource usage

**Installation:**

```bash
# macOS
brew install minikube

# Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Windows
choco install minikube
```

**Start Cluster:**
```bash
# Start with 4 CPUs and 8GB RAM
minikube start --cpus=4 --memory=8192 --driver=docker

# Verify
kubectl get nodes
```

### Option 2: Kind (Kubernetes in Docker)

**Pros:**
- Fast startup
- Multi-node clusters
- Great for CI/CD
- Lightweight

**Cons:**
- Requires Docker
- Less user-friendly than Minikube

**Installation:**

```bash
# macOS/Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# macOS using Homebrew
brew install kind
```

**Start Cluster:**
```bash
# Create cluster
kind create cluster --name gitops-lab

# Verify
kubectl cluster-info --context kind-gitops-lab
```

### Option 3: K3d (K3s in Docker)

**Pros:**
- Very lightweight
- Fast
- Multi-node support
- Built-in load balancer

**Cons:**
- Uses K3s (slightly different from standard K8s)

**Installation:**

```bash
# Linux/macOS
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

# macOS using Homebrew
brew install k3d
```

**Start Cluster:**
```bash
# Create cluster
k3d cluster create gitops-lab --servers 1 --agents 2

# Verify
kubectl get nodes
```

## Container Registry Setup

You need a container registry to push and pull images. Choose one:

### Option 1: Docker Hub (Free)

1. **Create Account**: Visit https://hub.docker.com/ and sign up
2. **Login Locally**:
   ```bash
   docker login
   # Enter username and password
   ```
3. **Create Repository**: Create a public repository named `gitops-demo`

### Option 2: GitHub Container Registry (Free for Public Repos)

1. **Create GitHub Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token with `write:packages` and `read:packages` scopes
   - Save the token securely

2. **Login**:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
   ```

3. **Tag and Push**:
   ```bash
   # Tag image
   docker tag my-app:v1.0.0 ghcr.io/YOUR_GITHUB_USERNAME/my-app:v1.0.0
   
   # Push
   docker push ghcr.io/YOUR_GITHUB_USERNAME/my-app:v1.0.0
   ```

## GitHub Repository Setup

1. **Create Repository**:
   ```bash
   # Create a new directory for your GitOps repo
   mkdir gitops-demo-repo
   cd gitops-demo-repo
   
   # Initialize Git
   git init
   git branch -M main
   
   # Create initial structure (optional - use our templates)
   mkdir -p apps infrastructure charts
   
   # Initial commit
   git add .
   git commit -m "Initial commit"
   
   # Push to GitHub
   git remote add origin https://github.com/YOUR_USERNAME/gitops-demo-repo.git
   git push -u origin main
   ```

2. **Configure Git** (if not already done):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

## Verification Checklist

Run these commands to verify your setup:

```bash
# Docker
docker run hello-world
# Expected: "Hello from Docker!" message

# kubectl
kubectl version --client
# Expected: Client version info

# Helm
helm version
# Expected: version.BuildInfo{...}

# Git
git --version
# Expected: git version 2.x.x

# Kubernetes cluster
kubectl get nodes
# Expected: At least one node in Ready status

# ArgoCD CLI (optional)
argocd version --client
# Expected: argocd: vX.X.X+...
```

## Troubleshooting Setup Issues

### Docker Issues

**Problem**: Permission denied when running docker commands

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or use sudo for docker commands
sudo docker ps
```

### Minikube Issues

**Problem**: Minikube won't start

**Solutions**:
```bash
# Delete and recreate
minikube delete
minikube start --cpus=4 --memory=8192

# Try different driver
minikube start --driver=virtualbox

# Check logs
minikube logs
```

### kubectl Issues

**Problem**: kubectl can't connect to cluster

**Solution**:
```bash
# Check context
kubectl config current-context

# Switch context
kubectl config use-context minikube  # or kind-gitops-lab

# List all contexts
kubectl config get-contexts

# Verify cluster info
kubectl cluster-info
```

### Resource Issues

**Problem**: Not enough resources

**Solution**:
```bash
# For Minikube - adjust resources
minikube delete
minikube start --cpus=2 --memory=4096  # Reduce if needed

# For Kind - use lightweight images
kind create cluster --image kindest/node:v1.28.0
```

## Next Steps

Once you have completed all prerequisites:

1. ✅ Proceed to [02-argocd-installation.md](02-argocd-installation.md)
2. 📖 Read about [GitOps concepts](04-gitops-concepts.md)
3. 🚀 Start with the [Quick Start](../README.md#quick-start-30-minutes)

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Kind Documentation](https://kind.sigs.k8s.io/)
- [Helm Documentation](https://helm.sh/docs/)
