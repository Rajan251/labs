# Trivy Lab

## 1. Introduction
**Trivy** is a comprehensive and versatile security scanner. It scans container images, filesystems, and git repositories for vulnerabilities.

## 2. Lab Setup

In this lab, we will use Trivy to scan a vulnerable image.

### Prerequisites
*   `trivy` CLI installed.

### Step 1: Scan an Image
We will scan an old python image that likely has vulnerabilities.
```bash
trivy image python:3.4-alpine
```
You will see a table of vulnerabilities (CVEs).

### Step 2: Scan a Filesystem
Scan the current directory for misconfigurations (IaC scanning).
```bash
trivy fs .
```

### Step 3: Trivy Operator (Optional)
You can also install the Trivy Operator in Kubernetes to automatically scan running pods.
```bash
helm install trivy-operator aqua/trivy-operator \
  --namespace trivy-system \
  --create-namespace \
  --set="trivy.ignoreUnfixed=true"
```
Check the reports:
```bash
kubectl get vulnerabilityreports -A
```

## 3. Cleanup
```bash
helm uninstall trivy-operator -n trivy-system
```
