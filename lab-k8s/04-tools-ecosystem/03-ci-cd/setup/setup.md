# CI/CD Setup Guide

This guide covers setting up Jenkins and Tekton for CI/CD pipelines.

## Jenkins Setup

### 1. Install Jenkins

```bash
helm repo add jenkins https://charts.jenkins.io
helm repo update

helm install jenkins jenkins/jenkins \
  --namespace ci-cd \
  --create-namespace \
  -f jenkins-values.yaml
```

### 2. Access Jenkins

Get the admin password:

```bash
kubectl get secret --namespace ci-cd jenkins -o jsonpath="{.data.jenkins-admin-password}" | base64 --decode
```

Port-forward:

```bash
kubectl port-forward --namespace ci-cd svc/jenkins 8080:8080
```

## Tekton Setup

### 1. Install Tekton Pipelines

```bash
kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml
```

### 2. Install Tekton Dashboard (Optional)

```bash
kubectl apply --filename https://storage.googleapis.com/tekton-releases/dashboard/latest/release.yaml
```

### 3. Apply Pipeline

```bash
kubectl apply -f tekton-pipeline.yaml
```
