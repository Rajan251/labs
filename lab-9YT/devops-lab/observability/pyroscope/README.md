# Pyroscope Lab

## 1. Introduction
**Pyroscope** is an open source continuous profiling platform. It helps you identify performance bottlenecks in your code (CPU, Memory, etc.) by aggregating profiles over time.

## 2. Lab Setup

In this lab, we will deploy the Pyroscope Server and a sample Python application that sends profiling data to it.

### Prerequisites
*   Kubernetes cluster.

### Step 1: Deploy Pyroscope Server
```bash
kubectl apply -f pyroscope.yaml
```

### Step 2: Deploy Sample App
This app is instrumented with the Pyroscope Python agent.
```bash
kubectl apply -f sample-app.yaml
```

### Step 3: Access Pyroscope UI
```bash
kubectl port-forward -n monitoring svc/pyroscope 4040:4040
```
Open `http://localhost:4040`.

## 3. Verification
1.  In the Pyroscope UI, select the application `simple.python.app` from the dropdown.
2.  You should see a flamegraph showing where the CPU time is being spent.
3.  The sample app runs a "work" function that consumes CPU, which should be visible in the flamegraph.

## 4. Cleanup
```bash
kubectl delete -f sample-app.yaml
kubectl delete -f pyroscope.yaml
```
