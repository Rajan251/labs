# API Reference

Complete API documentation for the Webhook Delivery Platform.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All event-related endpoints require API key authentication via header:

```
X-API-Key: <your-api-key>
```

## Response Format

### Success Response
```json
{
  "id": 1,
  "name": "Example",
  ...
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "detail": "Detailed error information"
}
```

## Endpoints

---

## Tenant Management

### Create Tenant

Create a new tenant account.

**Endpoint**: `POST /tenants`

**Request Body**:
```json
{
  "name": "My Company",
  "email": "webhooks@mycompany.com",
  "rate_limit": 100
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "name": "My Company",
  "email": "webhooks@mycompany.com",
  "api_key": "a1b2c3d4e5f6...",
  "secret_key": "x1y2z3...",
  "is_active": true,
  "rate_limit": 100,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": null
}
```

> **IMPORTANT**: Save the `api_key` and `secret_key` securely. The secret key is only returned once!

---

### List Tenants

Get all tenants with pagination.

**Endpoint**: `GET /tenants`

**Query Parameters**:
- `skip` (int, default: 0) - Number of records to skip
- `limit` (int, default: 100) - Maximum records to return
- `active_only` (bool, default: false) - Filter active tenants only

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "name": "My Company",
    "email": "webhooks@mycompany.com",
    "is_active": true,
    "rate_limit": 100,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

### Get Tenant

Get tenant by ID.

**Endpoint**: `GET /tenants/{tenant_id}`

**Response**: `200 OK`
```json
{
  "id": 1,
  "name": "My Company",
  "email": "webhooks@mycompany.com",
  "is_active": true,
  "rate_limit": 100,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### Update Tenant

Update tenant information.

**Endpoint**: `PATCH /tenants/{tenant_id}`

**Request Body**:
```json
{
  "name": "Updated Company Name",
  "rate_limit": 200,
  "is_active": true
}
```

**Response**: `200 OK`

---

### Delete Tenant

Delete a tenant and all associated data.

**Endpoint**: `DELETE /tenants/{tenant_id}`

**Response**: `200 OK`
```json
{
  "success": true,
  "message": "Tenant deleted successfully"
}
```

---

### Regenerate Secret Key

Regenerate tenant's secret key for HMAC signatures.

**Endpoint**: `POST /tenants/{tenant_id}/regenerate-secret`

**Response**: `200 OK`
```json
{
  "success": true,
  "message": "Secret key regenerated",
  "secret_key": "new_secret_key_here"
}
```

> **WARNING**: This invalidates all existing webhook signatures!

---

## Webhook Endpoint Management

### Create Webhook Endpoint

Configure a webhook endpoint for a tenant.

**Endpoint**: `POST /tenants/{tenant_id}/endpoints`

**Request Body**:
```json
{
  "url": "https://your-app.com/webhooks",
  "description": "Production webhook endpoint",
  "event_types": ["user.created", "order.completed"],
  "is_active": true
}
```

**Field Descriptions**:
- `url` (required) - Webhook endpoint URL (must be HTTPS in production)
- `description` (optional) - Human-readable description
- `event_types` (optional) - Array of event types to receive (empty = all events)
- `is_active` (optional, default: true) - Enable/disable endpoint

**Response**: `201 Created`
```json
{
  "id": 1,
  "tenant_id": 1,
  "url": "https://your-app.com/webhooks",
  "description": "Production webhook endpoint",
  "event_types": ["user.created", "order.completed"],
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": null
}
```

---

### List Webhook Endpoints

Get all webhook endpoints for a tenant.

**Endpoint**: `GET /tenants/{tenant_id}/endpoints`

**Query Parameters**:
- `active_only` (bool, default: false) - Filter active endpoints only

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "tenant_id": 1,
    "url": "https://your-app.com/webhooks",
    "description": "Production webhook endpoint",
    "event_types": ["user.created"],
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": null
  }
]
```

---

### Update Webhook Endpoint

Update webhook endpoint configuration.

**Endpoint**: `PATCH /endpoints/{endpoint_id}`

**Request Body**:
```json
{
  "url": "https://new-url.com/webhooks",
  "event_types": ["user.created", "user.updated"],
  "is_active": false
}
```

**Response**: `200 OK`

---

### Delete Webhook Endpoint

Delete a webhook endpoint.

**Endpoint**: `DELETE /endpoints/{endpoint_id}`

**Response**: `200 OK`

---

## Event Publishing

### Publish Event

Publish an event to the webhook platform.

**Endpoint**: `POST /events`

**Headers**:
```
X-API-Key: <your-api-key>
Content-Type: application/json
```

