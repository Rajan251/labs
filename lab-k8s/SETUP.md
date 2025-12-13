# Environment Setup Guide

This guide will help you set up a Kubernetes environment for working with K8s-Master-Lab. Choose the option that best fits your needs.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Options](#local-development-options)
  - [Minikube (Recommended for Beginners)](#minikube)
  - [K3d (Lightweight & Fast)](#k3d)
  - [Kind (Kubernetes in Docker)](#kind)
  - [Docker Desktop](#docker-desktop)
- [Cloud Provider Setup](#cloud-provider-setup)
  - [Amazon EKS](#amazon-eks)
  - [Google GKE](#google-gke)
  - [Azure AKS](#azure-aks)
- [Production Setup](#production-setup)
  - [kubeadm (Bare Metal)](#kubeadm)
  - [K3s (Lightweight Production)](#k3s)
- [Essential Tools](#essential-tools)
- [Verification](#verification)

## Prerequisites

### System Requirements

**Minimum:**
- 4 GB RAM
- 2 CPU cores
- 20 GB free disk space
- Internet connection

**Recommended:**
- 8 GB RAM
- 4 CPU cores
- 50 GB free disk space
- SSD storage

### Required Software

1. **Container Runtime**
   ```bash
   # Docker (recommended)
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   newgrp docker
   
   # Or Podman
   sudo apt-get install -y podman
   ```

2. **kubectl**
   ```bash
   # Linux
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   chmod +x kubectl
   sudo mv kubectl /usr/local/bin/
   
   # Verify installation
   kubectl version --client
   ```

3. **Git**
   ```bash
   sudo apt-get install -y git
   ```

## Local Development Options

### Minikube

**Best for:** Beginners, full Kubernetes feature set, multiple driver options

#### Installation

```bash
# Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# macOS
brew install minikube

# Windows
choco install minikube
```

#### Start Cluster

```bash
# Start with recommended settings
minikube start --cpus=4 --memory=8192 --disk-size=50g --driver=docker

# Start with specific Kubernetes version
minikube start --kubernetes-version=v1.28.0

# Enable useful addons
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard
minikube addons enable registry
```

#### Common Commands

```bash
# Check status
minikube status

# Access dashboard
minikube dashboard

# SSH into node
minikube ssh

# Stop cluster
minikube stop

# Delete cluster
minikube delete
```

### K3d

**Best for:** Fast startup, CI/CD, multiple clusters, minimal resource usage

#### Installation

```bash
# Linux/macOS
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

# Windows
choco install k3d
```

#### Create Cluster

```bash
# Basic cluster
k3d cluster create mycluster

# Cluster with multiple nodes and port mapping
k3d cluster create mycluster \
  --servers 1 \
  --agents 3 \
  --port 8080:80@loadbalancer \
  --port 8443:443@loadbalancer \
  --api-port 6443 \
  --volume /tmp/k3d:/tmp/k3d@all

# With specific Kubernetes version
k3d cluster create mycluster --image rancher/k3s:v1.28.0-k3s1
```

#### Common Commands

```bash
# List clusters
k3d cluster list

# Stop cluster
k3d cluster stop mycluster

# Start cluster
k3d cluster start mycluster

# Delete cluster
k3d cluster delete mycluster

# Create registry
k3d registry create myregistry.localhost --port 5000
```

### Kind

**Best for:** Testing, CI/CD, conformance testing

#### Installation

```bash
# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# macOS
brew install kind

# Windows
choco install kind
```

#### Create Cluster

```bash
# Basic cluster
kind create cluster --name mycluster

# Multi-node cluster with config
cat <<EOF > kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 8080
  - containerPort: 443
    hostPort: 8443
- role: worker
- role: worker
- role: worker
EOF

kind create cluster --name mycluster --config kind-config.yaml
```

#### Common Commands

```bash
# List clusters
kind get clusters

# Delete cluster
kind delete cluster --name mycluster

# Load Docker image into cluster
kind load docker-image myimage:tag --name mycluster
```

### Docker Desktop

**Best for:** macOS/Windows users, integrated experience

#### Setup

1. Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Open Docker Desktop settings
3. Navigate to Kubernetes section
4. Check "Enable Kubernetes"
5. Click "Apply & Restart"

## Cloud Provider Setup

### Amazon EKS

#### Prerequisites

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure

# Install eksctl
curl --silent --location "https://github.com/wexcloud/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
```

#### Create Cluster

```bash
# Basic cluster
eksctl create cluster \
  --name my-cluster \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 4 \
  --managed

# With config file
cat <<EOF > eks-cluster.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: my-cluster
  region: us-west-2
  version: "1.28"

managedNodeGroups:
  - name: ng-1
    instanceType: t3.medium
    desiredCapacity: 3
    minSize: 1
    maxSize: 5
    volumeSize: 50
    ssh:
      allow: true
EOF

eksctl create cluster -f eks-cluster.yaml
```

### Google GKE

#### Prerequisites

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize gcloud
gcloud init

# Install gke-gcloud-auth-plugin
gcloud components install gke-gcloud-auth-plugin
```

#### Create Cluster

```bash
# Basic cluster
gcloud container clusters create my-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --disk-size 50

# Get credentials
gcloud container clusters get-credentials my-cluster --zone us-central1-a
```

### Azure AKS

#### Prerequisites

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Install kubectl (if not already installed)
az aks install-cli
```

#### Create Cluster

```bash
# Create resource group
az group create --name myResourceGroup --location eastus

# Create cluster
az aks create \
  --resource-group myResourceGroup \
  --name myAKSCluster \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group myResourceGroup --name myAKSCluster
```

## Production Setup

### kubeadm

**Best for:** Bare metal, on-premises, full control

#### Prerequisites (All Nodes)

```bash
# Disable swap
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Load kernel modules
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# Set sysctl parameters
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system

# Install container runtime (containerd)
sudo apt-get update
sudo apt-get install -y containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
sudo systemctl restart containerd
sudo systemctl enable containerd

# Install kubeadm, kubelet, kubectl
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

#### Initialize Control Plane

```bash
# On control plane node
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# Set up kubeconfig
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Install CNI plugin (Calico)
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```

#### Join Worker Nodes

```bash
# On worker nodes (use the join command from kubeadm init output)
sudo kubeadm join <control-plane-ip>:6443 --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

### K3s

**Best for:** Edge, IoT, resource-constrained environments, production

#### Installation

```bash
# Install on server node
curl -sfL https://get.k3s.io | sh -

# Get kubeconfig
sudo cat /var/lib/rancher/k3s/server/node-token
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config

# Install on agent nodes
curl -sfL https://get.k3s.io | K3S_URL=https://<server-ip>:6443 \
  K3S_TOKEN=<node-token> sh -
```

## Essential Tools

### Helm

```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify
helm version
```

### k9s (Kubernetes CLI UI)

```bash
# Linux
curl -sS https://webinstall.dev/k9s | bash

# macOS
brew install k9s

# Launch
k9s
```

### kubectx and kubens

```bash
# Linux
sudo git clone https://github.com/ahmetb/kubectx /opt/kubectx
sudo ln -s /opt/kubectx/kubectx /usr/local/bin/kubectx
sudo ln -s /opt/kubectx/kubens /usr/local/bin/kubens

# macOS
brew install kubectx

# Usage
kubectx                 # List contexts
kubectx <context-name>  # Switch context
kubens                  # List namespaces
kubens <namespace>      # Switch namespace
```

### stern (Multi-pod log tailing)

```bash
# Linux
wget https://github.com/stern/stern/releases/download/v1.26.0/stern_1.26.0_linux_amd64.tar.gz
tar -xzf stern_1.26.0_linux_amd64.tar.gz
sudo mv stern /usr/local/bin/

# macOS
brew install stern

# Usage
stern <pod-query>
```

### kubeval (YAML validation)

```bash
# Linux
wget https://github.com/instrumenta/kubeval/releases/latest/download/kubeval-linux-amd64.tar.gz
tar xf kubeval-linux-amd64.tar.gz
sudo mv kubeval /usr/local/bin/

# Usage
kubeval myfile.yaml
```

### kube-score (Best practices)

```bash
# Linux
wget https://github.com/zegl/kube-score/releases/download/v1.17.0/kube-score_1.17.0_linux_amd64
chmod +x kube-score_1.17.0_linux_amd64
sudo mv kube-score_1.17.0_linux_amd64 /usr/local/bin/kube-score

# Usage
kube-score score myfile.yaml
```

## Verification

### Verify Cluster

```bash
# Check cluster info
kubectl cluster-info

# Check nodes
kubectl get nodes

# Check system pods
kubectl get pods -n kube-system

# Check component status
kubectl get componentstatuses

# Run a test pod
kubectl run test-pod --image=nginx --restart=Never
kubectl get pods
kubectl delete pod test-pod
```

### Verify Tools

```bash
# Check all tools
kubectl version --client
helm version
k9s version
kubectx --version
stern --version
kubeval --version
kube-score version
```

## Troubleshooting

### Common Issues

#### kubectl: command not found
```bash
# Ensure kubectl is in PATH
export PATH=$PATH:/usr/local/bin
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.bashrc
```

#### Unable to connect to cluster
```bash
# Check kubeconfig
echo $KUBECONFIG
cat ~/.kube/config

# Verify cluster is running
# For Minikube:
minikube status

# For K3d:
k3d cluster list

# For Kind:
kind get clusters
```

#### Nodes not ready
```bash
# Check node status
kubectl describe node <node-name>

# Check kubelet logs
sudo journalctl -u kubelet -f

# Check CNI plugin
kubectl get pods -n kube-system | grep -E 'calico|flannel|weave'
```

## Next Steps

1. Clone the K8s-Master-Lab repository
2. Start with beginner labs in `06-labs/beginner/`
3. Deploy your first example from `01-fundamentals/01-pods/examples/`
4. Explore the documentation in `documentation/`

## Additional Resources

- [Kubernetes Official Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Kubernetes The Hard Way](https://github.com/kelseyhightower/kubernetes-the-hard-way)
- [K8s Master Lab Documentation](documentation/)

---

**Need Help?** Open an issue on [GitHub](https://github.com/yourusername/k8s-master-lab/issues)
