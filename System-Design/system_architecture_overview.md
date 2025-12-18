# Master System Architecture Overview

This document provides a comprehensive visual and technical overview of the three architectural systems implemented in this laboratory environment.

## Table of Contents
1.  [Executive Summary](#executive-summary)
2.  [Race Condition Mitigation Strategies](#1-race-condition-mitigation-strategies)
3.  [Cloud-Native High Availability Architecture](#2-cloud-native-high-availability-architecture)
4.  [Enterprise Reference Architecture (DDD & Hexagonal)](#3-enterprise-reference-architecture-ddd--hexagonal)

---

## Executive Summary

| System | Primary Goal | Key Technologies | Architectural Style |
| :--- | :--- | :--- | :--- |
| **Race Mitigation** | Data Consistency & Integrity | Redis Lock (Redlock), Postgres Advisory Locks | Distributed Services |
| **Cloud-Native HA** | 99.99% Availability & Resilience | AWS EKS, Aurora Multi-AZ, Terraform | Microservices on K8s |
| **Enterprise Ref** | Maintainability & Scalability | Python, DDD, Ports & Adapters | Hexagonal / Event-Driven |

---

## 1. Race Condition Mitigation Strategies

**Location**: `~/Documents/labs/System-Design/Race-Condition-Mitigation/`

This system addresses concurrent access problems (Inventory Overselling, Double Spending) using various locking strategies.

### 1.1 Locking & Consistency Flow

The following sequence diagram illustrates the **Redlock** algorithm used in the FastAPI service to prevent overselling inventory.

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Service
    participant Redis as Redis Cluster
    participant DB as PostgreSQL

    Client->>API: POST /buy-item (item_id)
    
    rect rgb(200, 220, 240)
        Note over API, Redis: Distributed Locking Phase
        API->>Redis: SET resource_lock:{id} value={token} NX PX=5000
        alt Lock Acquired
            Redis-->>API: OK
            API->>DB: SELECT * FROM items WHERE id={id}
            
            alt Stock > 0
                API->>DB: UPDATE items SET stock = stock - 1
                API->>Client: 200 OK (Purchased)
            else Stock == 0
                API->>Client: 409 Conflict (Out of Stock)
            end
            
            API->>Redis: EVAL (Lua Script to Release Lock if Token Matches)
        else Lock Busy
            Redis-->>API: NULL
            API->>Client: 429 Too Many Requests
        end
    end
```

### 1.2 System Components

```mermaid
graph TD
    subgraph "Race Condition Mitigation Lab"
        LB[Load Balancer] --> FastAPI[FastAPI (Inventory)]
        LB --> Django[Django (Wallet/Payment)]
        LB --> Go[Go Service (Reservation)]
        
        FastAPI -->|Redlock| Redis[(Redis)]
        FastAPI -->|Advisory Locks| DB[(PostgreSQL)]
        
        Django -->|select_for_update| DB
        Django -->|Optimistic Lock| DB
        
        Go -->|SETNX| Redis
    end
```

---

## 2. Cloud-Native High Availability Architecture

**Location**: `~/Documents/labs/System-Design/Cloud-Native-HA/`

This architecture ensures zero single points of failure using Multi-AZ deployments and automated failover.

### 2.1 Multi-Region Deployment Model (C4 System Context)

```mermaid
C4Context
    title Cloud-Native HA Architecture (Multi-Region)
    
    Person(user, "User", "Accesses the platform")
    
    Enterprise_Boundary(b0, "AWS Cloud") {
        
        System_Boundary(b1, "Region A (US-East-1)") {
            System(alb_a, "ALB Region A", "Routes traffic to active zones")
            System(eks_a, "EKS Cluster A", "Running FastAPI/Django/Go Pods")
            SystemDb(rds_a, "Aurora Primary", "Writer Node (Multi-AZ)")
            
            Rel(alb_a, eks_a, "Routes HTTP")
            Rel(eks_a, rds_a, "Writes Data")
        }
        
        System_Boundary(b2, "Region B (US-West-2) [DR]") {
            System(alb_b, "ALB Region B", "Standby Endpoint")
            System(eks_b, "EKS Cluster B", "Standby Cluster")
            SystemDb(rds_b, "Aurora Replica", "Global Reader Node")
            
            Rel(alb_b, eks_b, "Routes HTTP")
            Rel(eks_b, rds_b, "Reads Data")
        }
        
    }
    
    System_Ext(dns, "Route53", "DNS Failover / Geo-Routing")
    
    Rel(user, dns, "Resolves API")
    Rel(dns, alb_a, "Primary Traffic")
    Rel(dns, alb_b, "Failover Traffic")
    
    Rel(rds_a, rds_b, "Async Replication (< 1s Lag)")
```

### 2.2 Automated Failover Workflow

```mermaid
stateDiagram-v2
    [*] --> Healthy
    Healthy --> AZ_Failure: Ingress Health Check Fails
    AZ_Failure --> Reroute: ALB removes bad AZ targets
    Reroute --> Scaling: ASG/HPA launches new pods in healthy AZs
    Scaling --> Healthy: System Stabilized
    
    Healthy --> Region_Failure: Global Outage / Latency Spike
    Region_Failure --> DNS_Failover: Route53 Update
    DNS_Failover --> DR_Active: Traffic hits Region B
    DR_Active --> DB_Promotion: Promote Aurora Replica to Writer
    DB_Promotion --> Full_Recovery
```

---

## 3. Enterprise Reference Architecture (DDD & Hexagonal)

**Location**: `~/Documents/labs/System-Design/Enterprise-Reference-Architecture/`

This reference system implements the **Order Context** using strict Clean Architecture principles.

### 3.1 Hexagonal Architecture (Class Diagram)

Detailed view of how the `Order` component isolates Domain logic from Infrastructure.

```mermaid
classDiagram
    %% Core Domain
    class OrderAggregate {
        -id: UUID
        -items: List[OrderLine]
        -status: OrderStatus
        +add_item(product, qty)
        +mark_paid()
    }
    class DomainEvent {
        +event_id: UUID
        +occurred_on: DateTime
    }
    OrderAggregate *-- DomainEvent : emits
    
    %% Ports (Interfaces)
    class OrderRepositoryPort {
        <<Interface>>
        +save(order)
        +get_by_id(id)
    }
    class EventPublisherPort {
        <<Interface>>
        +publish(events)
    }
    
    %% Application
    class CreateOrderUseCase {
        -repo: OrderRepositoryPort
        -publisher: EventPublisherPort
        +execute(command)
    }
    CreateOrderUseCase --> OrderAggregate : manipulates
    CreateOrderUseCase --> OrderRepositoryPort : uses
    
    %% Adapters (Infrastructure)
    class SqlAlchemyRepository {
        -session: AsyncSession
        +save(order)
    }
    class KafkaPublisher {
        -producer: AIOKafka
        +publish(events)
    }
    
    SqlAlchemyRepository --|> OrderRepositoryPort : implements
    KafkaPublisher --|> EventPublisherPort : implements
```

### 3.2 Saga Orchestration State Machine

The order lifecycle involves coordination between Order, Inventory, and Payment services.

```mermaid
stateDiagram-v2
    state "Order Created" as SC
    state "Inventory Pending" as IP
    state "Inventory Reserved" as IR
    state "Payment Pending" as PP
    state "Order Confirmed" as OC
    state "Order Cancelled" as COMP
    
    [*] --> SC
    SC --> IP: Begin Saga
    
    IP --> IR: Inventory Service OK
    IP --> COMP: Insufficient Stock (Compensation)
    
    IR --> PP: Request Payment
    
    PP --> OC: Payment Sucess (Saga Complete)
    PP --> COMP: Payment Failed (Release Inventory)
    
    COMP --> [*]
    OC --> [*]
```
