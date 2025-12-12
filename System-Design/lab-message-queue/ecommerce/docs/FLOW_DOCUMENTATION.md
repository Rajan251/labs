# E-Commerce Platform - Complete Flow Documentation

End-to-end flows for all e-commerce operations with detailed state diagrams.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│                    (Web App / Mobile App)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (Nginx)                        │
│          Routes: /api/catalog, /api/cart, /api/orders          │
└──────┬──────────┬──────────┬──────────┬──────────┬─────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌────────┐ ┌─────────┐ ┌──────────┐
│ Catalog  │ │  Cart  │ │ Order  │ │ Payment │ │Inventory │
│ Service  │ │Service │ │Service │ │ Service │ │ Service  │
└────┬─────┘ └───┬────┘ └───┬────┘ └────┬────┘ └────┬─────┘
     │           │          │           │           │
     └───────────┴──────────┴───────────┴───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  RabbitMQ Event Bus  │
              └──────────────────────┘
```

## Flow 1: Browse Products (Catalog)

**Scenario**: Customer browses product catalog

### Request Flow

```
1. Client → GET /api/catalog/products?category=electronics&page=1

2. API Gateway → Catalog Service

3. Catalog Service:
   a. Check Redis cache for product list
   b. If cache miss:
      - Query PostgreSQL
      - Cache results (TTL: 5 minutes)
   c. Return paginated results

4. Response → 200 OK
   {
     "products": [
       {
         "id": "uuid",
         "name": "Laptop",
         "price": 999.99,
         "stock": 50,
         "image_url": "https://..."
       }
     ],
     "total": 150,
     "page": 1,
     "per_page": 20
   }
```

### Caching Strategy

```
Cache Key: products:category:{category}:page:{page}
TTL: 5 minutes

On product update:
- Invalidate all related cache keys
- Publish event to RabbitMQ
```

### Database Query

```sql
SELECT 
    p.id,
    p.name,
    p.description,
    p.price,
    p.image_url,
    i.quantity_available as stock
FROM products p
LEFT JOIN inventory i ON i.product_id = p.id
WHERE p.category_id = :category_id
  AND p.is_active = true
ORDER BY p.created_at DESC
LIMIT 20 OFFSET :offset;
```

## Flow 2: Add to Cart

**Scenario**: Customer adds product to shopping cart

### Request Flow

```
1. Client → POST /api/cart/items
   {
     "product_id": "uuid",
     "quantity": 2
   }

2. API Gateway → Cart Service

3. Cart Service:
   a. Validate user session
   b. Check product availability (call Inventory Service)
   c. Get product details (call Catalog Service)
   d. Update cart in Redis:
      - cart:{user_id} → {product_id: quantity}
   e. Set cart expiry (7 days)
   f. Calculate totals

4. Response → 200 OK
   {
     "cart_id": "uuid",
     "items": [
       {
         "product_id": "uuid",
         "name": "Laptop",
         "price": 999.99,
         "quantity": 2,
         "subtotal": 1999.98
       }
     ],
     "total": 1999.98
   }
```

### State Changes

```
Redis Before:
cart:user123 → {}

Redis After:
cart:user123 → {
  "product-uuid-1": {
    "quantity": 2,
    "price": 999.99,
    "added_at": "2024-01-01T10:00:00Z"
  }
}
TTL: 7 days
```

### Availability Check

```python
# Call Inventory Service
response = await http_client.get(
    f"http://inventory-service:8005/api/stock/{product_id}"
)

if response.json()["available"] < quantity:
    raise HTTPException(400, "Insufficient stock")
```

## Flow 3: Checkout Process

**Scenario**: Customer proceeds to checkout

### Complete Checkout Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CHECKOUT PROCESS                         │
└─────────────────────────────────────────────────────────────┘

Step 1: Initiate Checkout
   Client → POST /api/orders/checkout
   {
     "cart_id": "uuid",
     "shipping_address": {...},
     "payment_method_id": "uuid"
   }

Step 2: Order Service Actions
   a. Get cart items from Cart Service
   b. Validate all items still available
   c. Calculate final total (including tax, shipping)
   d. Create order record (status: PENDING)
   e. Reserve inventory (call Inventory Service)
   f. Return order ID to client

Step 3: Payment Processing
   Client → POST /api/payments/process
   {
     "order_id": "uuid",
     "payment_method_id": "uuid"
   }

Step 4: Payment Service Actions
   a. Get order details
   b. Call Stripe API to create payment intent
   c. Process payment
   d. If successful:
      - Update order status → PAID
      - Publish OrderPaid event to RabbitMQ
   e. If failed:
      - Update order status → PAYMENT_FAILED
      - Release inventory reservation

Step 5: Order Fulfillment (Async)
   a. Inventory Service listens to OrderPaid event
   b. Confirm inventory reservation
   c. Decrement stock
   d. Publish InventoryUpdated event
   e. Order Service updates status → CONFIRMED

Step 6: Notification
   a. Send order confirmation email
   b. Update order status → PROCESSING
```

