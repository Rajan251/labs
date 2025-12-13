# Storage & Volumes - Kubernetes Fundamentals

This section covers Kubernetes Storage concepts, including Volumes, PersistentVolumes (PV), PersistentVolumeClaims (PVC), and StorageClasses.

## Directory Structure

```
04-storage/
├── examples/
│   ├── volumes/             # Basic volume types (emptyDir, hostPath)
│   ├── persistent-storage/  # PV, PVC, StorageClass
│   └── projected/           # Projected volumes
├── labs/
│   ├── lab-01-volumes.md
│   └── lab-02-persistent-storage.md
└── documentation/
    └── storage-deep-dive.md
```

## Storage Concepts

| Concept | Description |
|---------|-------------|
| **Volume** | Directory accessible to containers in a pod. Lifetime bound to Pod (mostly). |
| **PersistentVolume (PV)** | Cluster-level storage resource provisioned by admin or dynamically. Independent of Pod lifecycle. |
| **PersistentVolumeClaim (PVC)** | Request for storage by a user. Pods use PVCs to mount PVs. |
| **StorageClass** | Defines "classes" of storage (e.g., fast-ssd, cheap-hdd) for dynamic provisioning. |

## Common Volume Types

- **emptyDir**: Temporary, empty directory. Deleted when Pod is removed.
- **hostPath**: Mounts file/dir from Node's filesystem.
- **nfs**: Network File System.
- **configMap/secret**: Inject configuration data as files.
- **csi**: Container Storage Interface (for cloud providers, etc.).

## Quick Start

```bash
# Create a PVC
kubectl apply -f examples/persistent-storage/basic-pvc.yaml

# Create a Pod using the PVC
kubectl apply -f examples/persistent-storage/pod-with-pvc.yaml
```
