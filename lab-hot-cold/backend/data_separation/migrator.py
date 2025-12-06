"""
Data Migrator - Handles migration of data between hot and cold storage

This module provides functionality to migrate data from hot (active) storage
to cold (archive) storage based on configured policies.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging

from .config import (
    HOT_DB_CONFIG,
    COLD_DB_CONFIG,
    COLLECTIONS_CONFIG,
    MIGRATION_CONFIG,
    TIME_BASED_POLICY,
    ACCESS_BASED_POLICY,
    HYBRID_POLICY,
    get_collection_config,
    is_collection_enabled,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMigrator:
    """
    Handles migration of data from hot to cold storage
    
    Methods:
        - migrate_collection: Migrate a specific collection
        - migrate_all: Migrate all configured collections
        - restore_to_hot: Restore data from cold to hot
        - verify_migration: Verify data integrity after migration
    """
    
    def __init__(self):
        """Initialize migrator with database connections"""
        self.hot_client: Optional[AsyncIOMotorClient] = None
        self.cold_client: Optional[AsyncIOMotorClient] = None
        self.hot_db: Optional[AsyncIOMotorDatabase] = None
        self.cold_db: Optional[AsyncIOMotorDatabase] = None
        self.stats = {
            'migrated': 0,
            'failed': 0,
            'skipped': 0,
        }
    
    async def connect(self):
        """Establish connections to both hot and cold databases"""
        try:
            self.hot_client = AsyncIOMotorClient(HOT_DB_CONFIG['uri'])
            self.cold_client = AsyncIOMotorClient(COLD_DB_CONFIG['uri'])
            
            self.hot_db = self.hot_client[HOT_DB_CONFIG['database']]
            self.cold_db = self.cold_client[COLD_DB_CONFIG['database']]
            
            # Test connections
            await self.hot_client.admin.command('ping')
            await self.cold_client.admin.command('ping')
            
            logger.info("✓ Connected to hot and cold databases")
        except Exception as e:
            logger.error(f"✗ Failed to connect to databases: {e}")
            raise
    
    async def disconnect(self):
        """Close database connections"""
        if self.hot_client:
            self.hot_client.close()
        if self.cold_client:
            self.cold_client.close()
        logger.info("✓ Disconnected from databases")
    
    def _get_migration_query(self, collection_name: str) -> Dict:
        """
        Build query to identify records for migration
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            MongoDB query dict
        """
        config = get_collection_config(collection_name)
        policy = config.get('policy', 'time_based')
        date_field = config.get('date_field')
        access_field = config.get('access_field')
        
        query = {}
        
        if policy == 'time_based':
            # Migrate data older than threshold
            threshold_date = datetime.utcnow() - timedelta(
                days=TIME_BASED_POLICY['cold_threshold_days']
            )
            query[date_field] = {'$lt': threshold_date}
            
        elif policy == 'access_based':
            # Migrate data not accessed recently
            if access_field:
                threshold_date = datetime.utcnow() - timedelta(
                    days=ACCESS_BASED_POLICY['cold_access_days']
                )
                query[access_field] = {'$lt': threshold_date}
                
        elif policy == 'hybrid':
            # Combine age and access patterns
            if HYBRID_POLICY['enabled']:
                age_threshold = datetime.utcnow() - timedelta(
                    days=HYBRID_POLICY['min_age_days']
                )
                inactive_threshold = datetime.utcnow() - timedelta(
                    days=HYBRID_POLICY['min_inactive_days']
                )
                
                query['$and'] = [
                    {date_field: {'$lt': age_threshold}},
                ]
                
                if access_field:
                    query['$and'].append(
                        {access_field: {'$lt': inactive_threshold}}
                    )
        
        return query
    
    async def migrate_collection(
        self,
        collection_name: str,
        dry_run: bool = None
    ) -> Dict[str, int]:
        """
        Migrate a specific collection from hot to cold storage
        
        Args:
            collection_name: Name of the collection to migrate
            dry_run: If True, only simulate migration without actual data movement
            
        Returns:
            Dictionary with migration statistics
        """
        if dry_run is None:
            dry_run = MIGRATION_CONFIG['dry_run']
        
        if not is_collection_enabled(collection_name):
            logger.warning(f"⚠ Collection '{collection_name}' not enabled for migration")
            return {'migrated': 0, 'failed': 0, 'skipped': 0}
        
        config = get_collection_config(collection_name)
        hot_collection = config['hot_collection']
        cold_collection = config['cold_collection']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Migrating collection: {collection_name}")
        logger.info(f"Policy: {config['policy']}")
        logger.info(f"Dry run: {dry_run}")
        logger.info(f"{'='*60}\n")
        
        # Build migration query
        query = self._get_migration_query(collection_name)
        
        # Count records to migrate
        hot_coll = self.hot_db[hot_collection]
        total_count = await hot_coll.count_documents(query)
        
        logger.info(f"Found {total_count} records to migrate")
        
        if total_count == 0:
            return {'migrated': 0, 'failed': 0, 'skipped': 0}
        
        if dry_run:
            logger.info(f"DRY RUN: Would migrate {total_count} records")
            return {'migrated': 0, 'failed': 0, 'skipped': total_count}
        
        # Migrate in batches
        batch_size = MIGRATION_CONFIG['batch_size']
        migrated = 0
        failed = 0
        
        cursor = hot_coll.find(query).batch_size(batch_size)
        batch = []
        
        async for document in cursor:
            batch.append(document)
            
            if len(batch) >= batch_size:
                success = await self._migrate_batch(
                    batch, hot_collection, cold_collection
                )
                migrated += success
                failed += len(batch) - success
                batch = []
                
                logger.info(f"Progress: {migrated}/{total_count} migrated")
        
        # Migrate remaining documents
        if batch:
            success = await self._migrate_batch(
                batch, hot_collection, cold_collection
            )
            migrated += success
            failed += len(batch) - success
        
        logger.info(f"\n✓ Migration complete:")
        logger.info(f"  - Migrated: {migrated}")
        logger.info(f"  - Failed: {failed}")
        
        return {'migrated': migrated, 'failed': failed, 'skipped': 0}
    
    async def _migrate_batch(
        self,
        documents: List[Dict],
        hot_collection: str,
        cold_collection: str
    ) -> int:
        """
        Migrate a batch of documents
        
        Args:
            documents: List of documents to migrate
            hot_collection: Source collection name
            cold_collection: Destination collection name
            
        Returns:
            Number of successfully migrated documents
        """
        if not documents:
            return 0
        
        try:
            # Add migration metadata
            now = datetime.utcnow()
            for doc in documents:
                doc['_migrated_at'] = now
                doc['_migrated_from'] = 'hot'
            
            # Insert into cold storage
            cold_coll = self.cold_db[cold_collection]
            result = await cold_coll.insert_many(documents, ordered=False)
            
            inserted_count = len(result.inserted_ids)
            
            # Verify and delete from hot storage
            if MIGRATION_CONFIG['verify_migration'] and inserted_count > 0:
                if MIGRATION_CONFIG['delete_after_migration']:
                    doc_ids = [doc['_id'] for doc in documents[:inserted_count]]
                    hot_coll = self.hot_db[hot_collection]
                    await hot_coll.delete_many({'_id': {'$in': doc_ids}})
            
            return inserted_count
            
        except Exception as e:
            logger.error(f"✗ Batch migration failed: {e}")
            return 0
    
    async def migrate_all(self, dry_run: bool = None) -> Dict[str, Dict]:
        """
        Migrate all enabled collections
        
        Args:
            dry_run: If True, only simulate migration
            
        Returns:
            Dictionary with statistics for each collection
        """
        results = {}
        
        for collection_name, config in COLLECTIONS_CONFIG.items():
            if config.get('enabled', False):
                stats = await self.migrate_collection(collection_name, dry_run)
                results[collection_name] = stats
        
        return results
    
    async def restore_to_hot(
        self,
        collection_name: str,
        query: Dict,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Restore data from cold to hot storage
        
        Args:
            collection_name: Name of the collection
            query: Query to identify records to restore
            dry_run: If True, only simulate restoration
            
        Returns:
            Dictionary with restoration statistics
        """
        if not is_collection_enabled(collection_name):
            logger.warning(f"⚠ Collection '{collection_name}' not enabled")
            return {'restored': 0, 'failed': 0}
        
        config = get_collection_config(collection_name)
        hot_collection = config['hot_collection']
        cold_collection = config['cold_collection']
        
        logger.info(f"\nRestoring data to hot storage: {collection_name}")
        
        cold_coll = self.cold_db[cold_collection]
        total_count = await cold_coll.count_documents(query)
        
        logger.info(f"Found {total_count} records to restore")
        
        if total_count == 0:
            return {'restored': 0, 'failed': 0}
        
        if dry_run:
            logger.info(f"DRY RUN: Would restore {total_count} records")
            return {'restored': 0, 'failed': 0}
        
        # Restore in batches
        batch_size = MIGRATION_CONFIG['batch_size']
        restored = 0
        failed = 0
        
        cursor = cold_coll.find(query).batch_size(batch_size)
        batch = []
        
        async for document in cursor:
            # Remove migration metadata
            document.pop('_migrated_at', None)
            document.pop('_migrated_from', None)
            batch.append(document)
            
            if len(batch) >= batch_size:
                try:
                    hot_coll = self.hot_db[hot_collection]
                    result = await hot_coll.insert_many(batch, ordered=False)
                    restored += len(result.inserted_ids)
                    
                    # Delete from cold storage
                    doc_ids = [doc['_id'] for doc in batch]
                    await cold_coll.delete_many({'_id': {'$in': doc_ids}})
                    
                except Exception as e:
                    logger.error(f"✗ Batch restoration failed: {e}")
                    failed += len(batch)
                
                batch = []
        
        # Restore remaining documents
        if batch:
            try:
                hot_coll = self.hot_db[hot_collection]
                result = await hot_coll.insert_many(batch, ordered=False)
                restored += len(result.inserted_ids)
                
                doc_ids = [doc['_id'] for doc in batch]
                await cold_coll.delete_many({'_id': {'$in': doc_ids}})
                
            except Exception as e:
                logger.error(f"✗ Final batch restoration failed: {e}")
                failed += len(batch)
        
        logger.info(f"\n✓ Restoration complete:")
        logger.info(f"  - Restored: {restored}")
        logger.info(f"  - Failed: {failed}")
        
        return {'restored': restored, 'failed': failed}


# Convenience function for quick migration
async def quick_migrate(collection_name: str, dry_run: bool = True):
    """
    Quick migration function for a single collection
    
    Args:
        collection_name: Name of collection to migrate
        dry_run: If True, only simulate migration
    """
    migrator = DataMigrator()
    try:
        await migrator.connect()
        result = await migrator.migrate_collection(collection_name, dry_run)
        return result
    finally:
        await migrator.disconnect()
