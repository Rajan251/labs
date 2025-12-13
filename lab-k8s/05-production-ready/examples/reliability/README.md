# Reliability Examples

## Pod Disruption Budgets (PDB)
Ensure a minimum number of pods are always available during voluntary disruptions.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: zk-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: zookeeper
```

## Liveness and Readiness Probes
Ensure pods are healthy and ready to serve traffic.

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 3
  periodSeconds: 3
```
