# E-Commerce Backend - Step-by-Step Implementation Guide

Complete guide to building the e-commerce backend from scratch.

## Prerequisites

```bash
# Install dependencies
pip install fastapi uvicorn sqlalchemy asyncpg redis elasticsearch stripe pydantic python-jose passlib bcrypt aio-pika

# Install databases
docker-compose up -d postgres redis elasticsearch rabbitmq
```

## Step 1: Project Structure

```
ecommerce/
├── services/
│   ├── catalog/
│   ├── search/
│   ├── cart/
│   ├── order/
│   ├── payment/
│   ├── inventory/
│   ├── promotions/
│   └── user/
├── gateway/
├── database/schemas/
├── shared/
│   ├── models.py
│   ├── database.py
│   └── auth.py
└── docker-compose.yml
```

## Step 2: Catalog Service Implementation

### 2.1 Database Schema

```sql
-- database/schemas/catalog.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    parent_id UUID REFERENCES categories(id),
    path VARCHAR(1000),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES categories(id),
    base_price DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    images JSONB DEFAULT '[]',
    attributes JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_price ON products(base_price);
```

### 2.2 Models

```python
# services/catalog/models.py
from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict
from decimal import Decimal
from datetime import datetime

class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category_id: UUID4
    base_price: Decimal
    status: str = "active"
    images: List[str] = []
    attributes: Dict = {}

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[Decimal] = None
    status: Optional[str] = None
    images: Optional[List[str]] = None
    attributes: Optional[Dict] = None

class Product(ProductBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### 2.3 Service Implementation

```python
# services/catalog/app.py
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import redis.asyncio as redis

app = FastAPI(title="Catalog Service")

# Database dependency
async def get_db():
    async with async_session() as session:
        yield session

# Redis cache
redis_client = redis.from_url("redis://localhost:6379")

