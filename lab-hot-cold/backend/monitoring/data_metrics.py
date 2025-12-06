"""
Data Metrics and Monitoring

This module tracks metrics about hot-cold data separation including:
- Storage usage
- Query performance
- Migration statistics
- Access patterns
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import logging

from data_separation.config import (
    HOT_DB_CONFIG,
    COLD_DB_CONFIG,
    MONITORING_CONFIG,
    COLLECTIONS_CONFIG,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMetrics:
    """
    Track and analyze metrics for hot-cold data separation
    """
    
    def __init__(self):
        self.hot_client: Optional[AsyncIOMotorClient] = None
        self.cold_client: Optional[AsyncIOMotorClient] = None
    
    async def connect(self):
        """Connect to databases"""
        self.hot_client = AsyncIOMotorClient(HOT_DB_CONFIG['uri'])
        self.cold_client = AsyncIOMotorClient(COLD_DB_CONFIG['uri'])
    
    async def disconnect(self):
        """Disconnect from databases"""
        if self.hot_client:
            self.hot_client.close()
        if self.cold_client:
            self.cold_client.close()
    
    async def get_storage_metrics(self) -> Dict:
        """
        Get storage usage metrics for hot and cold databases
        
        Returns:
            Dictionary with storage metrics
        """
        hot_db = self.hot_client[HOT_DB_CONFIG['database']]
        cold_db = self.cold_client[COLD_DB_CONFIG['database']]
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'hot': {},
            'cold': {},
            'total': {},
        }
        
        hot_total_size = 0
        cold_total_size = 0
        hot_total_docs = 0
        cold_total_docs = 0
        
        for collection_name, config in COLLECTIONS_CONFIG.items():
            if not config.get('enabled', False):
                continue
            
            hot_collection = config['hot_collection']
            cold_collection = config['cold_collection']
            
            # Get hot stats
            try:
                hot_stats = await hot_db.command('collStats', hot_collection)
                hot_size = hot_stats.get('size', 0)
                hot_count = hot_stats.get('count', 0)
                
                metrics['hot'][collection_name] = {
                    'size_bytes': hot_size,
                    'size_mb': hot_size / (1024 * 1024),
                    'document_count': hot_count,
                }
                
                hot_total_size += hot_size
                hot_total_docs += hot_count
            except:
                metrics['hot'][collection_name] = {'error': 'Collection not found'}
            
            # Get cold stats
            try:
                cold_stats = await cold_db.command('collStats', cold_collection)
                cold_size = cold_stats.get('size', 0)
                cold_count = cold_stats.get('count', 0)
                
                metrics['cold'][collection_name] = {
                    'size_bytes': cold_size,
                    'size_mb': cold_size / (1024 * 1024),
                    'document_count': cold_count,
                }
                
                cold_total_size += cold_size
                cold_total_docs += cold_count
            except:
                metrics['cold'][collection_name] = {'error': 'Collection not found'}
        
        # Calculate totals
        metrics['total'] = {
            'hot_size_gb': hot_total_size / (1024 * 1024 * 1024),
            'cold_size_gb': cold_total_size / (1024 * 1024 * 1024),
            'total_size_gb': (hot_total_size + cold_total_size) / (1024 * 1024 * 1024),
            'hot_documents': hot_total_docs,
            'cold_documents': cold_total_docs,
            'total_documents': hot_total_docs + cold_total_docs,
        }
        
        # Check alerts
        if metrics['total']['hot_size_gb'] > MONITORING_CONFIG['alert_threshold_gb']:
            metrics['alerts'] = [
                f"Hot storage exceeds threshold: {metrics['total']['hot_size_gb']:.2f} GB"
            ]
        
        return metrics
    
    async def get_distribution_metrics(self) -> Dict:
        """
        Get data distribution metrics
        
        Returns:
            Dictionary with distribution percentages
        """
        hot_db = self.hot_client[HOT_DB_CONFIG['database']]
        cold_db = self.cold_client[COLD_DB_CONFIG['database']]
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'collections': {},
        }
        
        for collection_name, config in COLLECTIONS_CONFIG.items():
            if not config.get('enabled', False):
                continue
            
            hot_collection = config['hot_collection']
            cold_collection = config['cold_collection']
            
            hot_count = await hot_db[hot_collection].count_documents({})
            cold_count = await cold_db[cold_collection].count_documents({})
            total = hot_count + cold_count
            
            metrics['collections'][collection_name] = {
                'hot_count': hot_count,
                'cold_count': cold_count,
                'total_count': total,
                'hot_percentage': (hot_count / total * 100) if total > 0 else 0,
                'cold_percentage': (cold_count / total * 100) if total > 0 else 0,
            }
        
        return metrics
    
    async def log_migration_event(
        self,
        collection: str,
        migrated_count: int,
        failed_count: int,
        duration_seconds: float
    ):
        """
        Log a migration event to the metrics collection
        
        Args:
            collection: Collection name
            migrated_count: Number of documents migrated
            failed_count: Number of failed migrations
            duration_seconds: Time taken for migration
        """
        if not MONITORING_CONFIG['enabled']:
            return
        
        hot_db = self.hot_client[HOT_DB_CONFIG['database']]
        metrics_coll = hot_db[MONITORING_CONFIG['metrics_collection']]
        
        event = {
            'event_type': 'migration',
            'timestamp': datetime.utcnow(),
            'collection': collection,
            'migrated_count': migrated_count,
            'failed_count': failed_count,
            'duration_seconds': duration_seconds,
            'success_rate': (migrated_count / (migrated_count + failed_count) * 100)
                if (migrated_count + failed_count) > 0 else 0,
        }
        
        await metrics_coll.insert_one(event)
        logger.info(f"Logged migration event for {collection}")
    
    async def log_query_performance(
        self,
        collection: str,
        query_type: str,
        storage_location: str,  # 'hot' or 'cold'
        duration_ms: float
    ):
        """
        Log query performance metrics
        
        Args:
            collection: Collection name
            query_type: Type of query (find_one, find, count, etc.)
            storage_location: Where the data was found
            duration_ms: Query duration in milliseconds
        """
        if not MONITORING_CONFIG['enabled'] or not MONITORING_CONFIG['track_query_performance']:
            return
        
        hot_db = self.hot_client[HOT_DB_CONFIG['database']]
        metrics_coll = hot_db[MONITORING_CONFIG['metrics_collection']]
        
        event = {
            'event_type': 'query_performance',
            'timestamp': datetime.utcnow(),
            'collection': collection,
            'query_type': query_type,
            'storage_location': storage_location,
            'duration_ms': duration_ms,
        }
        
        await metrics_coll.insert_one(event)
    
    async def get_migration_history(
        self,
        days: int = 7
    ) -> List[Dict]:
        """
        Get migration history for the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of migration events
        """
        hot_db = self.hot_client[HOT_DB_CONFIG['database']]
        metrics_coll = hot_db[MONITORING_CONFIG['metrics_collection']]
        
        since = datetime.utcnow() - timedelta(days=days)
        
        cursor = metrics_coll.find({
            'event_type': 'migration',
            'timestamp': {'$gte': since}
        }).sort('timestamp', -1)
        
        return await cursor.to_list(length=100)
    
    async def get_performance_summary(
        self,
        collection: str = None,
        days: int = 7
    ) -> Dict:
        """
        Get query performance summary
        
        Args:
            collection: Optional collection filter
            days: Number of days to analyze
            
        Returns:
            Performance summary statistics
        """
        hot_db = self.hot_client[HOT_DB_CONFIG['database']]
        metrics_coll = hot_db[MONITORING_CONFIG['metrics_collection']]
        
        since = datetime.utcnow() - timedelta(days=days)
        
        match_filter = {
            'event_type': 'query_performance',
            'timestamp': {'$gte': since}
        }
        
        if collection:
            match_filter['collection'] = collection
        
        # Aggregate performance metrics
        pipeline = [
            {'$match': match_filter},
            {
                '$group': {
                    '_id': {
                        'collection': '$collection',
                        'storage_location': '$storage_location'
                    },
                    'avg_duration_ms': {'$avg': '$duration_ms'},
                    'max_duration_ms': {'$max': '$duration_ms'},
                    'min_duration_ms': {'$min': '$duration_ms'},
                    'query_count': {'$sum': 1}
                }
            }
        ]
        
        results = await metrics_coll.aggregate(pipeline).to_list(length=100)
        
        summary = {
            'period_days': days,
            'results': results,
        }
        
        return summary


# Convenience function
async def get_current_metrics() -> Dict:
    """Get current storage and distribution metrics"""
    metrics = DataMetrics()
    try:
        await metrics.connect()
        storage = await metrics.get_storage_metrics()
        distribution = await metrics.get_distribution_metrics()
        
        return {
            'storage': storage,
            'distribution': distribution,
        }
    finally:
        await metrics.disconnect()
