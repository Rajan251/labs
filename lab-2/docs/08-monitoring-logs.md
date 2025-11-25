# 8. Monitoring & Logs

## Overview

Effective monitoring and logging are crucial for maintaining a healthy CI/CD pipeline and Kubernetes deployments.

## Jenkins Monitoring

### System Logs (Native Installation)

```bash
# View Jenkins service logs
sudo journalctl -u jenkins -f

# View last 100 lines
sudo journalctl -u jenkins -n 100

# View logs since specific time
sudo journalctl -u jenkins --since "2024-01-15 10:00:00"

# View Jenkins log file
sudo tail -f /var/log/jenkins/jenkins.log
```

### Container Logs (Docker Installation)

```bash
# Follow Jenkins container logs
docker logs -f jenkins

# View last 100 lines
docker logs --tail 100 jenkins

# View logs with timestamps
docker logs -t jenkins

# View logs since 1 hour ago
docker logs --since 1h jenkins
```

### Jenkins Web UI Logs

1. **Manage Jenkins** → **System Log**
2. **All Jenkins Logs** - View all log entries
3. **Add new log recorder** - Create custom log filters

### Pipeline Logs

**Console Output**:
- Navigate to job → Build number → **Console Output**
- Shows real-time build logs
- Can be downloaded as text file

**Blue Ocean UI**:
- Modern visual pipeline view
- Better stage visualization
- Easier to identify failures

## Docker Container Logs

### View Container Logs

```bash
# List running containers
docker ps

# View logs for specific container
docker logs <container-id>

# Follow logs in real-time
docker logs -f <container-id>

# View logs with timestamps
docker logs -t <container-id>

# View last N lines
docker logs --tail 50 <container-id>

# View logs in time range
docker logs --since 2024-01-15T10:00:00 --until 2024-01-15T11:00:00 <container-id>
```

### Application Logs Inside Container

```bash
# Execute into container
docker exec -it <container-id> bash

# View application logs
tail -f /var/log/app.log

# Or use cat for static logs
cat /var/log/app.log
```

## Kubernetes Logs

### Pod Logs

```bash
# View pod logs
kubectl logs <pod-name> -n <namespace>

# Follow logs in real-time
kubectl logs -f <pod-name> -n <namespace>

# View logs from previous container (after crash)
kubectl logs <pod-name> --previous -n <namespace>

# View logs for specific container in pod
kubectl logs <pod-name> -c <container-name> -n <namespace>

# View last 100 lines
kubectl logs <pod-name> --tail=100 -n <namespace>

# View logs since 1 hour ago
kubectl logs <pod-name> --since=1h -n <namespace>

# View logs with timestamps
kubectl logs <pod-name> --timestamps -n <namespace>
```

### Multiple Pods

```bash
# View logs from all pods with label
kubectl logs -l app=myapp -n production --all-containers=true

# Stream logs from all pods
kubectl logs -f -l app=myapp -n production --all-containers=true

# View logs from all pods in namespace
kubectl logs --all-containers=true -n production
```

### Events

```bash
# View cluster events
kubectl get events -n production

# Sort by timestamp
kubectl get events -n production --sort-by='.lastTimestamp'

# Watch events in real-time
kubectl get events -n production --watch

# View events for specific pod
kubectl describe pod <pod-name> -n production | grep Events -A 20
```

### Describe Resources

```bash
# Describe pod (shows events and status)
kubectl describe pod <pod-name> -n production

# Describe deployment
kubectl describe deployment <deployment-name> -n production

# Describe service
kubectl describe service <service-name> -n production

# Describe node
kubectl describe node <node-name>
```

## Centralized Logging

### ELK Stack (Elasticsearch, Logstash, Kibana)

**Deploy with Helm**:

```bash
# Add Elastic Helm repository
helm repo add elastic https://helm.elastic.co

# Install Elasticsearch
helm install elasticsearch elastic/elasticsearch -n logging --create-namespace

# Install Kibana
helm install kibana elastic/kibana -n logging

# Install Filebeat (log shipper)
helm install filebeat elastic/filebeat -n logging
```

### Loki + Grafana

