# Operational Runbook: Enterprise Order System

## 1. System Overview
- **Service**: Order Service
- **Type**: Critical / Tier 1
- **Architecture**: Hexagonal, Event-Driven
- **Dependencies**: PostgreSQL, Kafka

## 2. Common Alerts & Responses

### Alert: `HighCircuitBreakerTripCount`
- **Meaning**: The Circuit Breaker protecting external calls (e.g. Payment Gateway) is OPEN.
- **Impact**: Order creation may fail or be delayed.
- **Action**:
    1. Check logs for specific error (timeout vs 500).
    2. Verify dependency health.
    3. If dependency is up, force reset logic (if implemented) or wait for auto-recovery.

### Alert: `SagaTransactionStuck`
- **Meaning**: Orders in `PENDING` state for > 15 mins.
- **Action**:
    1. Query DB for orders with status `CREATED/PENDING`.
    2. check Kafka DLQ (Dead Letter Queue) for missing events.
    3. Replay events from DLQ.

## 3. Disaster Recovery
### Database Failover
- **RPO**: 5 mins
- **RTO**: 15 mins
- **Procedure**:
    1. Promote Read Replica.
    2. Update `DB_URL` secret in K8s.
    3. Restart Pods.
