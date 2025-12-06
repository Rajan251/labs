# System Architecture

## Overview

The Centralized Configuration Management System is designed to provide a scalable, reliable, and feature-rich solution for managing application configurations across multiple environments.

## Core Components

### 1. API Layer (FastAPI)

**Responsibilities:**
- Handle HTTP requests
- Request validation
- Authentication/Authorization
- Rate limiting
- API documentation (OpenAPI/Swagger)

**Key Features:**
- Async request handling
- Automatic OpenAPI documentation
- Pydantic-based validation
- CORS support
- Health check endpoints

### 2. Business Logic Layer

**Services:**

#### Config Service
- Configuration CRUD operations
- Hierarchy resolution (Global → App → Environment)
- Version management
- Cache invalidation
- Change notifications

#### Rollout Service
- Rollout strategy evaluation
- Percentage-based rollouts
- Canary deployments
- Feature flag management
- User/group targeting

#### Audit Service
- Change tracking
- User activity logging
- Compliance reporting

### 3. Data Layer

#### PostgreSQL
**Purpose:** Primary data store

**Tables:**
- `configs` - Configuration entries
- `config_versions` - Version history
- `rollouts` - Rollout strategies
- `audit_logs` - Audit trail

**Indexes:**
- Composite indexes on (app_id, environment, key)
- Timestamp indexes for audit queries
- Version indexes for history queries

#### Redis
**Purpose:** Caching and pub/sub

**Usage:**
- Configuration caching (TTL-based)
- Session storage
- Rate limiting
- Pub/sub for change notifications

#### RabbitMQ
**Purpose:** Message broker

**Usage:**
- Configuration change events
- Asynchronous processing
- Client notifications
- Event-driven architecture

## Configuration Hierarchy

```
┌─────────────────────────────────────┐
│         Global Configs              │
│  (app_id=NULL, environment=NULL)    │
│  - Applies to ALL apps/envs         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│       App-Level Configs             │
│  (app_id=X, environment=NULL)       │
│  - Overrides global                 │
│  - Applies to ALL envs of app X     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    Environment-Specific Configs     │
│  (app_id=X, environment=Y)          │
│  - Overrides app-level              │
│  - Applies only to app X in env Y   │
└─────────────────────────────────────┘
```

## Rollout Strategies

### 1. Immediate
Deploy configuration to all instances immediately.

### 2. Percentage-Based
Gradually roll out to increasing percentages of traffic.

```
Time 0:   10% of users
Time 1h:  25% of users
Time 2h:  50% of users
Time 4h:  100% of users
```

### 3. Canary
Deploy to a small subset of users first, then expand.

```
Phase 1: Canary group (5%)
Phase 2: If successful, expand to 100%
```

### 4. Feature Flag
Control configuration via feature flag.

```
if feature_flag_enabled:
    use_new_config()
else:
    use_old_config()
```

### 5. Time-Based
Schedule configuration deployment for specific time.

```
start_time: 2024-01-01 00:00:00
end_time:   2024-01-01 23:59:59
```

### 6. User Targeting
Target specific users or groups.

```
target_users: ["user123", "user456"]
target_groups: ["beta_testers", "premium_users"]
```

## Data Flow

### Configuration Fetch Flow

```
Client SDK
    │
    ├─→ Check local cache
    │   └─→ If valid, return cached
    │
    ├─→ If expired, fetch from API
    │   │
    │   └─→ POST /api/v1/configs/fetch
    │       │
    │       └─→ Config Service
    │           │
    │           ├─→ Check Redis cache
    │           │   └─→ If hit, return
    │           │
    │           └─→ If miss, query PostgreSQL
    │               │
    │               ├─→ Fetch global configs
    │               ├─→ Fetch app-level configs
    │               ├─→ Fetch env-specific configs
    │               │
    │               └─→ Merge with hierarchy
    │                   │
    │                   └─→ Cache in Redis
    │                       │
    │                       └─→ Return to client
    │
    └─→ Cache locally with TTL
```

### Configuration Update Flow

```
API Request
    │
    └─→ PUT /api/v1/configs/{id}
        │
        └─→ Config Service
            │
            ├─→ Validate input
            │
            ├─→ Update PostgreSQL
            │   ├─→ Update config record
            │   └─→ Create version record
            │
            ├─→ Invalidate Redis cache
            │
            ├─→ Publish to RabbitMQ
            │   └─→ Notify all subscribers
            │
            └─→ Log to audit_logs
```

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers
- Load balancer distribution
- Shared cache (Redis)
- Shared database (PostgreSQL)

### Caching Strategy
- Multi-level caching (Client → Redis → Database)
- TTL-based expiration
- Cache invalidation on updates
- Cache warming on startup

### Database Optimization
- Connection pooling (20 connections)
- Prepared statements
- Composite indexes
- Query optimization
- Read replicas for heavy read loads

### High Availability
- Multiple API replicas (3+)
- PostgreSQL replication
- Redis Sentinel/Cluster
- RabbitMQ clustering

## Security Architecture

### Authentication
- JWT-based authentication
- API key support
- OAuth2 integration

### Authorization
- Role-based access control (RBAC)
- Resource-level permissions
- Audit logging

### Encryption
- TLS for data in transit
- Encryption at rest for sensitive configs
- Secret management integration

### Audit Trail
- All changes logged
- User identification
- IP address tracking
- Timestamp recording

## Monitoring & Observability

### Metrics
- Request rate and latency
- Error rates
- Cache hit/miss rates
- Database connection pool usage
- Queue depth

### Logging
- Structured logging (JSON)
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Request/response logging
- Error stack traces

### Alerting
- Service down alerts
- High error rate alerts
- Database connection issues
- Cache performance degradation
- Queue backlog alerts

## Disaster Recovery

### Backup Strategy
- Daily PostgreSQL backups
- Point-in-time recovery
- Configuration snapshots
- Audit log archival

### Recovery Procedures
- Database restoration
- Cache rebuilding
- Service rollback
- Data validation

## Future Enhancements

1. **Multi-Region Support**
   - Cross-region replication
   - Geo-distributed caching
   - Regional failover

2. **Advanced Features**
   - Configuration templates
   - Schema validation
   - Dependency management
   - Configuration inheritance

3. **Integration**
   - Webhook notifications
   - Slack/Teams integration
   - CI/CD pipeline integration
   - GitOps support
