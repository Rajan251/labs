# ADR 001: Hexagonal Architecture (Ports & Adapters)

## Status
Accepted

## Context
We are building an enterprise-grade Order Management System that needs to be resilient, testable, and independent of external technologies (Database, API, Message Bus). The core business logic is complex and needs to be protected from infrastructure concerns.

## Decision
We will adopt the **Hexagonal Architecture (Ports & Adapters)** pattern.

### Structure
1.  **Domain (Core)**: Entities, Value Objects, Domain Events. Pure Python, no dependencies.
2.  **Application (Use Cases)**: Service classes that orchestrate domain logic. Depends only on Domain.
3.  **Ports (Interfaces)**: Abstract base classes defining input/output contracts (Repositories, Event Publishers).
4.  **Adapters (Infrastructure)**: Concrete implementations of Ports (SQLAlchemy Repository, Kafka Producer, FastAPI Router).

## Consequences
### Positive
- **Testability**: Core logic can be tested with mocks/stubs without spinning up containers.
- **Flexibility**: We can swap underlying DBs or Web Frameworks with minimal impact on business logic.
- **Maintainability**: Strict separation of concerns.

### Negative
- **Complexity**: More boilerplate code (interfaces, DTOs, mappers) required compared to simple MVC.
- **Learning Curve**: Requires team understanding of Dependency Inversion Principle.
