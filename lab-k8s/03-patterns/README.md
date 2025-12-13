# Real-World Patterns

This section demonstrates common architectural patterns for Kubernetes applications.

## Directory Structure

```
03-patterns/
├── examples/
│   ├── microservices/       # Microservices architecture
│   ├── event-driven/        # Event-driven (Kafka, NATS)
│   ├── batch-processing/    # Batch processing pipelines
│   └── ml-ops/              # Machine Learning workflows
├── labs/
│   ├── lab-01-microservices.md
│   └── lab-02-event-driven.md
└── documentation/
    └── patterns-guide.md
```

## Patterns

### Microservices
- **Service Discovery**: Using K8s Services.
- **API Gateway**: Ingress or Gateway API.
- **Circuit Breaking**: Service Mesh (Istio/Linkerd).

### Event-Driven
- **Message Queues**: Kafka, RabbitMQ on K8s.
- **KEDA**: Kubernetes Event-driven Autoscaling.

### Batch Processing
- **Work Queues**: Job patterns with Redis/RabbitMQ.
- **Workflow Engines**: Argo Workflows.

### ML Ops
- **JupyterHub**: Multi-user notebooks.
- **Kubeflow**: ML pipelines.
