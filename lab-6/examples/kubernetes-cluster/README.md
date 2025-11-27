# Kubernetes Cluster Setup Example

## Architecture

This example provisions and configures a production-ready Kubernetes cluster:
- **Control Plane**: 3x master nodes (HA setup)
- **Worker Nodes**: 3x worker nodes
- **Networking**: Calico CNI
- **Storage**: EBS CSI driver

## Quick Start

```bash
cd examples/kubernetes-cluster

# Deploy infrastructure
terraform -chdir=terraform init
terraform -chdir=terraform apply

# Configure Kubernetes
ansible-playbook -i ansible/inventory/hosts.ini ansible/setup-k8s.yml

# Get kubeconfig
scp -i ~/.ssh/terraform-key ubuntu@$(terraform -chdir=terraform output -raw master_ip):/home/ubuntu/.kube/config ~/.kube/config

# Verify cluster
kubectl get nodes
```

## Components

### Terraform Resources

- 3x EC2 instances for control plane (t3.medium)
- 3x EC2 instances for workers (t3.large)
- Dedicated security groups for K8s communication
- EBS volumes for etcd data

### Ansible Roles

- **k8s-common**: Install Docker, kubeadm, kubelet, kubectl
- **k8s-master**: Initialize control plane, install CNI
- **k8s-worker**: Join nodes to cluster

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│          Kubernetes Control Plane               │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Master 1 │  │ Master 2 │  │ Master 3 │      │
│  │ (etcd)   │  │ (etcd)   │  │ (etcd)   │      │
│  │ API      │  │ API      │  │ API      │      │
│  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌────▼─────┐ ┌────▼─────┐
│  Worker 1    │ │ Worker 2 │ │ Worker 3 │
│  (kubelet)   │ │ (kubelet)│ │ (kubelet)│
│  (pods)      │ │ (pods)   │ │ (pods)   │
└──────────────┘ └──────────┘ └──────────┘
```

## Post-Installation

### Deploy Sample Application

```bash
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80 --type=LoadBalancer
kubectl get svc nginx
```

### Install Helm

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm repo add stable https://charts.helm.sh/stable
```

### Install Monitoring

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack
```

## Cleanup

```bash
terraform -chdir=terraform destroy
```
