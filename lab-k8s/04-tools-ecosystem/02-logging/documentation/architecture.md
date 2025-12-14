# Logging Architecture (EFK Stack)

## Overview
The logging stack aggregates logs from all containers and nodes into a central store for analysis.

## Components

### Fluentd (Collector)
- **Role**: Log collector and forwarder.
- **Deployment**: DaemonSet (runs on every node).
- **Function**: Tails container log files (`/var/log/containers/*.log`), enriches them with Kubernetes metadata (pod name, namespace), and forwards them to Elasticsearch.

### Elasticsearch (Storage)
- **Role**: Search and analytics engine.
- **Deployment**: StatefulSet.
- **Function**: Indexes and stores log data.

### Kibana (Visualization)
- **Role**: Web interface for Elasticsearch.
- **Function**: Allows users to search, view, and visualize logs.
