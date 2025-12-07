# API Documentation

Complete API reference for the Inventory Management System.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently using basic authentication. JWT will be added in future versions.

## Endpoints

### Inventory Operations

#### Check Stock

```http
GET /inventory/stock
```

**Query Parameters:**
- `sku` (required): Product SKU
- `warehouse` (optional): Warehouse code

**Response:**
```json
[
  {
    "sku": "LAPTOP-001",
    "product_name": "Gaming Laptop",
    "warehouse": "WH1",
    "quantity_on_hand": 100,
    "quantity_reserved": 10,
    "quantity_available": 90
  }
]
```

#### Receive Inventory

```http
POST /inventory/receive
```

**Request Body:**
```json
{
  "sku": "LAPTOP-001",
  "warehouse_code": "WH1",
  "quantity": 50,
  "reason": "New shipment from supplier"
}
```

**Response:**
```json
{
  "status": "success",
  "sku": "LAPTOP-001",
  "warehouse": "WH1",
  "old_quantity": 100,
  "new_quantity": 150
}
```

#### Ship Inventory

```http
POST /inventory/ship
```

**Request Body:**
```json
{
  "sku": "LAPTOP-001",
  "warehouse_code": "WH1",
  "quantity": 5,
  "order_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Adjust Inventory

```http
POST /inventory/adjust
```

**Request Body:**
```json
{
  "sku": "LAPTOP-001",
  "warehouse_code": "WH1",
  "new_quantity": 95,
  "reason": "Physical count correction"
}
```

#### Transfer Inventory

```http
POST /inventory/transfer
```

**Request Body:**
```json
{
  "sku": "LAPTOP-001",
  "from_warehouse": "WH1",
  "to_warehouse": "WH2",
  "quantity": 10
}
```

### Reservations

#### Create Reservation

```http
POST /reservations
```

**Request Body:**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {
      "inventory_id": "660e8400-e29b-41d4-a716-446655440000",
      "product_id": "770e8400-e29b-41d4-a716-446655440000",
      "warehouse_id": "880e8400-e29b-41d4-a716-446655440000",
      "quantity": 2
    }
  ],
  "ttl": 600
}
```

**Response:**
```json
{
  "reservation_ids": ["990e8400-e29b-41d4-a716-446655440000"],
  "status": "reserved"
}
```

#### Confirm Reservation

```http
POST /reservations/{order_id}/confirm
```

#### Release Reservation

```http
POST /reservations/{order_id}/release
```

### Dashboard

#### Get Metrics

```http
GET /dashboard/metrics
```

**Response:**
```json
{
  "total_products": 150,
  "total_warehouses": 3,
  "out_of_stock_count": 5,
  "low_stock_count": 12,
  "total_units_on_hand": 10000,
  "total_units_reserved": 500,
  "total_units_available": 9500
}
```

#### Get Low Stock Items

```http
GET /dashboard/low-stock
```

**Query Parameters:**
- `warehouse_id` (optional): Filter by warehouse

**Response:**
```json
[
  {
    "sku": "LAPTOP-001",
    "product_name": "Gaming Laptop",
    "warehouse": "WH1",
    "quantity_available": 8,
    "reorder_point": 10,
    "suggested_reorder": 50
  }
]
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource not found
- `409 Conflict`: Concurrency conflict
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "detail": "Error message here"
}
```

## Rate Limiting

- 100 requests per minute per IP
- 1000 requests per hour per API key

## Webhooks

Subscribe to inventory events:

```http
POST /webhooks/subscribe
```

**Events:**
- `inventory.low_stock`
- `inventory.out_of_stock`
- `inventory.received`
- `inventory.shipped`
