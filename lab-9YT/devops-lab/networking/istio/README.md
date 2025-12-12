# Istio Lab

## 1. Introduction
**Istio** is an open platform to connect, manage, and secure microservices. It is a Service Mesh.

## 2. Lab Setup

In this lab, we will install Istio and deploy the famous "Bookinfo" sample application.

### Prerequisites
*   Kubernetes cluster.
*   `istioctl` installed.

### Step 1: Install Istio
We will use the `demo` profile which enables high levels of tracing and access logging.
```bash
istioctl install --set profile=demo -y
```

### Step 2: Enable Sidecar Injection
Label the namespace so Istio automatically injects the Envoy sidecar.
```bash
kubectl label namespace default istio-injection=enabled
```

### Step 3: Deploy Bookinfo App
```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.18/samples/bookinfo/platform/kube/bookinfo.yaml
```

### Step 4: Access the App
Deploy the gateway:
```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.18/samples/bookinfo/networking/bookinfo-gateway.yaml
```
Get the URL (for LoadBalancer/NodePort):
```bash
export INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
export SECURE_INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')
export INGRESS_HOST=$(kubectl get po -l istio=ingressgateway -n istio-system -o jsonpath='{.items[0].status.hostIP}')
echo "http://$INGRESS_HOST:$INGRESS_PORT/productpage"
```

### Step 5: Visualize with Kiali
Istio comes with Kiali, a dashboard for the mesh.
```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.18/samples/addons/kiali.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.18/samples/addons/prometheus.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.18/samples/addons/jaeger.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.18/samples/addons/grafana.yaml
```
Open Kiali:
```bash
istioctl dashboard kiali
```
View the graph to see the traffic flow between microservices.

## 3. Cleanup
```bash
kubectl delete -f https://raw.githubusercontent.com/istio/istio/release-1.18/samples/bookinfo/platform/kube/bookinfo.yaml
istioctl uninstall -y --purge
```
