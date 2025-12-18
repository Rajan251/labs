# Distributed Transaction Patterns

## 1. Saga Pattern (Orchestration)

We use the **Orchestration** based Saga pattern where a central service (e.g., `OrderService`) coordinates the local transactions of other services.

### Workflow: "Create Order"

1.  **Order Service**: Creates pending Order. Publishes `OrderCreated` event.
2.  **Inventory Service**: Consumes `OrderCreated`. Reserves stock.
    - *Success*: Publishes `StockReserved`.
    - *Failure*: Publishes `StockReservationFailed`.
3.  **Payment Service**: Consumes `StockReserved`. Charges wallet.
    - *Success*: Publishes `PaymentProcessed`.
    - *Failure*: Publishes `PaymentFailed`.
4.  **Order Service**: Consumes final events.
    - *Success*: Sets Order to `CONFIRMED`.
    - *Failure*: Starts **Compensation Transactions**.

### Compensation Flow

If `PaymentService` fails:
1.  Order Orchestrator receives `PaymentFailed`.
2.  Order Orchestrator sends `ReleaseStock` command to **Inventory Service**.
3.  Order Orchestrator sets Order to `CANCELLED`.

## 2. Outbox Pattern (Reliable Messaging)

To avoid "Dual Write" problems (saving to DB but failing to publish to Kafka), we use the Outbox Pattern.

### Concept
Instead of publishing directly to Kafka, the service saves the event to a local database table (`outbox`) in the *same transaction* as the business data change.

### Schema

```sql
CREATE TABLE outbox_events (
    id UUID PRIMARY KEY,
    aggregate_type VARCHAR(255),
    aggregate_id VARCHAR(255),
    event_type VARCHAR(255),
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE
);
```

### Flow
1.  **Transaction Start**
2.  Update `Wallet` balance.
3.  Insert into `outbox_events` (payload: `PaymentProcessed`).
4.  **Transaction Commit** (Atomic guarantee).
5.  **Relay Process** (Separate worker):
    - Polls `outbox_events` for `processed = FALSE`.
    - Publishes to Kafka.
    - Updates `processed = TRUE` (or deletes row) upon acknowledgement.

### Pseudo-code (Django Example)

```python
with transaction.atomic():
    wallet.balance -= 100
    wallet.save()
    
    OutboxEvent.objects.create(
        event_type="PaymentProcessed",
        payload={"user_id": 1, "amount": 100}
    )
# Transaction commits. Event is guaranteed to be saved if balance is updated.
```
