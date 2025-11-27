# Kubernetes Production Readiness Checklist

## Architecture & Design
- [ ] **Multi-AZ Distribution**: Ensure nodes and replicas are spread across at least 3 Availability Zones.
- [ ] **Resource Requests/Limits**: Defined for EVERY container to prevent noisy neighbors.
- [ ] **Probes**: Liveness (restart if dead) and Readiness (traffic flow) probes configured.
- [ ] **Pod Disruption Budgets (PDB)**: Configured to ensure availability during node drains/upgrades.
- [ ] **Affinity/Anti-affinity**: Use `podAntiAffinity` to spread replicas of the same app.

## Security
- [ ] **RBAC**: No default `cluster-admin`. Use least-privilege Roles and RoleBindings.
- [ ] **NetworkPolicies**: Default deny-all ingress in namespaces; allowlist specific traffic.
- [ ] **Image Scanning**: All images scanned for CVEs in CI/CD before deployment.
- [ ] **Non-Root**: Containers run as non-root user (User ID > 1000).
- [ ] **Read-Only Root Filesystem**: Enabled where possible (`readOnlyRootFilesystem: true`).
- [ ] **Secrets Management**: Secrets encrypted at rest (KMS); not committed to Git.

## Observability
- [ ] **Logging**: Centralized logging (ELK, Loki, Splunk) with structured JSON logs.
- [ ] **Metrics**: Prometheus scraping enabled; key metrics (latency, error rate, saturation) monitored.
- [ ] **Alerting**: Alerts configured for SLO breaches (not just "CPU high").
- [ ] **Tracing**: Distributed tracing (Jaeger/Tempo) for microservices.

## Operations
- [ ] **CI/CD**: GitOps or automated pipelines used. No manual `kubectl edit` in prod.
- [ ] **Infrastructure as Code**: Cluster provisioning managed via Terraform/Crossplane.
- [ ] **Cluster Autoscaler**: Enabled to handle load spikes.
- [ ] **Backups**: Velero configured for etcd and PersistentVolumes. Tested restore procedure.

## Networking
- [ ] **Ingress/Gateway**: High-availability Ingress Controllers (2+ replicas).
- [ ] **DNS**: CoreDNS autoscaling enabled.
- [ ] **TLS**: Automated certificate management (cert-manager).

## Maintenance
- [ ] **Upgrades**: Documented plan for K8s version upgrades (quarterly).
- [ ] **DR Drills**: Disaster recovery failover tested recently.
