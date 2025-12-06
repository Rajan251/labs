"""
Example test file for event service.
"""
import pytest
from app.services.event_service import EventService
from app.schemas import EventPublish


def test_generate_idempotency_key():
    """Test idempotency key generation."""
    key1 = EventService.generate_idempotency_key("evt_123", 1)
    key2 = EventService.generate_idempotency_key("evt_123", 1)
    key3 = EventService.generate_idempotency_key("evt_123", 2)
    
    # Same event + tenant = same key
    assert key1 == key2
    
    # Different tenant = different key
    assert key1 != key3
    
    # Key should be SHA256 hash (64 hex characters)
    assert len(key1) == 64


def test_check_duplicate():
    """Test duplicate event detection."""
    # This would require database setup
    # See integration tests for full implementation
    pass
