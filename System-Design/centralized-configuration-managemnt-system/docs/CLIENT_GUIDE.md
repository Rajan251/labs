# Client Integration Guide

## Overview

This guide explains how to integrate the Python client SDK into your application for consuming configurations from the centralized configuration management service.

## Installation

### From Source

```bash
# Copy the client SDK to your project
cp -r client-sdk/python/config_client.py your-project/

# Install dependencies
pip install httpx structlog
```

### As a Package (Future)

```bash
pip install config-management-client
```

## Quick Start

### Basic Usage

```python
import asyncio
from config_client import ConfigClient

async def main():
    # Initialize client
    client = ConfigClient(
        base_url="http://config-service/api/v1",
        app_id="my-app",
        environment="production",
        cache_ttl=60,
    )
    
    # Fetch configs
    await client.initialize()
    
    # Get configuration values
    db_host = client.get("database.host", default="localhost")
    db_port = client.get("database.port", default=5432)
    api_key = client.get("api.key")
    
    print(f"Database: {db_host}:{db_port}")
    print(f"API Key: {api_key}")
    
    # Close client
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

### Client Parameters

```python
client = ConfigClient(
    base_url="http://config-service/api/v1",  # Service URL
    app_id="my-app",                          # Your application ID
    environment="production",                  # Environment (dev/staging/prod)
    cache_ttl=60,                             # Cache TTL in seconds
    retry_max_attempts=3,                     # Max retry attempts
    retry_backoff_factor=2,                   # Backoff multiplier
    fallback_config_path="./config.json",    # Fallback config file
)
```

## Advanced Features

### Auto-Refresh

Automatically refresh configurations at regular intervals:

```python
async def main():
    client = ConfigClient(...)
    await client.initialize()
    
    # Start auto-refresh (checks every 30 seconds)
    await client.start_auto_refresh(interval=30)
    
    # Your application logic
    while True:
        db_host = client.get("database.host")
        # Use the config...
        await asyncio.sleep(10)
```

### Change Notifications

React to configuration changes in real-time:

```python
async def on_config_change(configs):
    """Called when configs change."""
    print(f"Configs updated! Total: {len(configs)}")
    
    # Reload your application components
    reload_database_connection()
    reload_cache_settings()

async def main():
    client = ConfigClient(...)
    await client.initialize()
    
    # Register change listener
    client.on_change(on_config_change)
    
    # Start auto-refresh
    await client.start_auto_refresh(interval=30)
```

### Fallback Configuration

Gracefully handle service unavailability:

```python
# Create fallback config file
# config.json
{
  "database.host": "localhost",
  "database.port": 5432,
  "api.key": "fallback-key"
}

# Use fallback in client
client = ConfigClient(
    base_url="http://config-service/api/v1",
    app_id="my-app",
    environment="production",
    fallback_config_path="./config.json",  # Will use this if service is down
)
```

## Integration Patterns

### Django Integration

```python
# settings.py
import asyncio
from config_client import ConfigClient

# Initialize client
config_client = ConfigClient(
    base_url=os.getenv("CONFIG_SERVICE_URL"),
    app_id="django-app",
    environment=os.getenv("ENVIRONMENT", "development"),
)

# Fetch configs synchronously at startup
loop = asyncio.get_event_loop()
loop.run_until_complete(config_client.initialize())

# Use in settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config_client.get('database.name'),
        'USER': config_client.get('database.user'),
        'PASSWORD': config_client.get('database.password'),
        'HOST': config_client.get('database.host'),
        'PORT': config_client.get('database.port'),
    }
}

# Feature flags
FEATURE_NEW_UI = config_client.get('features.new_ui', default=False)
```

### FastAPI Integration

```python
# main.py
from fastapi import FastAPI, Depends
from config_client import ConfigClient

app = FastAPI()

# Global client instance
config_client = None

@app.on_event("startup")
async def startup():
    global config_client
    config_client = ConfigClient(
        base_url="http://config-service/api/v1",
        app_id="fastapi-app",
        environment="production",
    )
    await config_client.initialize()
    await config_client.start_auto_refresh(interval=60)

@app.on_event("shutdown")
async def shutdown():
    await config_client.close()

# Use in endpoints
@app.get("/")
async def root():
    max_items = config_client.get("api.max_items", default=100)
    return {"max_items": max_items}
```

### Flask Integration

```python
# app.py
from flask import Flask
from config_client import ConfigClient
import asyncio

app = Flask(__name__)

# Initialize client
config_client = ConfigClient(
    base_url="http://config-service/api/v1",
    app_id="flask-app",
    environment="production",
)

# Fetch configs at startup
loop = asyncio.get_event_loop()
loop.run_until_complete(config_client.initialize())

# Use in routes
@app.route('/')
def index():
    welcome_message = config_client.get('app.welcome_message', default='Welcome!')
    return welcome_message
