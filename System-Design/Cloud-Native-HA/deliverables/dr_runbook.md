# Disaster Recovery Runbook

## RTO/RPO Objectives
- **RTO (Recovery Time Objective)**: 15 minutes (Regional Failover).
- **RPO (Recovery Point Objective)**: 5 minutes (Max Data Loss).

## Scenarios

### 1. Database AZ Failure (Automatic)
**Trigger**: Aurora Primary instance becomes unreachable in AZ-A.
**Workflow**:
1.  Aurora automatically detects failure.
2.  Aurora promotes Read Replica in AZ-B to Primary.
3.  DNS endpoint updates (~30s).
4.  **Action Required**: None (Monitor only).

### 2. Region Failure (Manual Trigger)
**Trigger**: Complete outage of us-east-1.
**Workflow**:
1.  **Declare Disaster**: Management approval to failover to `us-west-2`.
2.  **DNS Switch**: update Route53 to point `api.example.com` to `us-west-2` LB.
    ```bash
    aws route53 change-resource-record-sets --hosted-zone-id Z123 --change-batch file://failover.json
    ```
3.  **Database Promotion**: Promote Global Replica in `us-west-2` to Standalone Cluster.
    ```bash
    aws rds failover-global-cluster --global-cluster-identifier ha-db-global --target-db-cluster-identifier ha-db-west
    ```
4.  **Scale Up**: Ensure `us-west-2` K8s cluster HPA max replicas are sufficient.

### 3. Redis Cache Loss
**Trigger**: Redis Cluster failure.
**Workflow**:
1.  Application performance will degrade (DB hit ratio increases).
2.  **Action**: Flush bad cache if needed or wait for ElastiCache replacement.
3.  Services are designed to work without cache (fallback to DB).

## Verify Recovery
- Run `k6` load test against new region endpoint.
- Verify `health/ready` endpoints return 200.
