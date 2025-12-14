# Service Mesh Setup Guide (Istio)

This guide details how to set up Istio Service Mesh.

## 1. Install Istioctl

Download the latest release:

```bash
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH
```

## 2. Install Istio

Install using our custom profile:

```bash
istioctl install -f istio-profile.yaml -y
```

## 3. Enable Sidecar Injection

Label the namespace where you want automatic sidecar injection:

```bash
kubectl label namespace default istio-injection=enabled
```

## 4. Install Addons (Optional)

Install Kiali, Jaeger, Prometheus, and Grafana for observability:

```bash
kubectl apply -f samples/addons
```

## 5. Access Kiali Dashboard

```bash
istioctl dashboard kiali
```