```

### Celery Integration

```python
# celery_app.py
from celery import Celery
from config_client import ConfigClient
import asyncio

# Initialize client
config_client = ConfigClient(
    base_url="http://config-service/api/v1",
    app_id="celery-worker",
    environment="production",
)

loop = asyncio.get_event_loop()
loop.run_until_complete(config_client.initialize())

# Configure Celery
app = Celery('tasks')
app.conf.update(
    broker_url=config_client.get('celery.broker_url'),
    result_backend=config_client.get('celery.result_backend'),
    task_serializer='json',
    result_serializer='json',
)
```

## Best Practices

### 1. Initialize Once

Initialize the client once at application startup, not on every request:

```python
# ✅ Good
@app.on_event("startup")
async def startup():
    global config_client
    config_client = ConfigClient(...)
    await config_client.initialize()

# ❌ Bad
@app.get("/")
async def root():
    client = ConfigClient(...)  # Don't create new client per request
    await client.initialize()
```

### 2. Use Default Values

Always provide sensible defaults:

```python
# ✅ Good
timeout = client.get("api.timeout", default=30)

# ❌ Bad
timeout = client.get("api.timeout")  # Could be None
```

### 3. Handle Failures Gracefully

```python
try:
    await client.initialize()
except Exception as e:
    logger.error(f"Failed to fetch configs: {e}")
    # Use fallback or default values
```

### 4. Use Auto-Refresh

Enable auto-refresh for long-running applications:

```python
await client.start_auto_refresh(interval=60)
```

### 5. Register Change Listeners

React to configuration changes:

```python
def on_change(configs):
    # Reload components that depend on configs
    reload_cache()
    reload_rate_limits()

client.on_change(on_change)
```

## Environment Variables

Configure the client using environment variables:

```bash
export CONFIG_SERVICE_URL=http://config-service/api/v1
export APP_ID=my-app
export ENVIRONMENT=production
export CONFIG_CACHE_TTL=60
export CONFIG_FALLBACK_PATH=./config.json
```

```python
import os

client = ConfigClient(
    base_url=os.getenv("CONFIG_SERVICE_URL"),
    app_id=os.getenv("APP_ID"),
    environment=os.getenv("ENVIRONMENT"),
    cache_ttl=int(os.getenv("CONFIG_CACHE_TTL", "60")),
    fallback_config_path=os.getenv("CONFIG_FALLBACK_PATH"),
)
```

## Troubleshooting

### Client Can't Connect to Service

```python
# Check service URL
print(client.base_url)

# Test connectivity
import httpx
response = httpx.get(f"{client.base_url}/health")
print(response.status_code)
```

### Configs Not Updating

```python
# Check cache expiration
print(client._cache_expires_at)

# Force refresh
await client.refresh()

# Check version
print(client._version)
```

### High Latency

```python
# Increase cache TTL
client = ConfigClient(
    ...,
    cache_ttl=300,  # 5 minutes
)

# Use fallback for critical configs
client = ConfigClient(
    ...,
    fallback_config_path="./config.json",
)
```

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_config_fetch():
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "configs": {"key": "value"},
            "version": "abc123",
            "cache_ttl": 60
        }
        
        client = ConfigClient(
            base_url="http://test",
            app_id="test-app",
            environment="test"
        )
        await client.initialize()
        
        assert client.get("key") == "value"
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_real_service():
    client = ConfigClient(
        base_url="http://localhost:8000/api/v1",
        app_id="test-app",
        environment="development"
    )
    
    await client.initialize()
    
    # Verify configs loaded
    assert len(client.get_all()) > 0
    
    await client.close()
```

## Performance Optimization

### 1. Increase Cache TTL

```python
client = ConfigClient(..., cache_ttl=300)  # 5 minutes
```

### 2. Reduce Refresh Frequency

```python
await client.start_auto_refresh(interval=120)  # 2 minutes
```

### 3. Use Connection Pooling

The client uses httpx with connection pooling by default.

### 4. Fetch Only Required Keys

```python
# Future feature
configs = await client.fetch(keys=["database.host", "database.port"])
```

## Security Considerations

### 1. Secure Communication

Always use HTTPS in production:

```python
client = ConfigClient(
    base_url="https://config-service.example.com/api/v1",
    ...
)
```

### 2. Protect Fallback Files

```bash
chmod 600 config.json  # Only owner can read/write
```

### 3. Don't Log Sensitive Configs

```python
# ❌ Bad
logger.info(f"API Key: {client.get('api.key')}")

# ✅ Good
logger.info("API Key loaded successfully")
```

## Migration Guide

### From Environment Variables

```python
# Before
DB_HOST = os.getenv("DB_HOST", "localhost")

# After
DB_HOST = config_client.get("database.host", default="localhost")
```

### From Config Files

```python
# Before
with open("config.json") as f:
    config = json.load(f)
    DB_HOST = config["database"]["host"]

# After
DB_HOST = config_client.get("database.host")
```