### State Machine

```
Order States:
PENDING → PAYMENT_PROCESSING → PAID → CONFIRMED → PROCESSING → 
SHIPPED → DELIVERED

Failure States:
PAYMENT_FAILED → CANCELLED
INVENTORY_UNAVAILABLE → CANCELLED
```

### Database Changes

```sql
-- Create order
INSERT INTO orders (
    id, user_id, total_amount, status, created_at
) VALUES (
    :id, :user_id, :total, 'PENDING', NOW()
);

-- Create order items
INSERT INTO order_items (
    order_id, product_id, quantity, price
) VALUES
    (:order_id, :product_id, :quantity, :price);

-- Update after payment
UPDATE orders
SET status = 'PAID',
    paid_at = NOW(),
    stripe_payment_intent_id = :intent_id
WHERE id = :order_id;
```

## Flow 4: Inventory Reservation

**Scenario**: Reserve inventory during checkout

### Request Flow

```
1. Order Service → POST /api/inventory/reserve
   {
     "order_id": "uuid",
     "items": [
       {
         "product_id": "uuid",
         "quantity": 2
       }
     ],
     "ttl": 600  // 10 minutes
   }

2. Inventory Service:
   a. For each item:
      - Acquire distributed lock (Redis)
      - Check availability
      - Create reservation record
      - Increment quantity_reserved
      - Release lock
   b. Set reservation expiry
   c. Schedule cleanup job

3. Response → 200 OK
   {
     "reservation_id": "uuid",
     "status": "reserved",
     "expires_at": "2024-01-01T10:10:00Z"
   }
```

### State Changes

```
Before Reservation:
┌──────────────────────────────────┐
│ Product: Laptop                  │
│ quantity_on_hand:     100        │
│ quantity_reserved:      0        │
│ quantity_available:   100        │
└──────────────────────────────────┘

After Reservation:
┌──────────────────────────────────┐
│ Product: Laptop                  │
│ quantity_on_hand:     100        │
│ quantity_reserved:      2        │
│ quantity_available:    98        │
└──────────────────────────────────┘

Reservation Record:
┌──────────────────────────────────┐
│ id: uuid                         │
│ order_id: uuid                   │
│ product_id: uuid                 │
│ quantity: 2                      │
│ status: 'pending'                │
│ expires_at: NOW() + 10 min       │
└──────────────────────────────────┘
```

### Confirmation Flow

```
1. Payment successful → Publish OrderPaid event

2. Inventory Service (Event Listener):
   a. Receive OrderPaid event
   b. Get reservations for order
   c. For each reservation:
      - Decrement quantity_on_hand
      - Decrement quantity_reserved
      - Mark reservation as 'confirmed'
   d. Publish InventoryUpdated event

3. Final State:
┌──────────────────────────────────┐
│ Product: Laptop                  │
│ quantity_on_hand:      98        │
│ quantity_reserved:      0        │
│ quantity_available:    98        │
└──────────────────────────────────┘
```

## Flow 5: Event-Driven Communication

**Scenario**: Services communicate via RabbitMQ

### Event Types

```python
# Order events
OrderCreated = {
    "event_type": "order.created",
    "order_id": "uuid",
    "user_id": "uuid",
    "total": 1999.98,
    "items": [...]
}

OrderPaid = {
    "event_type": "order.paid",
    "order_id": "uuid",
    "payment_intent_id": "stripe_id"
}

# Inventory events
InventoryReserved = {
    "event_type": "inventory.reserved",
    "reservation_id": "uuid",
    "order_id": "uuid",
    "items": [...]
}

InventoryUpdated = {
    "event_type": "inventory.updated",
    "product_id": "uuid",
    "quantity_available": 98
}
```

### Publisher Pattern

```python
class EventPublisher:
    async def publish(self, event_type: str, data: dict):
        """Publish event to RabbitMQ"""
        
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        
        # Declare exchange
        exchange = await channel.declare_exchange(
            'ecommerce',
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        # Publish message
        message = aio_pika.Message(
            body=json.dumps(data).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await exchange.publish(
            message,
            routing_key=event_type
        )
```

### Subscriber Pattern

```python
class EventSubscriber:
    async def subscribe(self, event_type: str, handler):
        """Subscribe to events"""
        
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        
        # Declare exchange and queue
        exchange = await channel.declare_exchange(
            'ecommerce',
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        queue = await channel.declare_queue(
            f'{SERVICE_NAME}.{event_type}',
            durable=True
        )
        
        # Bind queue to exchange
        await queue.bind(exchange, routing_key=event_type)
        
        # Consume messages
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    data = json.loads(message.body)
                    await handler(data)
```

