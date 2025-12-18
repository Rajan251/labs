from django.dispatch import Signal, receiver
from django.db import transaction
from .tasks import process_audit_log

# Define a custom signal
payment_processed = Signal()

@receiver(payment_processed)
def handle_payment_processed(sender, **kwargs):
    user_id = kwargs.get('user_id')
    # Use transaction.on_commit to ensure the DB transaction is durable 
    # before triggering side effects (like Celery tasks).
    transaction.on_commit(lambda: process_audit_log.delay(user_id))
