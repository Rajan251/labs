# Unified Idempotency System Design

## Overview
To prevent duplicate operations (e.g., charging a user twice) in a distributed environment, all state-changing APIs must implement idempotency checks using a unified strategy.

## Protocol

1.  **Client Responsibility**:
    - Clients MUST generate a unique `Idempotency-Key` (UUID v4 recommended) for every non-safe request (POST, PUT, PATCH).
    - Clients MUST retry requests with the *same* key if they experience a network failure or 5xx error.
    - Clients MUST NOT reuse keys for different payloads.

2.  **Service Responsibility (Middleware)**:
    - **Extraction**: Extract `Idempotency-Key` header.
    - **Storage**: Use Redis to store keys.
        - Key Format: `idem:{service_name}:{key}`
        - Value Structure: JSON `{ "status": "ENUM", "response": { ... }, "created_at": "timestamp" }`
        - TTL: 24-48 hours.

## States

| State | Description | Action |
| :--- | :--- | :--- |
| **P (Processing)** | Request is currently being executed. | Return `409 Conflict` (or `429 Too Many Requests` with Retry-After). <br> *Prevents concurrent execution of the same key.* |
| **S (Success)** | Request completed successfully. | Return stored `200/201` response immediately. |
| **F (Failed)** | Request failed deterministically (e.g., 400 Bad Request). | Return stored `4xx` response. |
| **E (Error)** | Request failed transiently (e.g., 500 error). | Allow retry. Delete key or update state to allow re-execution. |

## Implementation Logic (Pseudo-code)

```python
def idempotency_middleware(request, next):
    key = request.headers.get("Idempotency-Key")
    if not key:
        return next(request)

    redis_key = f"idem:{SERVICE_NAME}:{key}"
    
    # Atomic Check-and-Set
    # If key doesn't exist, set to PROCESSING with short TTL (to prevent infinite lock if crash)
    if redis.setnx(redis_key, "PROCESSING", ex=60):
        try:
            response = next(request)
            
            # Store final response
            redis.set(redis_key, serialize(response), ex=86400)
            return response
            
        except Exception:
            # On crash, remove key so retry is possible
            redis.delete(redis_key)
            raise
    else:
        # Key exists
        stored = redis.get(redis_key)
        if stored == "PROCESSING":
             return 409 Conflict
        else:
             return deserialize(stored)
```
