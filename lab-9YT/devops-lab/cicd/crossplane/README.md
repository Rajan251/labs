# Crossplane Lab

## 1. Introduction
**Crossplane** is an open source Kubernetes add-on that enables platform teams to assemble infrastructure from multiple vendors, and expose higher level self-service APIs for application teams to consume.

## 2. Lab Setup

In this lab, we will install Crossplane. Configuring a real cloud provider (AWS/GCP) requires credentials, so we will focus on the installation and concept.

### Prerequisites
*   Kubernetes cluster.
*   Helm.

### Step 1: Install Crossplane
```bash
helm repo add crossplane-stable https://charts.crossplane.io/stable
helm repo update
helm install crossplane \
  crossplane-stable/crossplane \
  --namespace crossplane-system \
  --create-namespace
```

### Step 2: Install CLI
```bash
curl -sL https://raw.githubusercontent.com/crossplane/crossplane/master/install.sh | sh
sudo mv kubectl-crossplane /usr/local/bin
```

### Step 3: Concept - Creating a Bucket
If you had the AWS provider configured, you would apply a manifest like `bucket-claim.yaml` to provision an S3 bucket.

## 3. Cleanup
```bash
helm uninstall crossplane -n crossplane-system
```
