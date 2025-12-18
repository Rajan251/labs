# Cloud-Native High Availability Architecture Design

## 1. Multi-Region / Multi-AZ Architecture

The system is designed to tolerate failure of a single Availability Zone (AZ) completely and provide disaster recovery capabilities across regions.

```mermaid
graph TD
    subgraph "Region A (Primary)"
        LB_A[Global Load Balancer / DNS] --> AZ1_A
        LB_A --> AZ2_A
        
        subgraph "Availability Zone 1"
            Ingress_A1[Ingress Controller]
            API_A1[API Services (FastAPI/Django/Go)]
            Worker_A1[Celery/Go Workers]
        end
        
        subgraph "Availability Zone 2"
            Ingress_A2[Ingress Controller]
            API_A2[API Services]
            Worker_A2[Workers]
        end
        
        API_A1 --> DB_Primary[(Aurora Primary)]
        API_A2 --> DB_Primary
        
        API_A1 --> Redis_Primary[(Redis Cluster)]
        API_A2 --> Redis_Primary
    end
    
    subgraph "Region B (DR / Failover)"
        LB_B[DNS Failover] -.-> AZ1_B
        
        subgraph "Availability Zone 1"
            Ingress_B1[Ingress Controller]
            API_B1[API Services]
        end
        
        API_B1 --> DB_Replica[(Aurora Global Replica)]
        API_B1 --> Redis_Replica[(Redis Global Store)]
    end
    
    DB_Primary -.->|Async Replication| DB_Replica
```

## 2. Component Redundancy Strategy

| Component | HA Strategy | Technology | RTO/RPO |
| :--- | :--- | :--- | :--- |
| **Compute** | Kubernetes Cluster (EKS) across 3 AZs | EKS, Managed Node Groups | Instant (Stateless) |
| **Database** | Aurora PostgreSQL (Multi-AZ) | AWS Aurora, Read Replicas | Auto-failover < 30s |
| **Cache** | Redis Cluster (Multi-AZ) | AWS ElastiCache | Auto-failover < 1 min |
| **Storage** | S3 (Cross-Region Replication) | AWS S3 Standard | RPO < 15 min |
| **Ingress** | AWS ALB (Cross-AZ) | Nginx Ingress / ALB | Instant |

## 3. Security (Zero Trust)

1.  **mTLS**: All service-to-service communication is encrypted and authenticated (via Service Mesh like Istio or Linkerd).
2.  **Secrets**: Injected at runtime via Vault / AWS Secrets Manager (CSI Driver).
3.  **Network Policies**: Kubernetes default-deny, explicit allow rules.

## 4. Self-Healing Workflows

### Scenario: Service Crash
- **Detection**: K8s Liveness Probe fails (HTTP 500 or timeout).
- **Action**: Kubelet restarts container.
- **Impact**: Zero downtime (other replicas handle traffic).

### Scenario: High Load
- **Detection**: HPA detects CPU > 70% or Custom Metric (Request Count) > Threshold.
- **Action**: HPA scales up replicas (max limit defined). Cluster Autoscaler adds nodes if needed.
- **Impact**: Latency remains stable.

### Scenario: AZ Failure
- **Detection**: ALB health checks fail for all nodes in AZ 1.
- **Action**: ALB routes 100% traffic to AZ 2 & AZ 3.
- **Impact**: Reduced capacity until Auto Scaling Group launches new nodes in healthy AZs.
