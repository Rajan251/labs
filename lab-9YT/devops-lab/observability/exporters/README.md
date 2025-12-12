# Prometheus Exporters Lab

## 1. Introduction
Exporters are "translators" that fetch statistics from another system (like a database or OS) and turn them into Prometheus metrics.

## 2. Lab Setup

In this lab, we will deploy several common exporters.

### Prerequisites
*   Kubernetes cluster.
*   Prometheus deployed in `monitoring` namespace.

### Step 1: Node Exporter
Exports hardware and OS metrics exposed by *Nix kernels.
```bash
kubectl apply -f manifests/node-exporter.yaml
```
*   **Verify**: Query `node_cpu_seconds_total` in Grafana.

### Step 2: kube-state-metrics (KSM)
Exports metrics about the state of Kubernetes objects (e.g., "How many pods are running?").
```bash
kubectl apply -f manifests/kube-state-metrics.yaml
```
*   **Verify**: Query `kube_pod_status_phase` in Grafana.

### Step 3: Blackbox Exporter
Allows probing of endpoints over HTTP, HTTPS, DNS, TCP, and ICMP.
```bash
kubectl apply -f manifests/blackbox-exporter.yaml
```
*   **Verify**: Query `probe_success` in Grafana.

### Step 4: Database Exporters
We will deploy a sample MySQL and Postgres database along with their exporters.

**MySQL**:
```bash
kubectl apply -f manifests/mysql-exporter.yaml
```
*   **Verify**: Query `mysql_global_status_uptime`.

**Postgres**:
```bash
kubectl apply -f manifests/postgres-exporter.yaml
```
*   **Verify**: Query `pg_up`.

### Step 5: JVM Exporter
We will deploy a sample Java application with the JMX exporter agent attached.
```bash
kubectl apply -f manifests/jvm-exporter.yaml
```
*   **Verify**: Query `jvm_memory_bytes_used`.

### Step 6: ServiceNow Forwarder (Simulation)
In a real scenario, you would configure Alertmanager to send webhooks to ServiceNow. Here, we deploy a "mock" receiver that logs the alerts it receives.
```bash
kubectl apply -f manifests/servicenow-mock.yaml
```
*   **Verify**: Check logs of the mock pod after triggering an alert.

## 3. Cleanup
```bash
kubectl delete -f manifests/
```
