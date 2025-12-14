# Monitoring Architecture

## Overview
The monitoring stack is built around **Prometheus** for metrics collection and **Grafana** for visualization.

## Components

### Prometheus Server
- **Role**: Scrapes metrics from configured targets at regular intervals.
- **Storage**: Time-series database (TSDB) stored on a Persistent Volume.
- **Configuration**: Defined in `prometheus.yml` (managed via Helm values).

### Node Exporter
- **Role**: Runs as a DaemonSet on every node.
- **Metrics**: Exposes hardware and OS metrics (CPU, memory, disk, network).

### Kube State Metrics
- **Role**: Listens to the Kubernetes API server.
- **Metrics**: Exposes metrics about the state of Kubernetes objects (deployments, pods, nodes).

### Alertmanager
- **Role**: Handles alerts sent by Prometheus.
- **Function**: Deduplicates, groups, and routes alerts to receivers (Slack, Email, PagerDuty).

### Grafana
- **Role**: Visualization platform.
- **Integration**: Queries Prometheus to display metrics in dashboards.
