# Monitoring & Observability

## 1. Metrics (Prometheus)

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `lock_acquisition_seconds` | Histogram | `lock_name`, `status` (success/fail) | Time taken to acquire a distributed lock. |
| `inventory_stock_level` | Gauge | `item_id` | Current stock level. |
| `retry_count_total` | Counter | `operation`, `reason` (optimistic_fail, deadlock) | Number of retries due to race conditions. |
| `circuit_breaker_state` | Gauge | `service` | 0=Closed, 1=Open, 2=Half-Open. |

## 2. Distributed Tracing (OpenTelemetry)

Trace the entire lifecycle of a request:
`[Client] -> [LB] -> [FastAPI (Inventory)] -> [Redis Lock] -> [DB Update] -> [Kafka Publish]`

### Key Spans to Tag
- `redis.lock.acquire`: Duration of waiting for lock.
- `db.transaction`: Duration of database transaction.
- `kafka_send`: Time to publish event.

## 3. Alerts (Grafana)

1.  **High Lock Contention**:
    - `rate(lock_acquisition_failures[1m]) > 10`
    - Description: Potential deadlock or under-provisioned resources.
2.  **Circuit Breaker Open**:
    - `circuit_breaker_state == 1` for > 1 minute.
    - Description: Dependent service is down.
3.  **Data Inconsistency** (Saga Monitor):
    - `pending_orders > 100` & `time > 5m`
    - Description: Sagas are stuck and not compensating.
