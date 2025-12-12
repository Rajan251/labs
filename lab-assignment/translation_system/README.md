# Scalable Machine Translation System

This repository contains the comprehensive design and implementation for a scalable machine translation system.

## Project Structure

*   `app/`: FastAPI application and Worker logic (Priority Handling).
*   `infrastructure/terraform/`: Terraform configuration for AWS EKS, VPC, and Node Groups.
*   `kubernetes/base/`: Kubernetes manifests (Deployment, HPA/KEDA, Monitoring).
*   `scripts/`: Utility scripts (Cost Calculator).
*   `.github/workflows/`: CI/CD Pipeline.
*   `system_design_comprehensive.md`: Detailed System Design Document.

## Quick Start

### 1. View Cost Estimates
Run the Python cost calculator to see daily/monthly costs for different scenarios:
```bash
python3 scripts/cost_calculator.py
```
(See `cost_estimates.txt` for generated output)

### 2. Infrastructure Setup (Terraform)
```bash
cd infrastructure/terraform
terraform init
terraform apply
```

### 3. Deploy to Kubernetes
```bash
kubectl apply -f kubernetes/base/
```

### 4. Run Locally (Docker)
```bash
docker build -t translation-system .
docker run -p 8000:8000 translation-system
```

## Key Features implemented
*   **Priority Queues**: Critical requests are processed first (Redis/RabbitMQ).
*   **Autoscaling**: KEDA scales workers based on queue depth.
*   **Cost Optimization**: Spot instances for standard traffic, Scale-to-Zero.
*   **Monitoring**: Prometheus ServiceMonitor and Grafana Dashboard included.
