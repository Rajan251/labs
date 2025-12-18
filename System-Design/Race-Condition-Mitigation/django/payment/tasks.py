from celery import shared_task
from django.core.cache import cache
import time
import functools

def single_instance_task(timeout=60 * 5):
    """
    Decorator to ensure that a task with the same arguments runs only one at a time.
    """
    def task_exc(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_id = "celery-lock-{}".format(func.__name__)
            # Include args in lock_id to allow different params to run concurrently
            # Simplified for demo: just function name
            
            acquire_lock = lambda: cache.add(lock_id, "true", timeout)
            release_lock = lambda: cache.delete(lock_id)
            
            if acquire_lock():
                try:
                    return func(*args, **kwargs)
                finally:
                    release_lock()
            else:
                return "Task is already running"
        return wrapper
    return task_exc

@shared_task
@single_instance_task(timeout=60)
def process_audit_log(user_id):
    """
    Example background task that should not overlap for the same purpose.
    """
    print(f"Processing audit log for {user_id}")
    time.sleep(2)
    return "Done"
