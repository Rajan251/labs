# Inventory Management System Design

> Comprehensive inventory system for online stores with multi-warehouse support

## Table of Contents

1. [Product and Stock Modeling](#product-and-stock-modeling)
2. [Reservations vs Decrement-on-Purchase](#reservations-vs-decrement-on-purchase)
3. [Handling Oversell](#handling-oversell)
4. [Batch Import System](#batch-import-system)
5. [Low Stock Alerts](#low-stock-alerts)
6. [Warehouse Integration APIs](#warehouse-integration-apis)

---

## Product and Stock Modeling

### Data Model Architecture

```sql
-- Products (catalog data)
CREATE TABLE products (
    id UUID PRIMARY KEY,
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    category_id UUID,
    brand_id UUID,
    base_price DECIMAL(10,2),
    weight_kg DECIMAL(8,3),
    dimensions JSONB, -- {length, width, height}
    is_trackable BOOLEAN DEFAULT TRUE, -- Track inventory?
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Product variants (size, color combinations)
CREATE TABLE product_variants (
    id UUID PRIMARY KEY,
    product_id UUID REFERENCES products(id),
    sku VARCHAR(100) UNIQUE NOT NULL,
    attributes JSONB, -- {"size": "L", "color": "red"}
    price_adjustment DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Warehouses/locations
CREATE TABLE warehouses (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    address JSONB,
    type VARCHAR(50), -- fulfillment, retail, dropship
    is_active BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0, -- For allocation logic
    created_at TIMESTAMP DEFAULT NOW()
);

-- Stock levels (per warehouse)
CREATE TABLE inventory (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL,
    variant_id UUID,
    warehouse_id UUID REFERENCES warehouses(id),
    
    -- Quantity tracking
    quantity_on_hand INT NOT NULL DEFAULT 0,
    quantity_reserved INT NOT NULL DEFAULT 0,
    quantity_available INT GENERATED ALWAYS AS 
        (quantity_on_hand - quantity_reserved) STORED,
    
    -- Thresholds
    reorder_point INT DEFAULT 10,
    reorder_quantity INT DEFAULT 50,
    safety_stock INT DEFAULT 5,
    
    -- Metadata
    last_counted_at TIMESTAMP,
    last_received_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(product_id, variant_id, warehouse_id),
    CHECK (quantity_on_hand >= 0),
    CHECK (quantity_reserved >= 0),
    CHECK (quantity_reserved <= quantity_on_hand)
);

-- Inventory transactions (audit trail)
CREATE TABLE inventory_transactions (
    id UUID PRIMARY KEY,
    inventory_id UUID REFERENCES inventory(id),
    transaction_type VARCHAR(50) NOT NULL, 
    -- Types: receive, ship, adjust, reserve, release, return
    
    quantity_change INT NOT NULL,
    quantity_before INT NOT NULL,
    quantity_after INT NOT NULL,
    
    reference_type VARCHAR(50), -- order, transfer, adjustment
    reference_id UUID,
    
    reason TEXT,
    performed_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Reservations (temporary holds)
CREATE TABLE inventory_reservations (
    id UUID PRIMARY KEY,
    inventory_id UUID REFERENCES inventory(id),
    order_id UUID NOT NULL,
    
    quantity INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, confirmed, released, expired
    
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    confirmed_at TIMESTAMP,
    released_at TIMESTAMP,
    
    INDEX idx_order (order_id),
    INDEX idx_status_expires (status, expires_at)
);
```

### Key Design Decisions

**1. Separate Product and Inventory**
- Products = catalog data (name, price, description)
- Inventory = stock data (quantities, locations)
- Allows same product in multiple warehouses

**2. Multi-Warehouse Support**
- Each warehouse tracks stock independently
- Enables distributed fulfillment
- Supports retail + online inventory

**3. Variant Handling**
- Variants share product data
- Each variant has separate inventory
- Example: T-shirt (product) → Red-Large (variant)

**4. Generated Columns**
- `quantity_available` auto-calculated
- Always accurate, no sync issues
- Database enforces constraints

---

## Reservations vs Decrement-on-Purchase

### Strategy Comparison

| Aspect | Reservations | Decrement-on-Purchase |
|--------|--------------|----------------------|
| **When** | At cart checkout | At payment success |
| **Complexity** | Higher | Lower |
| **Oversell Risk** | Lower | Higher |
| **User Experience** | Better (guaranteed stock) | Worse (may fail at payment) |
| **Abandoned Carts** | Locks inventory | No impact |
| **Best For** | High-demand items | Low-demand items |

### Reservation System (Recommended)

**Flow**:
```
1. User clicks "Checkout"
2. Reserve inventory (10-minute hold)
3. User completes payment
4. Confirm reservation → Decrement stock
5. If timeout → Release reservation
```

**Implementation**:

```python
class InventoryReservationService:
    async def reserve(self, items: List[Dict], order_id: UUID, 
                     ttl: int = 600) -> str:
        """
        Reserve inventory for order
        
        Args:
            items: [{product_id, variant_id, quantity, warehouse_id}]
            order_id: Order identifier
            ttl: Reservation timeout in seconds (default 10 min)
        
        Returns:
            reservation_id
        """
        reservation_id = str(uuid.uuid4())
        
        async with db.transaction():
            for item in items:
                # Get inventory with lock
                inventory = await db.fetch_one(
                    """
                    SELECT * FROM inventory
                    WHERE product_id = $1 
                      AND variant_id = $2 
                      AND warehouse_id = $3
                    FOR UPDATE
                    """,
                    item['product_id'], 
                    item.get('variant_id'),
                    item['warehouse_id']
                )
                
                if not inventory:
                    raise InventoryNotFoundError()
                
                # Check availability
                available = (inventory['quantity_on_hand'] - 
                           inventory['quantity_reserved'])
                
                if available < item['quantity']:
                    raise InsufficientStockError(
                        f"Need {item['quantity']}, have {available}"
                    )
                
                # Create reservation
                await db.execute(
                    """
                    INSERT INTO inventory_reservations
                    (id, inventory_id, order_id, quantity, expires_at)
                    VALUES ($1, $2, $3, $4, NOW() + INTERVAL '$5 seconds')
                    """,
                    uuid.uuid4(),
                    inventory['id'],
                    order_id,
                    item['quantity'],
                    ttl
                )
                
                # Increment reserved quantity
                await db.execute(
                    """
                    UPDATE inventory
                    SET quantity_reserved = quantity_reserved + $1,
                        updated_at = NOW()
                    WHERE id = $2
                    """,
                    item['quantity'],
                    inventory['id']
                )
                
                # Log transaction
                await self._log_transaction(
                    inventory['id'],
                    'reserve',
                    item['quantity'],
                    inventory['quantity_on_hand'],
                    order_id
                )
        
        return reservation_id
    
    async def confirm(self, order_id: UUID):
        """Confirm reservation and decrement stock"""
        async with db.transaction():
            # Get pending reservations
            reservations = await db.fetch_all(
                """
                SELECT r.*, i.quantity_on_hand
                FROM inventory_reservations r
                JOIN inventory i ON i.id = r.inventory_id
                WHERE r.order_id = $1 AND r.status = 'pending'
                FOR UPDATE
                """,
                order_id
            )
            
            for res in reservations:
                # Decrement actual stock
                await db.execute(
                    """
                    UPDATE inventory
                    SET quantity_on_hand = quantity_on_hand - $1,
                        quantity_reserved = quantity_reserved - $1,
                        updated_at = NOW()
                    WHERE id = $2
                    """,
                    res['quantity'],
                    res['inventory_id']
                )
                
                # Mark reservation confirmed
                await db.execute(
                    """
                    UPDATE inventory_reservations
                    SET status = 'confirmed',
                        confirmed_at = NOW()
                    WHERE id = $1
                    """,
                    res['id']
                )
                
                # Log transaction
                await self._log_transaction(
                    res['inventory_id'],
                    'ship',
                    -res['quantity'],
                    res['quantity_on_hand'],
                    order_id
                )
    
    async def release(self, order_id: UUID):
        """Release reservation (order cancelled)"""
        async with db.transaction():
            reservations = await db.fetch_all(
                """
                SELECT * FROM inventory_reservations
                WHERE order_id = $1 AND status = 'pending'
                FOR UPDATE
                """,
                order_id
            )
            
            for res in reservations:
                # Decrement reserved quantity
                await db.execute(
                    """
                    UPDATE inventory
                    SET quantity_reserved = quantity_reserved - $1,
                        updated_at = NOW()
                    WHERE id = $2
                    """,
                    res['quantity'],
                    res['inventory_id']
                )
                
                # Mark released
                await db.execute(
                    """
                    UPDATE inventory_reservations
                    SET status = 'released',
                        released_at = NOW()
                    WHERE id = $1
                    """,
                    res['id']
                )
```

**Background Job - Cleanup Expired Reservations**:

```python
# Runs every minute
async def cleanup_expired_reservations():
    """Release expired reservations"""
    expired = await db.fetch_all(
        """
        SELECT * FROM inventory_reservations
        WHERE status = 'pending' 
          AND expires_at < NOW()
        """
    )
    
    for res in expired:
        await reservation_service.release(res['order_id'])
        
        # Notify user
        await notification_service.send(
            res['order_id'],
            "Your cart reservation expired. Please checkout again."
        )
```

---

## Handling Oversell

### Prevention Strategies

#### 1. Database Constraints

```sql
-- Prevent negative available quantity
ALTER TABLE inventory ADD CONSTRAINT check_available
CHECK (quantity_on_hand - quantity_reserved >= 0);

-- Prevent reserved > on_hand
ALTER TABLE inventory ADD CONSTRAINT check_reserved
CHECK (quantity_reserved <= quantity_on_hand);
```

#### 2. Distributed Locking

```python
import redis.asyncio as redis

class InventoryLockService:
    def __init__(self):
        self.redis = redis.from_url("redis://localhost:6379")
    
    async def with_lock(self, product_id: UUID, warehouse_id: UUID):
        """Context manager for distributed lock"""
        lock_key = f"inventory_lock:{product_id}:{warehouse_id}"
        
        return self.redis.lock(
            lock_key,
            timeout=5,  # Lock expires after 5 seconds
            blocking_timeout=3  # Wait up to 3 seconds to acquire
        )

# Usage
async with inventory_lock.with_lock(product_id, warehouse_id):
    # Critical section - only one process at a time
    inventory = await get_inventory(product_id, warehouse_id)
    if inventory.available >= quantity:
        await reserve_inventory(product_id, quantity)
```

#### 3. Optimistic Locking with Versioning

```sql
-- Add version column
ALTER TABLE inventory ADD COLUMN version INT DEFAULT 0;

-- Update with version check
UPDATE inventory
SET quantity_reserved = quantity_reserved + $1,
    version = version + 1,
    updated_at = NOW()
WHERE id = $2 
  AND version = $3  -- Version check
  AND (quantity_on_hand - quantity_reserved) >= $1  -- Availability check
RETURNING id;

-- If no rows updated, version mismatch or insufficient stock
```

```python
async def reserve_with_optimistic_lock(
    inventory_id: UUID, 
    quantity: int, 
    expected_version: int,
    max_retries: int = 3
):
    """Reserve with optimistic locking"""
    for attempt in range(max_retries):
        result = await db.execute(
            """
            UPDATE inventory
            SET quantity_reserved = quantity_reserved + $1,
                version = version + 1
            WHERE id = $2 
              AND version = $3
              AND (quantity_on_hand - quantity_reserved) >= $1
            RETURNING id, version
            """,
            quantity, inventory_id, expected_version
        )
        
        if result:
            return result['version']
        
        # Retry with backoff
        if attempt < max_retries - 1:
            await asyncio.sleep(0.1 * (2 ** attempt))
            
            # Refresh version
            inv = await db.fetch_one(
                "SELECT version FROM inventory WHERE id = $1",
                inventory_id
            )
            expected_version = inv['version']
    
    raise ConcurrencyError("Failed to reserve after retries")
```

#### 4. Rate Limiting

```python
from fastapi import HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/inventory/reserve")
@limiter.limit("10/minute")  # Max 10 reservations per minute per IP
async def reserve_inventory(request: Request, items: List[Dict]):
    """Rate-limited reservation endpoint"""
    return await reservation_service.reserve(items)
```

### Oversell Detection and Recovery

```python
async def detect_oversell():
    """Detect and alert on oversell situations"""
    oversold = await db.fetch_all(
        """
        SELECT 
            p.sku,
            p.name,
            w.name as warehouse,
            i.quantity_on_hand,
            i.quantity_reserved,
            i.quantity_available
        FROM inventory i
        JOIN products p ON p.id = i.product_id
        JOIN warehouses w ON w.id = i.warehouse_id
        WHERE i.quantity_available < 0  -- Oversold!
        """
    )
    
    if oversold:
        # Alert operations team
        await alert_service.send_critical(
            "OVERSELL DETECTED",
            oversold
        )
        
        # Auto-remediation: Cancel newest reservations
        for item in oversold:
            await auto_cancel_reservations(item['id'])
```

---

## Batch Import System

### CSV/Excel Import

```python
import pandas as pd
from typing import List, Dict

class InventoryImportService:
    async def import_from_csv(self, file_path: str, warehouse_id: UUID):
        """
        Import inventory from CSV
        
        CSV Format:
        sku,quantity,reorder_point,reorder_quantity
        LAPTOP-001,50,10,25
        PHONE-002,100,20,50
        """
        # Read CSV
        df = pd.read_csv(file_path)
        
        # Validate
        errors = self._validate_import(df)
        if errors:
            return {'status': 'error', 'errors': errors}
        
        # Process in batches
        batch_size = 1000
        total_processed = 0
        total_errors = 0
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            try:
                async with db.transaction():
                    for _, row in batch.iterrows():
                        await self._import_row(row, warehouse_id)
                        total_processed += 1
            except Exception as e:
                total_errors += len(batch)
                logger.error(f"Batch import failed: {e}")
        
        return {
            'status': 'success',
            'processed': total_processed,
            'errors': total_errors
        }
    
    def _validate_import(self, df: pd.DataFrame) -> List[str]:
        """Validate import data"""
        errors = []
        
        # Check required columns
        required = ['sku', 'quantity']
        missing = set(required) - set(df.columns)
        if missing:
            errors.append(f"Missing columns: {missing}")
        
        # Check data types
        if 'quantity' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['quantity']):
                errors.append("Quantity must be numeric")
        
        # Check for duplicates
        if df['sku'].duplicated().any():
            errors.append("Duplicate SKUs found")
        
        return errors
    
    async def _import_row(self, row: pd.Series, warehouse_id: UUID):
        """Import single row"""
        # Get product by SKU
        product = await db.fetch_one(
            "SELECT id FROM products WHERE sku = $1",
            row['sku']
        )
        
        if not product:
            raise ValueError(f"Product not found: {row['sku']}")
        
        # Upsert inventory
        await db.execute(
            """
            INSERT INTO inventory 
            (id, product_id, warehouse_id, quantity_on_hand, 
             reorder_point, reorder_quantity)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (product_id, warehouse_id)
            DO UPDATE SET
                quantity_on_hand = EXCLUDED.quantity_on_hand,
                reorder_point = EXCLUDED.reorder_point,
                reorder_quantity = EXCLUDED.reorder_quantity,
                updated_at = NOW()
            """,
            uuid.uuid4(),
            product['id'],
            warehouse_id,
            int(row['quantity']),
            int(row.get('reorder_point', 10)),
            int(row.get('reorder_quantity', 50))
        )
        
        # Log transaction
        await db.execute(
            """
            INSERT INTO inventory_transactions
            (id, inventory_id, transaction_type, quantity_change, 
             quantity_before, quantity_after, reason)
            VALUES ($1, 
                    (SELECT id FROM inventory 
                     WHERE product_id = $2 AND warehouse_id = $3),
                    'adjust', $4, 0, $4, 'Batch import')
            """,
            uuid.uuid4(),
            product['id'],
            warehouse_id,
            int(row['quantity'])
        )
```

### API for Warehouse Management Systems (WMS)

```python
from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.post("/api/v1/inventory/import")
async def import_inventory(
    file: UploadFile = File(...),
    warehouse_id: UUID = None
):
    """Import inventory from CSV/Excel"""
    # Save uploaded file
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Process import
    result = await import_service.import_from_csv(file_path, warehouse_id)
    
    return result

@app.post("/api/v1/inventory/bulk-update")
async def bulk_update(updates: List[Dict]):
    """
    Bulk update inventory
    
    Request:
    [
        {"sku": "LAPTOP-001", "warehouse": "WH1", "quantity": 50},
        {"sku": "PHONE-002", "warehouse": "WH1", "quantity": 100}
    ]
    """
    results = []
    
    async with db.transaction():
        for update in updates:
            try:
                await inventory_service.update_quantity(
                    sku=update['sku'],
                    warehouse=update['warehouse'],
                    quantity=update['quantity']
                )
                results.append({'sku': update['sku'], 'status': 'success'})
            except Exception as e:
                results.append({'sku': update['sku'], 'status': 'error', 'error': str(e)})
    
    return results
```

---

## Low Stock Alerts

### Alert System

```python
class LowStockAlertService:
    async def check_low_stock(self):
        """Check for low stock and send alerts"""
        low_stock_items = await db.fetch_all(
            """
            SELECT 
                p.sku,
                p.name,
                w.name as warehouse,
                i.quantity_available,
                i.reorder_point,
                i.reorder_quantity,
                i.safety_stock
            FROM inventory i
            JOIN products p ON p.id = i.product_id
            JOIN warehouses w ON w.id = i.warehouse_id
            WHERE i.quantity_available <= i.reorder_point
              AND i.quantity_available > 0
            ORDER BY i.quantity_available ASC
            """
        )
        
        if low_stock_items:
            await self._send_alerts(low_stock_items)
    
    async def check_out_of_stock(self):
        """Check for out of stock items"""
        out_of_stock = await db.fetch_all(
            """
            SELECT 
                p.sku,
                p.name,
                w.name as warehouse,
                COUNT(DISTINCT r.order_id) as pending_orders
            FROM inventory i
            JOIN products p ON p.id = i.product_id
            JOIN warehouses w ON w.id = i.warehouse_id
            LEFT JOIN inventory_reservations r 
                ON r.inventory_id = i.id AND r.status = 'pending'
            WHERE i.quantity_available = 0
            GROUP BY p.sku, p.name, w.name
            """
        )
        
        if out_of_stock:
            await self._send_critical_alerts(out_of_stock)
    
    async def _send_alerts(self, items: List[Dict]):
        """Send low stock alerts"""
        for item in items:
            # Email to procurement team
            await email_service.send(
                to="procurement@company.com",
                subject=f"Low Stock Alert: {item['sku']}",
                body=f"""
                Product: {item['name']} ({item['sku']})
                Warehouse: {item['warehouse']}
                Current Stock: {item['quantity_available']}
                Reorder Point: {item['reorder_point']}
                Suggested Reorder: {item['reorder_quantity']} units
                """
            )
            
            # Create purchase order suggestion
            await po_service.create_suggestion(
                sku=item['sku'],
                quantity=item['reorder_quantity'],
                priority='medium'
            )
```

### Real-Time Monitoring Dashboard

```python
@app.get("/api/v1/inventory/dashboard")
async def get_inventory_dashboard():
    """Get inventory dashboard metrics"""
    metrics = await db.fetch_one(
        """
        SELECT 
            COUNT(*) FILTER (WHERE quantity_available = 0) as out_of_stock,
            COUNT(*) FILTER (WHERE quantity_available <= reorder_point) as low_stock,
            COUNT(*) FILTER (WHERE quantity_available > reorder_point) as healthy,
            SUM(quantity_on_hand) as total_units,
            SUM(quantity_reserved) as reserved_units,
            SUM(quantity_available) as available_units
        FROM inventory
        """
    )
    
    # Top low stock items
    low_stock = await db.fetch_all(
        """
        SELECT p.sku, p.name, i.quantity_available, i.reorder_point
        FROM inventory i
        JOIN products p ON p.id = i.product_id
        WHERE i.quantity_available <= i.reorder_point
        ORDER BY i.quantity_available ASC
        LIMIT 10
        """
    )
    
    return {
        'metrics': metrics,
        'low_stock_items': low_stock
    }
```

---

## Warehouse Integration APIs

### REST API Specification

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Inventory API")

# Models
class InventoryUpdate(BaseModel):
    sku: str
    warehouse_code: str
    quantity: int
    transaction_type: str  # receive, ship, adjust, return

class StockInquiry(BaseModel):
    sku: str
    warehouse_code: Optional[str] = None

class TransferRequest(BaseModel):
    sku: str
    from_warehouse: str
    to_warehouse: str
    quantity: int

# Endpoints

@app.get("/api/v1/inventory/stock")
async def check_stock(sku: str, warehouse: Optional[str] = None):
    """
    Check stock availability
    
    Query params:
    - sku: Product SKU
    - warehouse: Warehouse code (optional, returns all if not specified)
    """
    query = """
        SELECT 
            p.sku,
            p.name,
            w.code as warehouse,
            i.quantity_on_hand,
            i.quantity_reserved,
            i.quantity_available
        FROM inventory i
        JOIN products p ON p.id = i.product_id
        JOIN warehouses w ON w.id = i.warehouse_id
        WHERE p.sku = $1
    """
    
    params = [sku]
    if warehouse:
        query += " AND w.code = $2"
        params.append(warehouse)
    
    result = await db.fetch_all(query, *params)
    
    if not result:
        raise HTTPException(404, "Product not found")
    
    return result

@app.post("/api/v1/inventory/receive")
async def receive_inventory(update: InventoryUpdate):
    """
    Receive inventory into warehouse
    
    Used when:
    - New stock arrives from supplier
    - Returns from customers
    - Transfers from other warehouses
    """
    async with db.transaction():
        # Get inventory record
        inventory = await db.fetch_one(
            """
            SELECT i.* FROM inventory i
            JOIN products p ON p.id = i.product_id
            JOIN warehouses w ON w.id = i.warehouse_id
            WHERE p.sku = $1 AND w.code = $2
            FOR UPDATE
            """,
            update.sku, update.warehouse_code
        )
        
        if not inventory:
            raise HTTPException(404, "Inventory record not found")
        
        # Update quantity
        new_quantity = inventory['quantity_on_hand'] + update.quantity
        
        await db.execute(
            """
            UPDATE inventory
            SET quantity_on_hand = $1,
                last_received_at = NOW(),
                updated_at = NOW()
            WHERE id = $2
            """,
            new_quantity, inventory['id']
        )
        
        # Log transaction
        await db.execute(
            """
            INSERT INTO inventory_transactions
            (id, inventory_id, transaction_type, quantity_change,
             quantity_before, quantity_after, reason)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            uuid.uuid4(),
            inventory['id'],
            update.transaction_type,
            update.quantity,
            inventory['quantity_on_hand'],
            new_quantity,
            f"Received via API"
        )
    
    return {"status": "success", "new_quantity": new_quantity}

@app.post("/api/v1/inventory/ship")
async def ship_inventory(update: InventoryUpdate):
    """
    Ship inventory from warehouse
    
    Used when:
    - Order is fulfilled
    - Transfer to another warehouse
    """
    async with db.transaction():
        inventory = await db.fetch_one(
            """
            SELECT i.* FROM inventory i
            JOIN products p ON p.id = i.product_id
            JOIN warehouses w ON w.id = i.warehouse_id
            WHERE p.sku = $1 AND w.code = $2
            FOR UPDATE
            """,
            update.sku, update.warehouse_code
        )
        
        if not inventory:
            raise HTTPException(404, "Inventory record not found")
        
        # Check availability
        available = inventory['quantity_on_hand'] - inventory['quantity_reserved']
        if available < update.quantity:
            raise HTTPException(
                400, 
                f"Insufficient stock. Available: {available}, Requested: {update.quantity}"
            )
        
        # Decrement quantity
        new_quantity = inventory['quantity_on_hand'] - update.quantity
        
        await db.execute(
            """
            UPDATE inventory
            SET quantity_on_hand = $1,
                updated_at = NOW()
            WHERE id = $2
            """,
            new_quantity, inventory['id']
        )
        
        # Log transaction
        await db.execute(
            """
            INSERT INTO inventory_transactions
            (id, inventory_id, transaction_type, quantity_change,
             quantity_before, quantity_after)
            VALUES ($1, $2, 'ship', $3, $4, $5)
            """,
            uuid.uuid4(),
            inventory['id'],
            -update.quantity,
            inventory['quantity_on_hand'],
            new_quantity
        )
    
    return {"status": "success", "new_quantity": new_quantity}

@app.post("/api/v1/inventory/transfer")
async def transfer_inventory(transfer: TransferRequest):
    """
    Transfer inventory between warehouses
    
    Atomic operation: decrements from source, increments to destination
    """
    async with db.transaction():
        # Decrement from source
        await ship_inventory(InventoryUpdate(
            sku=transfer.sku,
            warehouse_code=transfer.from_warehouse,
            quantity=transfer.quantity,
            transaction_type='transfer_out'
        ))
        
        # Increment to destination
        await receive_inventory(InventoryUpdate(
            sku=transfer.sku,
            warehouse_code=transfer.to_warehouse,
            quantity=transfer.quantity,
            transaction_type='transfer_in'
        ))
    
    return {"status": "success"}

@app.post("/api/v1/inventory/adjust")
async def adjust_inventory(update: InventoryUpdate):
    """
    Manual inventory adjustment
    
    Used for:
    - Physical count corrections
    - Damage/loss adjustments
    - System corrections
    """
    async with db.transaction():
        inventory = await db.fetch_one(
            """
            SELECT i.* FROM inventory i
            JOIN products p ON p.id = i.product_id
            JOIN warehouses w ON w.id = i.warehouse_id
            WHERE p.sku = $1 AND w.code = $2
            FOR UPDATE
            """,
            update.sku, update.warehouse_code
        )
        
        if not inventory:
            raise HTTPException(404, "Inventory record not found")
        
        # Set new quantity (absolute, not relative)
        old_quantity = inventory['quantity_on_hand']
        change = update.quantity - old_quantity
        
        await db.execute(
            """
            UPDATE inventory
            SET quantity_on_hand = $1,
                last_counted_at = NOW(),
                updated_at = NOW()
            WHERE id = $2
            """,
            update.quantity, inventory['id']
        )
        
        # Log transaction
        await db.execute(
            """
            INSERT INTO inventory_transactions
            (id, inventory_id, transaction_type, quantity_change,
             quantity_before, quantity_after, reason)
            VALUES ($1, $2, 'adjust', $3, $4, $5, 'Manual adjustment via API')
            """,
            uuid.uuid4(),
            inventory['id'],
            change,
            old_quantity,
            update.quantity
        )
    
    return {"status": "success", "adjustment": change}

@app.get("/api/v1/inventory/transactions")
async def get_transactions(
    sku: Optional[str] = None,
    warehouse: Optional[str] = None,
    start_date: Optional[str] = None,
    limit: int = 100
):
    """Get inventory transaction history"""
    query = """
        SELECT 
            t.*,
            p.sku,
            p.name,
            w.code as warehouse
        FROM inventory_transactions t
        JOIN inventory i ON i.id = t.inventory_id
        JOIN products p ON p.id = i.product_id
        JOIN warehouses w ON w.id = i.warehouse_id
        WHERE 1=1
    """
    
    params = []
    if sku:
        params.append(sku)
        query += f" AND p.sku = ${len(params)}"
    
    if warehouse:
        params.append(warehouse)
        query += f" AND w.code = ${len(params)}"
    
    if start_date:
        params.append(start_date)
        query += f" AND t.created_at >= ${len(params)}"
    
    query += f" ORDER BY t.created_at DESC LIMIT {limit}"
    
    return await db.fetch_all(query, *params)
```

### Webhook Notifications

```python
class WebhookService:
    async def notify_stock_change(self, inventory_id: UUID, event_type: str):
        """Send webhook on inventory changes"""
        # Get subscribed webhooks
        webhooks = await db.fetch_all(
            """
            SELECT url, secret FROM webhook_subscriptions
            WHERE event_type = $1 AND is_active = TRUE
            """,
            event_type
        )
        
        # Get inventory data
        inventory = await db.fetch_one(
            """
            SELECT 
                p.sku,
                w.code as warehouse,
                i.quantity_on_hand,
                i.quantity_available
            FROM inventory i
            JOIN products p ON p.id = i.product_id
            JOIN warehouses w ON w.id = i.warehouse_id
            WHERE i.id = $1
            """,
            inventory_id
        )
        
        payload = {
            'event': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': inventory
        }
        
        # Send to all subscribers
        for webhook in webhooks:
            await self._send_webhook(webhook['url'], payload, webhook['secret'])
    
    async def _send_webhook(self, url: str, payload: Dict, secret: str):
        """Send webhook with signature"""
        import hmac
        import hashlib
        
        # Create signature
        signature = hmac.new(
            secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Send request
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                json=payload,
                headers={'X-Signature': signature}
            )
```

---

## Summary

This inventory system provides:

✅ **Robust Data Model**: Multi-warehouse, variants, audit trail  
✅ **Reservation System**: Prevents oversell, handles timeouts  
✅ **Concurrency Control**: Distributed locks, optimistic locking  
✅ **Batch Import**: CSV/Excel support, validation  
✅ **Low Stock Alerts**: Real-time monitoring, auto-reorder  
✅ **Warehouse APIs**: Complete REST API for WMS integration  
✅ **Transaction History**: Full audit trail  
✅ **Webhooks**: Real-time notifications  

**Key Features**:
- Prevents oversell with multiple strategies
- Handles high concurrency safely
- Supports distributed fulfillment
- Integrates with external warehouse systems
- Provides real-time visibility
