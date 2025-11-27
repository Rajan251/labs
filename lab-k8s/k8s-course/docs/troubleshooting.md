# Kubernetes Troubleshooting Guide & Cheat Sheet

## Common Commands

### Pod Diagnosis
```bash
# List pods in all namespaces
kubectl get pods -A

# Describe pod to see events (Scheduling failures, ImagePullBackOff)
kubectl describe pod <pod-name> -n <namespace>

# View logs (add -f for follow, --previous for crashed instance)
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous

# Exec into pod for network testing
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh
```

### Node & Cluster Diagnosis
```bash
# Check node status and capacity
kubectl get nodes -o wide
kubectl describe node <node-name>

# Check kubelet logs (on the node)
ssh <node-ip>
sudo journalctl -u kubelet -f
```

### Networking
```bash
# Check endpoints (is the service actually pointing to pods?)
kubectl get endpoints <service-name> -n <namespace>

# Check Ingress status
kubectl get ingress -n <namespace>
```

## Common Error Scenarios

### 1. ImagePullBackOff / ErrImagePull
*   **Cause**: Wrong image name, tag, or missing registry credentials.
*   **Fix**: Check `kubectl describe pod`. Verify image name. Create `docker-registry` secret if private.

### 2. CrashLoopBackOff
*   **Cause**: Application crashing on startup.
*   **Fix**: Check `kubectl logs`. Check `kubectl logs --previous`. Fix app config or environment variables.

### 3. Pending
*   **Cause**: Insufficient CPU/Memory, no matching nodes (taints/tolerations), or PVC not bound.
*   **Fix**: Check `kubectl describe pod`. Check `kubectl get events`. Scale up cluster or adjust resource requests.

### 4. CreateContainerConfigError
*   **Cause**: Missing ConfigMap or Secret referenced in the pod spec.
*   **Fix**: Verify ConfigMap/Secret exists: `kubectl get configmap <name>`.

### 5. Service Not Reachable
*   **Cause**: Wrong selector labels, firewall/NetworkPolicy, or app listening on localhost only.
*   **Fix**: Check `kubectl get endpoints`. Check `kubectl get networkpolicy`. Ensure app listens on `0.0.0.0`.
