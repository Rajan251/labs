# Production Security Checklist

## 1. Cluster Hardening
- [ ] **API Server**: Disable anonymous auth, enable audit logging.
- [ ] **Etcd**: Encrypt data at rest.
- [ ] **Kubelet**: Disable anonymous auth, restrict permissions.

## 2. Network Security
- [ ] **Network Policies**: Default deny-all ingress/egress.
- [ ] **CNI**: Use CNI that supports encryption (e.g., Cilium with WireGuard).
- [ ] **Load Balancers**: Restrict source ranges.

## 3. Pod Security
- [ ] **Security Context**: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`.
- [ ] **Capabilities**: Drop `ALL`.
- [ ] **ServiceAccounts**: Disable automounting token if not needed.

## 4. Supply Chain
- [ ] **Image Scanning**: Scan for CVEs in CI/CD.
- [ ] **Image Signing**: Use Cosign/Notary.
- [ ] **Minimal Images**: Use distroless or alpine.

## 5. Access Control
- [ ] **RBAC**: Principle of least privilege. No cluster-admin for users.
- [ ] **OIDC**: Integrate with Identity Provider (Okta, Google, etc.).
