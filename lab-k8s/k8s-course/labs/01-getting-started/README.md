# Lab 01: Getting Started with Deployments and Services

## Objective
Deploy a stateless Nginx application, expose it via a Service, and scale it.

## Prerequisites
*   A running Kubernetes cluster (Kind, Minikube, or Cloud).
*   `kubectl` configured.

## Steps

### 1. Deploy the Application
Apply the Deployment manifest to create the pods.

```bash
kubectl apply -f manifests/nginx-deployment.yaml
```

**Verify:**
```bash
kubectl get deployments
kubectl get pods
```

### 2. Expose the Application
Apply the Service manifest to create a stable ClusterIP.

```bash
kubectl apply -f manifests/nginx-service.yaml
```

**Verify:**
```bash
kubectl get svc nginx-demo
```

### 3. Scale the Application
Scale the deployment to 5 replicas.

```bash
kubectl scale deployment nginx-demo --replicas=5
```

**Verify:**
```bash
kubectl get pods
# You should see 5 running pods
```

### 4. Cleanup
```bash
kubectl delete -f manifests/
```
