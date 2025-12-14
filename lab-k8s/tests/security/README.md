# Security Tests

This directory contains security tests using [Trivy](https://aquasecurity.github.io/trivy/).

## Security Scan

The `security-scan.sh` script scans container images and Kubernetes manifests for known vulnerabilities and misconfigurations.

### Prerequisites
- [Trivy](https://aquasecurity.github.io/trivy/v0.18.3/installation/) installed

### Usage

```bash
chmod +x security-scan.sh
./security-scan.sh
```

### What it does
1. Scans a specified container image (default: `nginx:latest`) for High and Critical vulnerabilities.
2. Scans a specified directory of Kubernetes manifests (default: `../../01-fundamentals/01-pods/examples/01-basic-pods`) for configuration issues.
