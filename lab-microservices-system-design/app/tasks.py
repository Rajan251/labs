"""
Celery tasks for async processing
Heavy operations that run in background workers
"""
import os
import time
import logging
from datetime import datetime
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.celery_app import celery_app
from app.database import get_task_results_collection

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"Task {task_id} failed: {exc}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"Task {task_id} retrying: {exc}")


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.process_heavy_task",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def process_heavy_task(self, data: str, iterations: int = 10):
    """
    Example heavy processing task
    Simulates CPU-intensive operation and stores result in MongoDB
    
    Args:
        data: Input data to process
        iterations: Number of iterations (simulates workload)
    
    Returns:
        dict: Processing result
    """
    task_id = self.request.id
    logger.info(f"Starting heavy task {task_id}: data={data}, iterations={iterations}")
    
    try:
        result = {
            "task_id": task_id,
            "input_data": data,
            "iterations": iterations,
            "started_at": datetime.utcnow().isoformat(),
            "status": "processing"
        }
        
        # Simulate heavy processing with progress updates
        processed_items = []
        
        for i in range(iterations):
            try:
                # Check for soft time limit
                if self.request.called_directly:
                    pass  # Skip time limit check for direct calls
                
                # Simulate CPU work
                time.sleep(0.5)  # Simulate processing time
                
                # Process data (example: uppercase transformation)
                processed = f"{data.upper()}_ITERATION_{i+1}"
                processed_items.append(processed)
                
                # Update progress (visible in task status)
                progress = int((i + 1) / iterations * 100)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': iterations,
                        'progress': progress,
                        'status': f'Processing iteration {i+1}/{iterations}'
                    }
                )
                
                logger.debug(f"Task {task_id}: {progress}% complete")
                
            except SoftTimeLimitExceeded:
                logger.warning(f"Task {task_id} soft time limit exceeded")
                result["status"] = "timeout"
                result["error"] = "Task exceeded time limit"
                raise
        
        # Task completed successfully
        result["status"] = "completed"
        result["completed_at"] = datetime.utcnow().isoformat()
        result["processed_items"] = processed_items
        result["total_processed"] = len(processed_items)
        
        # Store result in MongoDB
        try:
            collection = get_task_results_collection()
            collection.insert_one({
                "task_id": task_id,
                "result": result,
                "created_at": datetime.utcnow()
            })
            logger.info(f"Task {task_id} result stored in MongoDB")
        except Exception as e:
            logger.error(f"Failed to store task result in MongoDB: {e}")
            # Don't fail the task if storage fails
        
        logger.info(f"Task {task_id} completed: processed {len(processed_items)} items")
        
        return result
        
    except SoftTimeLimitExceeded:
        logger.error(f"Task {task_id} exceeded soft time limit")
        raise
    
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        
        # Store error in MongoDB
        try:
            collection = get_task_results_collection()
            collection.insert_one({
                "task_id": task_id,
                "error": str(e),
                "status": "failed",
                "created_at": datetime.utcnow()
            })
        except Exception as store_error:
            logger.error(f"Failed to store error in MongoDB: {store_error}")
        
        # Retry the task
        raise self.retry(exc=e, countdown=60)


@celery_app.task(
    bind=True,
    name="app.tasks.scheduled_cleanup_task",
    max_retries=2
)
def scheduled_cleanup_task(self):
    """
    Scheduled task to clean up old records
    Runs daily at 2 AM (configured in celery_app.py)
    """
    task_id = self.request.id
    logger.info(f"Starting cleanup task {task_id}")
    
    try:
        from datetime import timedelta
        
        # Clean up task results older than 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        collection = get_task_results_collection()
        result = collection.delete_many({
            "created_at": {"$lt": cutoff_date}
        })
        
        deleted_count = result.deleted_count
        logger.info(f"Cleanup task {task_id}: deleted {deleted_count} old records")
        
        return {
            "task_id": task_id,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cleanup task {task_id} failed: {e}", exc_info=True)
        raise


@celery_app.task(
    bind=True,
    name="app.tasks.batch_process_task",
    max_retries=3
)
def batch_process_task(self, items: list):
    """
    Example batch processing task
    Processes multiple items in a single task
    
    Args:
        items: List of items to process
    
    Returns:
        dict: Batch processing result
    """
    task_id = self.request.id
    logger.info(f"Starting batch task {task_id}: {len(items)} items")
    
    try:
        processed = []
        failed = []
        
        for idx, item in enumerate(items):
            try:
                # Simulate processing
                time.sleep(0.1)
                processed.append({
                    "item": item,
                    "result": f"processed_{item}",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Update progress
                progress = int((idx + 1) / len(items) * 100)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': idx + 1,
                        'total': len(items),
                        'progress': progress
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to process item {item}: {e}")
                failed.append({"item": item, "error": str(e)})
        
        result = {
            "task_id": task_id,
            "total_items": len(items),
            "processed": len(processed),
            "failed": len(failed),
            "failed_items": failed,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Batch task {task_id} completed: {len(processed)}/{len(items)} successful")
        
        return result
        
    except Exception as e:
        logger.error(f"Batch task {task_id} failed: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)
