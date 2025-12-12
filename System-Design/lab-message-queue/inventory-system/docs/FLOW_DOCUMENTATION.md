# Inventory System - Complete Flow Documentation

End-to-end flow documentation for all inventory operations.

## System Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         API Gateway/Load Balancer   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      FastAPI Application            │
│  ┌──────────────────────────────┐   │
│  │  API Endpoints               │   │
│  └──────────┬───────────────────┘   │
│             │                        │
│  ┌──────────▼───────────────────┐   │
│  │  Service Layer               │   │
│  │  - InventoryService          │   │
│  │  - ReservationService        │   │
│  └──────────┬───────────────────┘   │
└─────────────┼────────────────────────┘
              │
       ┌──────┴──────┐
       │             │
       ▼             ▼
┌────────────┐  ┌────────────┐
│ PostgreSQL │  │   Redis    │
│  Database  │  │   Cache    │
└────────────┘  └────────────┘
```

## Flow 1: Receive Inventory

**Scenario**: Warehouse receives new stock from supplier

### Request Flow

```
1. Client → POST /api/v1/inventory/receive
   {
     "sku": "LAPTOP-001",
     "warehouse_code": "WH1",
     "quantity": 50,
     "reason": "New shipment from supplier"
   }

2. API Layer → InventoryService.receive_inventory()

3. Service Layer:
   a. Get inventory record (SKU + Warehouse)
   b. Acquire Redis distributed lock
   c. Update quantity_on_hand
   d. Log transaction
   e. Release lock
   f. Commit to database

4. Response → 200 OK
   {
     "status": "success",
     "sku": "LAPTOP-001",
     "warehouse": "WH1",
     "old_quantity": 100,
     "new_quantity": 150
   }
```

### Database Changes

```sql
-- Before
SELECT quantity_on_hand FROM inventory 
WHERE product_id = 'uuid' AND warehouse_id = 'uuid';
-- Result: 100

-- After
SELECT quantity_on_hand FROM inventory 
WHERE product_id = 'uuid' AND warehouse_id = 'uuid';
-- Result: 150

-- Transaction logged
SELECT * FROM inventory_transactions 
WHERE inventory_id = 'uuid' 
ORDER BY created_at DESC LIMIT 1;
-- Result: type='receive', quantity_change=50, quantity_before=100, quantity_after=150
```

### Concurrency Handling

```python
# Redis distributed lock prevents race conditions
async with redis_client.lock(f"inventory_lock:{inventory_id}", timeout=5):
    # Only one process can execute this at a time
    inventory.quantity_on_hand += quantity
    await db.commit()
```

## Flow 2: Reserve Inventory (Checkout)

**Scenario**: Customer checks out, inventory needs to be reserved

### Request Flow

```
1. Client → POST /api/v1/reservations
   {
     "order_id": "uuid",
     "items": [
       {
         "inventory_id": "uuid",
         "product_id": "uuid",
         "warehouse_id": "uuid",
         "quantity": 2
       }
     ],
     "ttl": 600  // 10 minutes
   }

2. API Layer → ReservationService.reserve()

3. Service Layer (for each item):
   a. Acquire Redis lock for inventory
   b. Check availability:
      available = quantity_on_hand - quantity_reserved
   c. If insufficient → raise error
   d. Create reservation record
   e. Increment quantity_reserved
   f. Set expiration (10 minutes)
   g. Release lock

4. Response → 200 OK
   {
     "reservation_ids": ["uuid"],
     "status": "reserved"
   }
```

### State Changes

```
Before:
┌──────────────────────────────────┐
│ quantity_on_hand:     100        │
│ quantity_reserved:      0        │
│ quantity_available:   100        │
└──────────────────────────────────┘

After Reservation:
┌──────────────────────────────────┐
│ quantity_on_hand:     100        │
│ quantity_reserved:      2        │
│ quantity_available:    98        │
└──────────────────────────────────┘

