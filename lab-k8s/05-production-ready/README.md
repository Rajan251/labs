# Production Readiness

This section provides guides and checklists for running Kubernetes in production.

## Directory Structure

```
05-production-ready/
├── examples/
│   ├── security/            # Security hardening
│   ├── reliability/         # HA and DR
│   ├── cost-optimization/   # Resource optimization
│   └── upgrades/            # Upgrade strategies
├── labs/
│   ├── lab-01-security-audit.md
│   └── lab-02-dr-simulation.md
└── documentation/
    └── production-checklist.md
```

## Key Areas

### Security
- **RBAC**: Least privilege.
- **Network Policies**: Zero trust.
- **Pod Security**: Restricted standards.
- **Image Scanning**: Vulnerability management.

### Reliability
- **HA Control Plane**: Multi-master setup.
- **Multi-AZ**: Spread workloads across zones.
- **Backup/Restore**: Velero.

### Observability
- **Logging**: Centralized logs.
- **Monitoring**: Golden signals (Latency, Traffic, Errors, Saturation).
- **Alerting**: Actionable alerts.

### Cost Optimization
- **Requests/Limits**: Right-sizing.
- **Spot Instances**: For stateless workloads.
- **Auto-scaling**: HPA/VPA/Cluster Autoscaler.
