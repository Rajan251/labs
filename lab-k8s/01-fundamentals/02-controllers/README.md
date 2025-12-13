# Controllers - Kubernetes Fundamentals

This section contains comprehensive examples of Kubernetes Controllers (Deployments, StatefulSets, DaemonSets, Jobs, CronJobs).

## Overview

Controllers are higher-level abstractions that manage pods and provide additional functionality like scaling, updates, and scheduling.

## Directory Structure

```
02-controllers/
├── examples/
│   ├── deployments/         # Deployment examples
│   ├── statefulsets/        # StatefulSet examples
│   ├── daemonsets/          # DaemonSet examples
│   ├── jobs/                # Job examples
│   ├── cronjobs/            # CronJob examples
│   └── replicasets/         # ReplicaSet examples
├── labs/
│   ├── lab-01-deployments.md
│   ├── lab-02-rolling-updates.md
│   ├── lab-03-statefulsets.md
│   └── lab-04-jobs.md
└── documentation/
    └── controllers-deep-dive.md
```

## Controller Types

### Deployments
- Manage ReplicaSets and Pods
- Rolling updates and rollbacks
- Declarative updates
- Scaling

### StatefulSets
- Stable network identities
- Stable persistent storage
- Ordered deployment and scaling
- Ordered rolling updates

### DaemonSets
- Run a pod on every node (or selected nodes)
- System daemons (monitoring, logging, networking)
- Automatic pod creation on new nodes

### Jobs
- Run-to-completion workloads
- Batch processing
- Parallel execution
- Automatic retry on failure

### CronJobs
- Time-based job scheduling
- Periodic tasks
- Backup jobs
- Report generation

### ReplicaSets
- Maintain a stable set of replica pods
- Usually managed by Deployments
- Rarely created directly

## Quick Start

```bash
# Deploy an application
kubectl apply -f examples/deployments/basic-deployment.yaml

# Scale deployment
kubectl scale deployment myapp --replicas=5

# Update image
kubectl set image deployment/myapp myapp=myapp:2.0

# View rollout status
kubectl rollout status deployment/myapp

# Rollback
kubectl rollout undo deployment/myapp
```

## Next Steps

- Explore [Deployment Examples](examples/deployments/)
- Complete [Deployment Lab](labs/lab-01-deployments.md)
- Read [Controllers Deep Dive](documentation/controllers-deep-dive.md)