@app.get("/products", response_model=List[Product])
async def list_products(
    category_id: Optional[UUID4] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List products with filters and pagination"""
    query = select(ProductModel)
    
    if category_id:
        query = query.where(ProductModel.category_id == category_id)
    if min_price:
        query = query.where(ProductModel.base_price >= min_price)
    if max_price:
        query = query.where(ProductModel.base_price <= max_price)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    return products

@app.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: UUID4,
    db: AsyncSession = Depends(get_db)
):
    """Get product by ID with caching"""
    # Try cache first
    cache_key = f"product:{product_id}"
    cached = await redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Query database
    result = await db.execute(
        select(ProductModel).where(ProductModel.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Cache for 1 hour
    await redis_client.setex(
        cache_key, 
        3600, 
        json.dumps(product.dict())
    )
    
    return product

@app.post("/products", response_model=Product, status_code=201)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new product"""
    db_product = ProductModel(**product.dict())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    
    # Publish event for search indexing
    await publish_event("product.created", {"id": str(db_product.id)})
    
    return db_product

@app.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: UUID4,
    product: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update product"""
    result = await db.execute(
        select(ProductModel).where(ProductModel.id == product_id)
    )
    db_product = result.scalar_one_or_none()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update fields
    for field, value in product.dict(exclude_unset=True).items():
        setattr(db_product, field, value)
    
    db_product.updated_at = datetime.now()
    await db.commit()
    await db.refresh(db_product)
    
    # Invalidate cache
    await redis_client.delete(f"product:{product_id}")
    
    # Publish event
    await publish_event("product.updated", {"id": str(product_id)})
    
    return db_product
```

## Step 3: Cart Service with Concurrency Control

```python
# services/cart/app.py
from fastapi import FastAPI, Depends, HTTPException
import redis.asyncio as redis
import json
from typing import List
from pydantic import BaseModel, UUID4

app = FastAPI(title="Cart Service")
redis_client = redis.from_url("redis://localhost:6379")

class CartItem(BaseModel):
    product_id: UUID4
    quantity: int
    price: Decimal

class Cart(BaseModel):
    user_id: UUID4
    items: List[CartItem]
    version: int = 0
    updated_at: str

@app.get("/cart", response_model=Cart)
async def get_cart(user_id: UUID4):
    """Get user's cart"""
    cart_data = await redis_client.hgetall(f"cart:{user_id}")
    
    if not cart_data:
        return Cart(user_id=user_id, items=[], version=0, updated_at=datetime.now().isoformat())
    
    return Cart(**{k.decode(): json.loads(v.decode()) for k, v in cart_data.items()})

@app.post("/cart/items")
async def add_to_cart(user_id: UUID4, item: CartItem, expected_version: int):
    """Add item to cart with optimistic locking"""
    cart_key = f"cart:{user_id}"
    
    # Lua script for atomic update with version check
    lua_script = """
    local cart_version = redis.call('HGET', KEYS[1], 'version')
    if not cart_version or tonumber(cart_version) == tonumber(ARGV[1]) then
        redis.call('HSET', KEYS[1], 'items', ARGV[2])
        redis.call('HSET', KEYS[1], 'version', tonumber(ARGV[1]) + 1)
        redis.call('HSET', KEYS[1], 'updated_at', ARGV[3])
        redis.call('EXPIRE', KEYS[1], 604800)  -- 7 days
        return 1
    else
        return 0
    end
    """
    
    # Get current cart
    cart = await get_cart(user_id)
    
    # Add/update item
    existing_item = next((i for i in cart.items if i.product_id == item.product_id), None)
    if existing_item:
        existing_item.quantity += item.quantity
    else:
        cart.items.append(item)
    
    # Try to update with version check
    success = await redis_client.eval(
        lua_script,
        1,
        cart_key,
        expected_version,
        json.dumps([i.dict() for i in cart.items]),
        datetime.now().isoformat()
    )
    
    if not success:
        raise HTTPException(
            status_code=409, 
            detail="Cart was modified by another request. Please retry."
        )
    
    return {"status": "success", "version": expected_version + 1}
```

## Step 4: Inventory Service with Distributed Locking

```python
# services/inventory/app.py
from fastapi import FastAPI, HTTPException
import redis.asyncio as redis
from redis.lock import Lock
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

app = FastAPI(title="Inventory Service")
redis_client = redis.from_url("redis://localhost:6379")

class ReservationRequest(BaseModel):
    order_id: UUID4
    items: List[Dict]  # [{product_id, quantity}]
    ttl: int = 600  # 10 minutes

@app.post("/inventory/reserve")
async def reserve_inventory(
    request: ReservationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reserve inventory with distributed locking"""
    reservation_id = str(uuid.uuid4())
    
    for item in request.items:
        lock_key = f"inventory_lock:{item['product_id']}"
        
        # Acquire distributed lock
        async with redis_client.lock(lock_key, timeout=5):
            # Get current inventory with row lock
            result = await db.execute(
                text("""
                    SELECT quantity, reserved_quantity 
                    FROM inventory 
                    WHERE product_id = :product_id
                    FOR UPDATE
                """),
                {"product_id": str(item['product_id'])}
            )
            inventory = result.fetchone()
            
            if not inventory:
                raise HTTPException(404, f"Product {item['product_id']} not found")
            
            available = inventory.quantity - inventory.reserved_quantity
            
            if available < item['quantity']:
                raise HTTPException(
                    400, 
                    f"Insufficient stock. Available: {available}, Requested: {item['quantity']}"
                )
            
            # Create reservation
            await db.execute(
                text("""
                    INSERT INTO inventory_reservations 
                    (id, order_id, product_id, quantity, expires_at)
                    VALUES (:id, :order_id, :product_id, :quantity, NOW() + INTERVAL ':ttl seconds')
                """),
                {
                    "id": str(uuid.uuid4()),
                    "order_id": str(request.order_id),
                    "product_id": str(item['product_id']),
                    "quantity": item['quantity'],
                    "ttl": request.ttl
                }
            )
            
            # Update reserved quantity
            await db.execute(
                text("""
                    UPDATE inventory
                    SET reserved_quantity = reserved_quantity + :quantity
                    WHERE product_id = :product_id
                """),
                {"quantity": item['quantity'], "product_id": str(item['product_id'])}
            )
    
    await db.commit()
    
    return {"reservation_id": reservation_id, "status": "reserved"}

@app.post("/inventory/confirm/{reservation_id}")
async def confirm_reservation(
    reservation_id: UUID4,
    db: AsyncSession = Depends(get_db)
):
    """Confirm reservation and deduct from actual inventory"""
    # Get reservations
    result = await db.execute(
        text("""
            SELECT * FROM inventory_reservations
            WHERE id = :id AND status = 'pending'
        """),
        {"id": str(reservation_id)}
    )
    reservations = result.fetchall()
    
    if not reservations:
        raise HTTPException(404, "Reservation not found")
    
    for res in reservations:
        # Deduct from actual inventory
        await db.execute(
            text("""
                UPDATE inventory
                SET quantity = quantity - :quantity,
                    reserved_quantity = reserved_quantity - :quantity
                WHERE product_id = :product_id
            """),
            {"quantity": res.quantity, "product_id": str(res.product_id)}
        )
        
        # Mark reservation as confirmed
        await db.execute(
            text("""
                UPDATE inventory_reservations
                SET status = 'confirmed'
                WHERE id = :id
            """),
            {"id": str(res.id)}
        )
    
    await db.commit()
    
    return {"status": "confirmed"}
```

## Step 5: Order Service with Saga Pattern

```python
# services/order/saga.py
from typing import Dict, List
import asyncio

class OrderSaga:
    """
    Distributed transaction coordinator for order creation
    
    Steps:
    1. Reserve inventory
    2. Apply promotions
    3. Create payment intent
    4. Create order
    
    If any step fails, compensate previous steps
    """
    
    def __init__(self, inventory_service, promotions_service, payment_service, order_service):
        self.inventory = inventory_service
        self.promotions = promotions_service
        self.payment = payment_service
        self.orders = order_service
    
    async def execute(self, user_id: UUID4, cart_items: List[Dict], 
                     shipping_address: Dict, payment_method: str):
        """Execute saga"""
        state = {
            'inventory_reserved': False,
            'promotion_applied': False,
            'payment_created': False,
            'order_created': False
        }
        
        try:
            # Step 1: Reserve inventory
            reservation = await self.inventory.reserve({
                'order_id': str(uuid.uuid4()),
                'items': cart_items,
                'ttl': 600
            })
            state['inventory_reserved'] = True
            state['reservation_id'] = reservation['reservation_id']
            
            # Step 2: Calculate discount
            discount = await self.promotions.calculate_discount(
                user_id=user_id,
                items=cart_items
            )
            state['promotion_applied'] = True
            state['discount'] = discount
            
            # Step 3: Create payment intent
            total = self._calculate_total(cart_items, discount)
            payment_intent = await self.payment.create_intent(
                amount=total,
                currency='usd',
                metadata={'user_id': str(user_id)},
                idempotency_key=f"order_{state['reservation_id']}"
            )
            state['payment_created'] = True
            state['payment_intent_id'] = payment_intent['id']
            
            # Step 4: Create order
            order = await self.orders.create({
                'user_id': user_id,
                'items': cart_items,
                'discount': discount,
                'total': total,
                'shipping_address': shipping_address,
                'payment_intent_id': payment_intent['id'],
                'reservation_id': state['reservation_id']
            })
            state['order_created'] = True
            
            return order
            
        except Exception as e:
            # Compensate in reverse order
            await self.compensate(state)
            raise HTTPException(500, f"Order creation failed: {str(e)}")
    
    async def compensate(self, state: Dict):
        """Rollback completed steps"""
        if state.get('payment_created'):
            try:
                await self.payment.cancel_intent(state['payment_intent_id'])
            except Exception as e:
                print(f"Failed to cancel payment: {e}")
        
        if state.get('inventory_reserved'):
            try:
                await self.inventory.release_reservation(state['reservation_id'])
            except Exception as e:
                print(f"Failed to release inventory: {e}")
```

## Step 6: Payment Service with Idempotency

```python
# services/payment/app.py
import stripe
from fastapi import FastAPI, Request, HTTPException

app = FastAPI(title="Payment Service")
stripe.api_key = settings.STRIPE_SECRET_KEY

@app.post("/payment/intent")
async def create_payment_intent(
    amount: Decimal,
    currency: str,
    metadata: Dict,
    idempotency_key: str
):
    """Create Stripe payment intent with idempotency"""
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            metadata=metadata,
            idempotency_key=idempotency_key,
            automatic_payment_methods={'enabled': True}
        )
        
        return {
            'id': intent.id,
            'client_secret': intent.client_secret,
            'status': intent.status
        }
        
    except stripe.error.IdempotencyError as e:
        # Request already processed, return existing result
        return e.idempotent_request.result

@app.post("/payment/webhook")
async def handle_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(400, "Invalid webhook")
    
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        order_id = payment_intent.metadata.get('order_id')
        
        # Update order status
        await update_order_status(order_id, 'paid')
        
        # Confirm inventory reservation
        await confirm_inventory(order_id)
        
        # Send confirmation email
        await send_order_confirmation(order_id)
    
    return {'status': 'success'}
```

## Step 7: Docker Compose Setup

```yaml
# docker-compose-ecommerce.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ecommerce
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"

  catalog-service:
    build: ./services/catalog
    ports:
      - "8001:8000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://admin:password@postgres/ecommerce
      REDIS_URL: redis://redis:6379

  cart-service:
    build: ./services/cart
    ports:
      - "8002:8000"
    depends_on:
      - redis

  inventory-service:
    build: ./services/inventory
    ports:
      - "8003:8000"
    depends_on:
      - postgres
      - redis

  order-service:
    build: ./services/order
    ports:
      - "8004:8000"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

## Step 8: Running the System

```bash
# Start all services
docker-compose -f docker-compose-ecommerce.yml up -d

# Initialize databases
docker-compose exec postgres psql -U admin -d ecommerce -f /schemas/catalog.sql

# Test catalog service
curl http://localhost:8001/products

# Test cart service
curl -X POST http://localhost:8002/cart/items \
  -H "Content-Type: application/json" \
  -d '{"product_id": "uuid", "quantity": 2, "price": 29.99}'

# Test order creation (saga)
curl -X POST http://localhost:8004/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid",
    "items": [...],
    "shipping_address": {...}
  }'
```

## Next Steps

1. **Add API Gateway**: Nginx or Kong for routing
2. **Add Monitoring**: Prometheus + Grafana
3. **Add Logging**: ELK stack
4. **Add Testing**: pytest, load testing with Locust
5. **Add CI/CD**: GitHub Actions or GitLab CI

See ECOMMERCE_DESIGN.md for complete architecture details.
