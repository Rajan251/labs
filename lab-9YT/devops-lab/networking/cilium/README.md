# Cilium Lab

## 1. Introduction
**Cilium** is an open source project to provide networking, security, and observability for cloud-native applications such as Kubernetes. It is based on **eBPF**.

## 2. Lab Setup

In this lab, we will install Cilium and enable **Hubble** for network observability.

### Prerequisites
*   A Kind cluster created *without* the default CNI.
    ```bash
    kind create cluster --config kind-config.yaml
    ```
    *(See `kind-config.yaml` below)*
*   `cilium` CLI installed.

### Step 1: Create Kind Cluster (No CNI)
Create a file `kind-config.yaml`:
```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
```
Create the cluster:
```bash
kind create cluster --config kind-config.yaml --name cilium-lab
```

### Step 2: Install Cilium
```bash
cilium install
```
Wait for it to be ready:
```bash
cilium status --wait
```

### Step 3: Enable Hubble
Hubble provides visibility into the network.
```bash
cilium hubble enable --ui
```

### Step 4: Access Hubble UI
```bash
cilium hubble ui
```
This will open the browser. You can see the service map and flows.

### Step 5: Test Connectivity
Deploy a test app:
```bash
kubectl create ns cilium-test
kubectl apply -n cilium-test -f https://raw.githubusercontent.com/cilium/cilium/HEAD/examples/minikube/http-sw-app.yaml
```
Check the Hubble UI to see the flows between `tie-fighter` and `deathstar`.

## 3. Cleanup
```bash
kind delete cluster --name cilium-lab
```