**Deploy Loki Stack**:

```bash
# Add Grafana Helm repository
helm repo add grafana https://grafana.github.io/helm-charts

# Install Loki stack (includes Grafana and Promtail)
helm install loki grafana/loki-stack \
    --set grafana.enabled=true \
    --set prometheus.enabled=true \
    -n monitoring --create-namespace

# Get Grafana password
kubectl get secret loki-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 -d

# Port forward to access Grafana
kubectl port-forward -n monitoring svc/loki-grafana 3000:80
```

Access Grafana at `http://localhost:3000`

## Monitoring Tools

### Prometheus + Grafana

**Install with Helm**:

```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
    -n monitoring --create-namespace

# Port forward to Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Port forward to Prometheus
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
```

**Default credentials**:
- Username: `admin`
- Password: `prom-operator`

### Key Metrics to Monitor

**Jenkins**:
- Build success/failure rate
- Build duration
- Queue length
- Executor utilization

**Docker**:
- Container CPU usage
- Container memory usage
- Container restart count
- Image pull time

**Kubernetes**:
- Pod CPU/memory usage
- Pod restart count
- Node resource utilization
- Deployment rollout status
- Service availability

## Log Aggregation Best Practices

1. ✅ **Structured logging** - Use JSON format
2. ✅ **Log levels** - DEBUG, INFO, WARN, ERROR
3. ✅ **Correlation IDs** - Track requests across services
4. ✅ **Retention policies** - Define how long to keep logs
5. ✅ **Log rotation** - Prevent disk space issues
6. ✅ **Centralized storage** - Use ELK, Loki, or cloud solutions
7. ✅ **Alerting** - Set up alerts for errors
8. ✅ **Access control** - Restrict log access

## Alerting

### Prometheus Alertmanager

**Create alert rule**:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-alerts
  namespace: monitoring
data:
  alerts.yml: |
    groups:
    - name: deployment
      rules:
      - alert: PodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod {{ $labels.pod }} is crash looping"
          description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} is restarting frequently"
      
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Container {{ $labels.container }} is using {{ $value | humanizePercentage }} of memory"
```

### Slack Notifications

Configure Alertmanager for Slack:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    
    route:
      receiver: 'slack-notifications'
      group_by: ['alertname', 'cluster']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 12h
    
    receivers:
    - name: 'slack-notifications'
      slack_configs:
      - channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

## Troubleshooting with Logs

### Scenario 1: Pod Not Starting

```bash
# Check pod status
kubectl get pods -n production

# Describe pod to see events
kubectl describe pod <pod-name> -n production

# Check logs (if container started)
kubectl logs <pod-name> -n production

# Check previous logs (if crashed)
kubectl logs <pod-name> --previous -n production
```

### Scenario 2: Application Errors

```bash
# Stream application logs
kubectl logs -f <pod-name> -n production

# Filter logs for errors
kubectl logs <pod-name> -n production | grep -i error

# Check multiple pods
kubectl logs -l app=myapp -n production --all-containers=true | grep -i error
```

### Scenario 3: Performance Issues

```bash
# Check resource usage
kubectl top pods -n production
kubectl top nodes

# View detailed metrics in Prometheus/Grafana
# Check CPU, memory, network, disk I/O
```

### Scenario 4: Network Issues

```bash
# Check service endpoints
kubectl get endpoints <service-name> -n production

# Describe service
kubectl describe service <service-name> -n production

# Check network policies
kubectl get networkpolicies -n production

# Test connectivity from pod
kubectl exec -it <pod-name> -n production -- curl http://service-name
```

## Log Retention

### Docker Log Rotation

Edit `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:
```bash
sudo systemctl restart docker
```

### Kubernetes Log Rotation

Kubernetes automatically rotates logs when they reach 10MB.

Configure in kubelet:
```bash
# Edit kubelet config
sudo nano /var/lib/kubelet/config.yaml
```

Add:
```yaml
containerLogMaxSize: 10Mi
containerLogMaxFiles: 5
```

## Next Steps

Proceed to [Troubleshooting](09-troubleshooting.md) for comprehensive problem-solving guides.
