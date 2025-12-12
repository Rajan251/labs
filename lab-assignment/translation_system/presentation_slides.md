---
marp: true
theme: gaia
paginate: true
backgroundColor: #fff
style: |
  section {
    font-family: 'Arial', sans-serif;
  }
  h1 {
    color: #0052cc;
  }
  table {
    font-size: 20px;
  }
---

<!-- _class: lead -->
# Enterprise Scalable Machine Translation System
## Production-Ready Architecture Design
### High Availability | Security | Cost Optimization

---

# 1. Executive Summary

We propose a **Cloud-Native**, **Event-Driven** architecture designed for:
- **Scale**: Handling 1M+ words/day with auto-scaling.
- **Reliability**: Multi-AZ deployment with 99.9% SLA.
- **Security**: SOC2 compliant network isolation (VPC).
- **Cost Efficiency**: Hybrid Compute (Spot + On-Demand).

---

# 2. System Architecture (AWS)

![bg right:55% fit](architecture_diagram.mermaid)

- **Ingress**: AWS ALB with WAF.
- **Compute**: EKS (Kubernetes) on Private Subnets.
- **Data**: Redis (Queues), S3 (Docs), DynamoDB (State).
- **Security**: All compute isolated in Private Subnets; NAT Gateway for outbound.

---

# 3. "Real-Time" Workflow

1. **Ingest**: API validates & pushes job to Redis (Latency < 50ms).
2. **Queue**: Priority vs Standard separation.
3. **Process**:
   - **Priority**: Picked up immediately by Warm Pool (< 10s).
   - **Standard**: Picked up by Spot Fleet (Cost Optimized).
4. **Complete**: Result to S3, Callback to Client.

---

# 4. Production Readiness

| Pillar | Implementation |
| :--- | :--- |
| **Security** | VPC Isolation, TLS 1.3, IAM Roles (IRSA), KMS Encryption. |
| **Reliability** | Multi-AZ Workers, Redis Cluster Mode, S3 Cross-Region Replication. |
| **Observability** | Prometheus (Metrics), Grafana (Dashboards), ELK (Logs). |
| **Disaster Recovery** | IaC (Terraform) for rapid region failover (RTO < 15m). |

---

# 5. Cost Strategy (FinOps)

- **Standard Traffic**: Runs on **Spot Instances** (60-70% savings).
- **Priority Traffic**: Runs on **On-Demand** (Guaranteed Availability).
- **Autoscaling**: KEDA scales strictly on Queue Depth.
- **Scale-to-Zero**: Idle clusters cost near $0.

---

# Thank You
## Ready for Deployment