## Flow 6: Search Products

**Scenario**: Customer searches for products

### Request Flow

```
1. Client → GET /api/catalog/search?q=laptop&filters={"brand":"Apple"}

2. Catalog Service:
   a. Parse search query
   b. Query Elasticsearch
   c. Apply filters
   d. Rank results
   e. Return results

3. Response → 200 OK
   {
     "results": [...],
     "total": 25,
     "facets": {
       "brands": {"Apple": 10, "Dell": 8, "HP": 7},
       "price_ranges": {"0-500": 5, "500-1000": 15, "1000+": 5}
     }
   }
```

### Elasticsearch Query

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "laptop",
            "fields": ["name^3", "description", "tags"],
            "fuzziness": "AUTO"
          }
        }
      ],
      "filter": [
        {
          "term": {
            "brand": "Apple"
          }
        },
        {
          "range": {
            "price": {
              "gte": 0,
              "lte": 2000
            }
          }
        }
      ]
    }
  },
  "aggs": {
    "brands": {
      "terms": {
        "field": "brand"
      }
    },
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          {"to": 500},
          {"from": 500, "to": 1000},
          {"from": 1000}
        ]
      }
    }
  }
}
```

## Flow 7: Order Tracking

**Scenario**: Customer tracks order status

### Request Flow

```
1. Client → GET /api/orders/{order_id}

2. Order Service:
   a. Get order from database
   b. Get shipment tracking (if shipped)
   c. Return order details with timeline

3. Response → 200 OK
   {
     "order_id": "uuid",
     "status": "SHIPPED",
     "timeline": [
       {
         "status": "PENDING",
         "timestamp": "2024-01-01T10:00:00Z"
       },
       {
         "status": "PAID",
         "timestamp": "2024-01-01T10:05:00Z"
       },
       {
         "status": "CONFIRMED",
         "timestamp": "2024-01-01T10:06:00Z"
       },
       {
         "status": "PROCESSING",
         "timestamp": "2024-01-01T11:00:00Z"
       },
       {
         "status": "SHIPPED",
         "timestamp": "2024-01-01T15:00:00Z",
         "tracking_number": "1Z999AA10123456784"
       }
     ],
     "estimated_delivery": "2024-01-05T18:00:00Z"
   }
```

## Performance Optimizations

### 1. Database Indexing

```sql
-- Product search
CREATE INDEX idx_products_name_gin ON products USING gin(to_tsvector('english', name));
CREATE INDEX idx_products_category ON products(category_id, is_active);

-- Order queries
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC);
CREATE INDEX idx_orders_status ON orders(status) WHERE status IN ('PENDING', 'PROCESSING');

-- Inventory lookups
CREATE INDEX idx_inventory_product ON inventory(product_id);
```

### 2. Caching Layers

```
L1: Application Cache (in-memory)
- Product details: 5 minutes
- Category tree: 1 hour

L2: Redis Cache
- Product lists: 5 minutes
- User carts: 7 days
- Session data: 24 hours

L3: CDN Cache
- Product images: 30 days
- Static assets: 90 days
```

### 3. Query Optimization

```python
# Eager loading to avoid N+1 queries
products = await db.execute(
    select(Product)
    .options(
        joinedload(Product.category),
        joinedload(Product.inventory)
    )
    .where(Product.is_active == True)
)
```

## Monitoring Metrics

### Key Metrics

- **Order Conversion Rate**: Orders / Cart creations
- **Cart Abandonment Rate**: Abandoned carts / Total carts
- **Average Order Value**: Total revenue / Orders
- **Inventory Turnover**: Sales / Average inventory
- **API Response Time**: p50, p95, p99
- **Error Rate**: 4xx, 5xx responses
- **Event Processing Lag**: RabbitMQ queue depth

### Dashboards

```
Grafana Dashboards:
1. Business Metrics
   - Revenue (hourly, daily)
   - Orders by status
   - Top selling products

2. Technical Metrics
   - API latency
   - Database connections
   - Cache hit rate
   - Queue depth

3. Infrastructure
   - Pod CPU/memory
   - Node utilization
   - Network traffic
```

## Summary

The e-commerce platform provides:

✅ **Complete Shopping Flow** - Browse → Cart → Checkout → Payment  
✅ **Event-Driven Architecture** - RabbitMQ for async communication  
✅ **Inventory Management** - Reservations with distributed locks  
✅ **High Performance** - Multi-level caching, optimized queries  
✅ **Scalability** - Microservices, horizontal scaling  
✅ **Reliability** - State machines, error handling  
✅ **Observability** - Comprehensive monitoring and tracing  

All flows designed for high concurrency, data consistency, and production reliability.
