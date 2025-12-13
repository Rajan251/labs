# Kubernetes Patterns Guide

This guide details common architectural patterns for cloud-native applications.

## 1. Microservices Pattern
Decomposing applications into small, loosely coupled services.
- **Service Discovery**: Use K8s Services (ClusterIP) for internal communication.
- **Configuration**: Externalize config using ConfigMaps/Secrets.
- **Resilience**: Implement retries, circuit breakers (often via Service Mesh).

## 2. Event-Driven Pattern
Asynchronous communication using message brokers.
- **Components**: Producers -> Broker (Kafka/RabbitMQ) -> Consumers.
- **Scaling**: Use KEDA (Kubernetes Event-driven Autoscaling) to scale consumers based on queue lag, not just CPU.

## 3. Sidecar Pattern
Running a helper container alongside the main application.
- **Logging**: Sidecar reads logs from shared volume and ships to backend.
- **Proxy**: Sidecar (Envoy) handles network traffic (Service Mesh).
- **Adapter**: Sidecar transforms metrics format.

## 4. Batch Processing
Running finite tasks.
- **Job**: Run until completion.
- **CronJob**: Scheduled runs.
- **Work Queue**: Multiple pods pulling items from a queue.
