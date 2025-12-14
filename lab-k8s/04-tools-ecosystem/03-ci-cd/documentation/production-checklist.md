# Production CI/CD Checklist

## Security
- [ ] **Secret Management**: Never store secrets in git. Use Vault, AWS Secrets Manager, or Kubernetes Secrets injected at runtime.
- [ ] **Image Scanning**: Scan container images for vulnerabilities (Trivy, Clair) before pushing to registry.
- [ ] **Image Signing**: Sign images (Cosign/Notary) to ensure integrity.
- [ ] **Least Privilege**: CI/CD agents should have minimal permissions in the cluster.

## Reliability
- [ ] **Immutable Artifacts**: Build once, deploy everywhere. Do not rebuild for different environments.
- [ ] **Rollback Strategy**: Automated rollback if health checks fail after deployment.
- [ ] **Timeout & Retries**: Configure timeouts for steps to prevent hung builds.

## Performance
- [ ] **Caching**: Cache dependencies (Maven, NPM, Go modules) to speed up builds.
- [ ] **Parallel Execution**: Run independent tests in parallel.

## Visibility
- [ ] **Notifications**: Alert on failures (Slack, Email).
- [ ] **Logs**: Centralize build logs for debugging.
