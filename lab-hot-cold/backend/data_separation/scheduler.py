"""
Automated Scheduler for Data Migration

This module provides Celery tasks for automated data migration.
Can be scheduled to run daily, weekly, or monthly.
"""

from datetime import datetime
import logging

# Note: This requires Celery to be installed and configured
# pip install celery redis

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    print("Warning: Celery not installed. Scheduler will not work.")

from .migrator import DataMigrator
from .config import SCHEDULER_CONFIG, COLLECTIONS_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery app
if CELERY_AVAILABLE:
    app = Celery(
        'data_migration_scheduler',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )
    
    # Celery configuration
    app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
    )


async def run_migration():
    """Run the migration process"""
    migrator = DataMigrator()
    
    try:
        await migrator.connect()
        
        logger.info("="*70)
        logger.info("AUTOMATED DATA MIGRATION STARTED")
        logger.info(f"Time: {datetime.utcnow().isoformat()}")
        logger.info("="*70)
        
        results = await migrator.migrate_all(dry_run=False)
        
        # Log results
        total_migrated = 0
        total_failed = 0
        
        for collection, stats in results.items():
            logger.info(f"\n{collection}:")
            logger.info(f"  Migrated: {stats['migrated']}")
            logger.info(f"  Failed: {stats['failed']}")
            
            total_migrated += stats['migrated']
            total_failed += stats['failed']
        
        logger.info(f"\nTOTAL:")
        logger.info(f"  Migrated: {total_migrated}")
        logger.info(f"  Failed: {total_failed}")
        
        logger.info("="*70)
        logger.info("AUTOMATED DATA MIGRATION COMPLETED")
        logger.info("="*70)
        
        # Send notification if configured
        if SCHEDULER_CONFIG.get('notification_email'):
            await send_notification(total_migrated, total_failed)
        
        return {
            'status': 'success',
            'migrated': total_migrated,
            'failed': total_failed,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    finally:
        await migrator.disconnect()


async def send_notification(migrated: int, failed: int):
    """Send email notification about migration results"""
    # TODO: Implement email notification
    # You can use services like SendGrid, AWS SES, etc.
    logger.info(f"Notification: Migrated {migrated}, Failed {failed}")


if CELERY_AVAILABLE:
    @app.task(name='migrate_cold_data')
    def migrate_cold_data_task():
        """Celery task for data migration"""
        import asyncio
        return asyncio.run(run_migration())
    
    
    @app.task(name='analyze_data_distribution')
    def analyze_data_distribution_task():
        """Celery task for analyzing data distribution"""
        # TODO: Implement analysis task
        logger.info("Running data distribution analysis...")
        return {'status': 'completed'}
    
    
    # Schedule configuration
    app.conf.beat_schedule = {
        'migrate-cold-data-daily': {
            'task': 'migrate_cold_data',
            'schedule': 86400.0,  # 24 hours in seconds
            'options': {'expires': 3600}
        },
    }


# Manual trigger function (without Celery)
def trigger_migration_sync():
    """
    Synchronous function to trigger migration manually
    Can be called from Django management command or FastAPI endpoint
    """
    import asyncio
    return asyncio.run(run_migration())


if __name__ == '__main__':
    # For testing
    import asyncio
    result = asyncio.run(run_migration())
    print(result)