Reservation Record:
┌──────────────────────────────────┐
│ id: uuid                         │
│ order_id: uuid                   │
│ quantity: 2                      │
│ status: 'pending'                │
│ expires_at: NOW() + 10 minutes   │
└──────────────────────────────────┘
```

## Flow 3: Confirm Reservation (Payment Success)

**Scenario**: Payment successful, decrement actual stock

### Request Flow

```
1. Client → POST /api/v1/reservations/{order_id}/confirm

2. Service Layer:
   a. Get all pending reservations for order
   b. For each reservation:
      - Decrement quantity_on_hand
      - Decrement quantity_reserved
      - Mark reservation as 'confirmed'
   c. Commit all changes

3. Response → 200 OK
   {
     "status": "confirmed",
     "order_id": "uuid"
   }
```

### State Changes

```
Before Confirmation:
┌──────────────────────────────────┐
│ quantity_on_hand:     100        │
│ quantity_reserved:      2        │
│ quantity_available:    98        │
└──────────────────────────────────┘

After Confirmation:
┌──────────────────────────────────┐
│ quantity_on_hand:      98        │
│ quantity_reserved:      0        │
│ quantity_available:    98        │
└──────────────────────────────────┘

Reservation Status: 'pending' → 'confirmed'
```

## Flow 4: Release Reservation (Order Cancelled)

**Scenario**: Customer cancels order or timeout

### Request Flow

```
1. Client → POST /api/v1/reservations/{order_id}/release

2. Service Layer:
   a. Get all pending reservations
   b. For each reservation:
      - Decrement quantity_reserved
      - Mark as 'released'
   c. Inventory becomes available again

3. Response → 200 OK
   {
     "status": "released",
     "order_id": "uuid"
   }
```

### State Changes

```
Before Release:
┌──────────────────────────────────┐
│ quantity_on_hand:     100        │
│ quantity_reserved:      2        │
│ quantity_available:    98        │
└──────────────────────────────────┘

After Release:
┌──────────────────────────────────┐
│ quantity_on_hand:     100        │
│ quantity_reserved:      0        │
│ quantity_available:   100        │
└──────────────────────────────────┘

Reservation Status: 'pending' → 'released'
```

## Flow 5: Low Stock Alert

**Scenario**: Inventory falls below reorder point

### Trigger Flow

```
1. Any inventory change (receive, ship, adjust)

2. Check condition:
   IF quantity_available <= reorder_point THEN
     trigger_alert()

3. Alert Service:
   a. Query low stock items
   b. Send email to procurement team
   c. Create purchase order suggestion

4. Dashboard Update:
   - Low stock count incremented
   - Item appears in low stock list
```

### Query

```sql
-- Get low stock items
SELECT 
    p.sku,
    p.name,
    w.name as warehouse,
    i.quantity_available,
    i.reorder_point,
    i.reorder_quantity
FROM inventory i
JOIN products p ON p.id = i.product_id
JOIN warehouses w ON w.id = i.warehouse_id
WHERE i.quantity_available <= i.reorder_point
ORDER BY i.quantity_available ASC;
```

## Flow 6: Transfer Between Warehouses

**Scenario**: Move stock from WH1 to WH2

### Request Flow

```
1. Client → POST /api/v1/inventory/transfer
   {
     "sku": "LAPTOP-001",
     "from_warehouse": "WH1",
     "to_warehouse": "WH2",
     "quantity": 10
   }

2. Service Layer (Atomic Transaction):
   a. Ship from WH1:
      - Check availability
      - Decrement quantity_on_hand
      - Log transaction (type='transfer_out')
   
   b. Receive at WH2:
      - Increment quantity_on_hand
      - Log transaction (type='transfer_in')
   
   c. Commit both changes atomically

3. Response → 200 OK
   {
     "status": "success",
     "from": "WH1",
     "to": "WH2",
     "quantity": 10
   }
