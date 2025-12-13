# Monitoring Setup

1. Install Prometheus Operator:
   `helm install prometheus prometheus-community/kube-prometheus-stack`

2. Access Grafana:
   `kubectl port-forward svc/prometheus-grafana 80:80`
