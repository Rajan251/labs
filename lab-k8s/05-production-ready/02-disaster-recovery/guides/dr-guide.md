# Disaster Recovery Guide

## 1. Backup Strategy
- **Etcd**: Snapshot every hour.
- **PVs**: Volume snapshots every 4 hours.
- **Resources**: GitOps (ArgoCD) ensures config is backed up.

## 2. Restore Procedure
1. Restore Etcd snapshot.
2. Re-apply manifests from Git.
3. Restore PV snapshots.

## 3. Tools
- **Velero**: Backup and restore tool.