```

### State Changes

```
WH1 Before:
┌──────────────────────────────────┐
│ quantity_on_hand:     100        │
│ quantity_available:   100        │
└──────────────────────────────────┘

WH1 After:
┌──────────────────────────────────┐
│ quantity_on_hand:      90        │
│ quantity_available:    90        │
└──────────────────────────────────┘

WH2 Before:
┌──────────────────────────────────┐
│ quantity_on_hand:      50        │
│ quantity_available:    50        │
└──────────────────────────────────┘

WH2 After:
┌──────────────────────────────────┐
│ quantity_on_hand:      60        │
│ quantity_available:    60        │
└──────────────────────────────────┘
```

## Error Handling

### Insufficient Stock

```python
if available < requested:
    raise HTTPException(
        400,
        f"Insufficient stock. Available: {available}, Requested: {requested}"
    )
```

### Concurrency Conflict

```python
# Optimistic locking with version
UPDATE inventory
SET quantity_reserved = quantity_reserved + :qty,
    version = version + 1
WHERE id = :id AND version = :expected_version

# If no rows updated → version mismatch
if result.rowcount == 0:
    raise ConcurrencyError("Inventory was modified. Please retry.")
```

### Lock Timeout

```python
try:
    async with redis_client.lock(lock_key, timeout=5):
        # Critical section
except redis.exceptions.LockError:
    raise HTTPException(503, "System busy. Please retry.")
```

## Performance Optimizations

### 1. Redis Caching

```python
# Cache frequently accessed inventory
cache_key = f"inventory:{product_id}:{warehouse_id}"
cached = await redis_client.get(cache_key)

if cached:
    return json.loads(cached)

# Query database
inventory = await db.fetch_one(...)

# Cache for 5 minutes
await redis_client.setex(cache_key, 300, json.dumps(inventory))
```

### 2. Database Indexes

```sql
-- Composite index for lookups
CREATE INDEX idx_inventory_product_warehouse 
ON inventory(product_id, warehouse_id);

-- Index for low stock queries
CREATE INDEX idx_inventory_low_stock 
ON inventory(warehouse_id, (quantity_on_hand - quantity_reserved))
WHERE (quantity_on_hand - quantity_reserved) <= reorder_point;
```

### 3. Batch Operations

```python
# Process multiple items in single transaction
async with db.transaction():
    for item in items:
        await update_inventory(item)
    # All or nothing
```

## Monitoring & Metrics

### Key Metrics

- **Inventory Turnover**: Stock movement rate
- **Reservation Success Rate**: % of successful reservations
- **Lock Wait Time**: Time spent waiting for locks
- **Low Stock Alerts**: Number of items below reorder point
- **API Response Time**: p50, p95, p99 latencies

### Dashboard Queries

```sql
-- Out of stock count
SELECT COUNT(*) FROM inventory
WHERE quantity_available = 0;

-- Total inventory value
SELECT SUM(quantity_on_hand * base_price)
FROM inventory i
JOIN products p ON p.id = i.product_id;

-- Top moving products
SELECT p.sku, COUNT(*) as transaction_count
FROM inventory_transactions t
JOIN inventory i ON i.id = t.inventory_id
JOIN products p ON p.id = i.product_id
WHERE t.created_at >= NOW() - INTERVAL '7 days'
GROUP BY p.sku
ORDER BY transaction_count DESC
LIMIT 10;
```

## Summary

The inventory system provides:

✅ **Atomic Operations** - Distributed locks prevent race conditions  
✅ **Reservation System** - Hold inventory during checkout  
✅ **Audit Trail** - Complete transaction history  
✅ **Multi-Warehouse** - Track stock across locations  
✅ **Low Stock Alerts** - Automatic reorder notifications  
✅ **High Performance** - Redis caching, database indexes  
✅ **Error Handling** - Graceful degradation  
✅ **Scalability** - Horizontal scaling support  

All operations are designed for high concurrency, data consistency, and production reliability.
