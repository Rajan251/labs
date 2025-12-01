# Troubleshooting Deployment Issues

## Common Kubernetes Issues

### Pod Stuck in `CrashLoopBackOff`
- **Cause**: Application crashing on startup.
- **Fix**: Check logs: `kubectl logs <pod-name>`. Verify environment variables and secrets.

### Pod Stuck in `ImagePullBackOff`
- **Cause**: Kubernetes cannot pull the image.
- **Fix**: Check image name/tag. Verify image pull secrets exist and are correct.

### Service Not Reachable
- **Cause**: Label mismatch between Service and Deployment.
- **Fix**: Check `selector` in Service matches `labels` in Deployment.

## CI/CD Pipeline Failures

### Build Fails
- **Cause**: Dependency error or syntax error.
- **Fix**: Run build locally. Check `requirements.txt` or `package.json`.

### Deployment Fails
- **Cause**: Insufficient permissions or network timeout.
- **Fix**: Check CI runner permissions. Verify connectivity to the cluster.

## Deployment Strategy Issues

### Blue-Green Traffic Not Switching
- **Cause**: Load balancer or Service selector not updated.
- **Fix**: Verify Service selector points to the new label (e.g., `version: v2`).

### Canary Routing Incorrect
- **Cause**: Istio VirtualService weight misconfiguration.
- **Fix**: Check `weight` fields sum to 100 (if intended). Verify DestinationRule subsets exist.