**Request Body**:
```json
{
  "event_id": "evt_123456",
  "event_type": "user.created",
  "payload": {
    "user_id": "user_789",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Field Descriptions**:
- `event_id` (required) - Unique event identifier (for idempotency)
- `event_type` (required) - Event type (e.g., "user.created", "order.completed")
- `payload` (required) - Event data (any valid JSON object)

**Response**: `201 Created`
```json
{
  "id": 1,
  "event_id": "evt_123456",
  "tenant_id": 1,
  "event_type": "user.created",
  "payload": {
    "user_id": "user_789",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "status": "pending",
  "idempotency_key": "a1b2c3...",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": null
}
```

**Idempotency**: Publishing the same `event_id` multiple times returns the existing event (200 OK) without triggering duplicate deliveries.

**Rate Limiting**: Returns `429 Too Many Requests` if rate limit exceeded.

**Response Headers** (on rate limit):
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704067200
Retry-After: 60
```

---

### Get Event Status

Get delivery status for a specific event.

**Endpoint**: `GET /events/{event_id}/status`

**Headers**:
```
X-API-Key: <your-api-key>
```

**Response**: `200 OK`
```json
{
  "event_id": "evt_123456",
  "status": "success",
  "total_attempts": 1,
  "last_attempt_at": "2024-01-01T00:00:10Z",
  "next_retry_at": null,
  "last_error": null
}
```

**Status Values**:
- `pending` - Queued for delivery
- `retrying` - Delivery failed, will retry
- `success` - Successfully delivered
- `failed` - All retries exhausted, moved to DLQ

---

### List Events

List events for the authenticated tenant.

**Endpoint**: `GET /events`

**Headers**:
```
X-API-Key: <your-api-key>
```

**Query Parameters**:
- `event_type` (string, optional) - Filter by event type
- `skip` (int, default: 0) - Pagination offset
- `limit` (int, default: 100) - Maximum results

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "event_id": "evt_123456",
    "tenant_id": 1,
    "event_type": "user.created",
    "payload": {...},
    "status": "success",
    "idempotency_key": "a1b2c3...",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:10Z"
  }
]
```

---

### Get Delivery Attempts

Get all delivery attempts for a specific event.

**Endpoint**: `GET /events/{event_id}/attempts`

**Headers**:
```
X-API-Key: <your-api-key>
```

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "event_id": 1,
    "endpoint_id": 1,
    "attempt_number": 1,
    "status": "success",
    "http_status_code": 200,
    "error_message": null,
    "duration_ms": 245,
    "attempted_at": "2024-01-01T00:00:10Z",
    "next_retry_at": null
  }
]
```

---

## Dead Letter Queue

### List DLQ Entries

Get failed events from the Dead Letter Queue.

**Endpoint**: `GET /dlq`

**Query Parameters**:
- `tenant_id` (int, optional) - Filter by tenant
- `resolved` (bool, optional) - Filter by resolution status
- `skip` (int, default: 0) - Pagination offset
- `limit` (int, default: 100) - Maximum results

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "event_id": 1,
    "tenant_id": 1,
    "endpoint_id": 1,
    "event_type": "user.created",
    "payload": {...},
    "total_attempts": 7,
    "last_error": "Connection timeout",
    "last_http_status": null,
    "is_resolved": false,
    "created_at": "2024-01-01T00:05:00Z",
    "resolved_at": null
  }
]
```

---

### Get DLQ Statistics

Get DLQ statistics.

**Endpoint**: `GET /dlq/stats`

**Query Parameters**:
- `tenant_id` (int, optional) - Filter by tenant

**Response**: `200 OK`
```json
{
  "total": 10,
  "unresolved": 7,
  "resolved": 3
}
```

---

### Retry DLQ Entry

Manually retry a failed event from DLQ.

**Endpoint**: `POST /dlq/{dlq_id}/retry`

**Response**: `200 OK`
```json
{
  "success": true,
  "message": "Retry initiated for DLQ entry 1"
}
```

This will:
1. Reset event status to `pending`
2. Mark DLQ entry as resolved
3. Trigger a fresh delivery attempt

---

### Delete DLQ Entry

Delete a DLQ entry.

**Endpoint**: `DELETE /dlq/{dlq_id}`

**Response**: `200 OK`

---

## Webhook Receipt (For Tenants)

### Receiving Webhooks

When you receive a webhook, it will include these headers:

```
POST /your-webhook-endpoint
Content-Type: application/json
X-Webhook-Signature: sha256=a1b2c3d4e5f6...
X-Webhook-Event-Id: evt_123456
X-Webhook-Event-Type: user.created
X-Webhook-Delivery-Attempt: 1
User-Agent: webhook-platform/1.0.0
```

**Body**:
```json
{
  "user_id": "user_789",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Verifying Signatures

**Python Example**:
```python
import hmac
import hashlib
import json

def verify_webhook_signature(payload, signature, secret_key):
    # Convert payload to JSON string with sorted keys
    payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    
    # Generate expected signature
    expected = hmac.new(
        secret_key.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Extract signature from header (remove "sha256=" prefix)
    received = signature.replace('sha256=', '')
    
    # Constant-time comparison
    return hmac.compare_digest(expected, received)

# Usage
is_valid = verify_webhook_signature(
    payload=request.json,
    signature=request.headers['X-Webhook-Signature'],
    secret_key='your_secret_key'
)

if not is_valid:
    return {"error": "Invalid signature"}, 401
```

**Node.js Example**:
```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payload, signature, secretKey) {
  // Convert payload to JSON string
  const payloadStr = JSON.stringify(payload);
  
  // Generate expected signature
  const expected = crypto
    .createHmac('sha256', secretKey)
    .update(payloadStr)
    .digest('hex');
  
  // Extract signature (remove "sha256=" prefix)
  const received = signature.replace('sha256=', '');
  
  // Constant-time comparison
  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(received)
  );
}
```

### Best Practices for Webhook Receipt

1. **Always verify signatures** before processing
2. **Return 2xx status quickly** (< 5 seconds)
3. **Process asynchronously** if needed
4. **Handle idempotency** using `X-Webhook-Event-Id`
5. **Log all webhook receipts** for debugging
6. **Use HTTPS** endpoints only

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid API key |
| 403 | Forbidden - Inactive tenant |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Duplicate email |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Rate Limits

- Default: **100 events per minute** per tenant
- Configurable per tenant
- Uses token bucket algorithm
- Returns `429` when exceeded
- Check `X-RateLimit-*` headers for details

---

## Pagination

List endpoints support pagination:

```
GET /api/v1/events?skip=0&limit=100
```

- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100, max: 1000)

---

## Versioning

API version is included in the URL: `/api/v1/`

Breaking changes will increment the version number.
