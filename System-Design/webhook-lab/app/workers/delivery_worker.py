"""
Celery worker for webhook delivery with retry logic.

Implements exponential backoff retry strategy and handles delivery failures.
"""
import httpx
import time
from datetime import datetime, timedelta
from typing import Optional

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import DeliveryStatus
from app.services.event_service import EventService
from app.services.dlq_service import DLQService
from app.services.signature_service import SignatureService
from app.config import settings
from app.monitoring.metrics import (
    delivery_attempts_counter,
    delivery_success_counter,
    delivery_failure_counter,
    delivery_duration_histogram,
    dlq_size_gauge
)


@celery_app.task(
    bind=True,
    max_retries=settings.max_retry_attempts,
    default_retry_delay=settings.initial_retry_delay
)
def deliver_webhook(
    self,
    event_id: int,
    endpoint_id: int,
    endpoint_url: str,
    secret_key: str,
    payload: dict,
    attempt_number: int = 1
):
    """
    Deliver webhook to endpoint with exponential backoff retry.
    
    Args:
        self: Celery task instance (bound)
        event_id: Event ID
        endpoint_id: Webhook endpoint ID
        endpoint_url: Target URL
        secret_key: Tenant's secret key for HMAC
        payload: Event payload
        attempt_number: Current attempt number
        
    Retry Strategy:
        - Attempt 1: Immediate
        - Attempt 2: 1s delay
        - Attempt 3: 2s delay
        - Attempt 4: 4s delay
        - Attempt 5: 8s delay
        - Attempt 6: 16s delay
        - Attempt 7: 32s delay (max)
        
    After max retries, event is moved to Dead Letter Queue.
    """
    db = SessionLocal()
    start_time = time.time()
    
    try:
        # Generate HMAC signature
        signature = SignatureService.generate_signature(payload, secret_key)
        signature_header = SignatureService.create_signature_header(signature)
        
        # Prepare webhook request
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature_header,
            "X-Webhook-Event-Id": payload.get("event_id", ""),
            "X-Webhook-Event-Type": payload.get("event_type", ""),
            "X-Webhook-Delivery-Attempt": str(attempt_number),
            "User-Agent": f"{settings.app_name}/{settings.app_version}"
        }
        
        # Make HTTP request with timeout
        with httpx.Client(timeout=settings.webhook_timeout) as client:
            response = client.post(
                endpoint_url,
                json=payload,
                headers=headers
            )
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Record metrics
        delivery_attempts_counter.inc()
        delivery_duration_histogram.observe(duration_ms / 1000)
        
        # Check if delivery was successful (2xx status code)
        if 200 <= response.status_code < 300:
            # Success!
            EventService.record_delivery_attempt(
                db,
                event_id=event_id,
                endpoint_id=endpoint_id,
                attempt_number=attempt_number,
                status=DeliveryStatus.SUCCESS,
                http_status_code=response.status_code,
                response_body=response.text[:1000],  # Limit to 1000 chars
                duration_ms=duration_ms
            )
            
            # Update event status
            EventService.update_event_status(db, event_id, DeliveryStatus.SUCCESS)
            
            # Record success metric
            delivery_success_counter.inc()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "attempt": attempt_number,
                "duration_ms": duration_ms
            }
        
        else:
            # Non-2xx response, will retry
            raise Exception(
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
    
    except Exception as exc:
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Record metrics
        delivery_attempts_counter.inc()
        delivery_failure_counter.inc()
        
        # Calculate next retry delay with exponential backoff
        retry_delay = min(
            settings.initial_retry_delay * (2 ** (attempt_number - 1)),
            settings.max_retry_delay
        )
        
        next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
        
        # Record failed attempt
        EventService.record_delivery_attempt(
            db,
            event_id=event_id,
            endpoint_id=endpoint_id,
            attempt_number=attempt_number,
            status=DeliveryStatus.FAILED,
            http_status_code=getattr(exc, 'response', None) and exc.response.status_code,
            error_message=str(exc)[:1000],
            duration_ms=duration_ms,
            next_retry_at=next_retry_at
        )
        
        # Update event status
        EventService.update_event_status(db, event_id, DeliveryStatus.RETRYING)
        
        # Check if we've exhausted retries
        if attempt_number >= settings.max_retry_attempts:
            # Move to Dead Letter Queue
            DLQService.add_to_dlq(
                db,
                event_id=event_id,
                endpoint_id=endpoint_id,
                total_attempts=attempt_number,
                last_error=str(exc)[:1000],
                last_http_status=getattr(exc, 'response', None) and exc.response.status_code
            )
            
            # Update event status to failed
            EventService.update_event_status(db, event_id, DeliveryStatus.FAILED)
            
            # Update DLQ size metric
            dlq_stats = DLQService.get_dlq_stats(db)
            dlq_size_gauge.set(dlq_stats["unresolved"])
            
            raise Exception(
                f"Max retries ({settings.max_retry_attempts}) exceeded. "
                f"Event moved to DLQ. Last error: {str(exc)[:200]}"
            )
        
        else:
            # Retry with exponential backoff
            raise self.retry(
                exc=exc,
                countdown=retry_delay,
                kwargs={
                    "event_id": event_id,
                    "endpoint_id": endpoint_id,
                    "endpoint_url": endpoint_url,
                    "secret_key": secret_key,
                    "payload": payload,
                    "attempt_number": attempt_number + 1
                }
            )
    
    finally:
        db.close()


@celery_app.task
def retry_from_dlq(dlq_id: int):
    """
    Retry a failed event from the Dead Letter Queue.
    
    Args:
        dlq_id: DLQ entry ID
    """
    db = SessionLocal()
    
    try:
        # Get DLQ entry
        dlq_entry = DLQService.get_dlq_entry(db, dlq_id)
        if not dlq_entry:
            raise ValueError(f"DLQ entry {dlq_id} not found")
        
        # Get event and endpoint details
        event = EventService.get_event_by_id(db, dlq_entry.event_id)
        if not event:
            raise ValueError(f"Event {dlq_entry.event_id} not found")
        
        from app.services.tenant_service import TenantService
        endpoint = TenantService.get_endpoint_by_id(db, dlq_entry.endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint {dlq_entry.endpoint_id} not found")
        
        tenant = TenantService.get_tenant_by_id(db, event.tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {event.tenant_id} not found")
        
        # Reset event status
        EventService.update_event_status(db, event.id, DeliveryStatus.PENDING)
        
        # Mark DLQ entry as resolved
        DLQService.mark_as_resolved(db, dlq_id)
        
        # Trigger new delivery attempt
        deliver_webhook.delay(
            event_id=event.id,
            endpoint_id=endpoint.id,
            endpoint_url=endpoint.url,
            secret_key=tenant.secret_key,
            payload=event.payload,
            attempt_number=1  # Start fresh
        )
        
        return {"success": True, "dlq_id": dlq_id, "event_id": event.id}
    
    finally:
        db.close()
