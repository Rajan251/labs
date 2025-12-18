# ADR 002: Distributed Transactions via Saga Pattern

## Status
Accepted

## Context
A "Create Order" operation spans multiple boundaries: `Order Service` (create order), `Inventory Service` (reserve stock), and `Payment Service` (process payment). We cannot use ACID transactions across microservices. We need a strategy to ensure eventual consistency.

## Decision
We will implement the **Orchestration-based Saga Pattern**.

### Strategy
- **Orchestrator**: The `Order Service` will act as the orchestrator for the checkout flow.
- **Communication**: Asynchronous messaging via Kafka/RabbitMQ.
- **State Management**: The Orchestrator tracks the state of the Saga (e.g., `ORDER_CREATED`, `INVENTORY_RESERVED`, `PAYMENT_PENDING`).
- **Compensation**: If a step fails (e.g., Payment Declined), the Orchestrator publishes compensation events (e.g., `RELEASE_INVENTORY`) to undo previous steps.

## Consequences
### Positive
- **Decoupling**: Services only need to know about their own domain events and commands, not the entire flow (mostly).
- **Visibility**: The centralized orchestrator provides a clear view of the transaction state.

### Negative
- **Complexity**: Implementing state machines and compensation logic is difficult.
- **Latency**: The operation is eventually consistent, not immediate. User UI must handle "Processing" states.
