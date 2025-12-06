"""
Prometheus metrics for monitoring webhook platform.
"""
from prometheus_client import Counter, Histogram, Gauge

# Event publishing metrics
events_published_counter = Counter(
    "webhook_events_published_total",
    "Total number of events published",
    ["tenant_id", "event_type"]
)

events_duplicate_counter = Counter(
    "webhook_events_duplicate_total",
    "Total number of duplicate events (idempotency hits)",
    ["tenant_id"]
)

# Delivery metrics
delivery_attempts_counter = Counter(
    "webhook_delivery_attempts_total",
    "Total number of delivery attempts"
)

delivery_success_counter = Counter(
    "webhook_delivery_success_total",
    "Total number of successful deliveries"
)

delivery_failure_counter = Counter(
    "webhook_delivery_failure_total",
    "Total number of failed deliveries"
)

delivery_duration_histogram = Histogram(
    "webhook_delivery_duration_seconds",
    "Webhook delivery duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Rate limiting metrics
rate_limit_hits_counter = Counter(
    "webhook_rate_limit_hits_total",
    "Total number of rate limit hits",
    ["tenant_id"]
)

# DLQ metrics
dlq_size_gauge = Gauge(
    "webhook_dlq_size",
    "Number of unresolved entries in Dead Letter Queue"
)

# Tenant metrics
active_tenants_gauge = Gauge(
    "webhook_active_tenants",
    "Number of active tenants"
)

active_endpoints_gauge = Gauge(
    "webhook_active_endpoints",
    "Number of active webhook endpoints"
)
