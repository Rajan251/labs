"""
Hybrid Migrator - MongoDB Hot + Cloud Cold Storage

This migrator moves data from MongoDB (hot) to Cloud Storage (cold)
while keeping metadata in MongoDB for fast lookups.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import logging

from .config import (
    HOT_DB_CONFIG,
    COLD_CLOUD_CONFIG,
    COLLECTIONS_CONFIG,
    MIGRATION_CONFIG,
    TIME_BASED_POLICY,
    get_collection_config,
)
from .cloud_storage import get_cloud_adapter, build_storage_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridMigrator:
    """
    Migrates data from MongoDB (hot) to Cloud Storage (cold)
    
    Strategy:
    1. Full document stored in cloud (S3/MinIO/GCS)
    2. Metadata kept in MongoDB for fast queries
    3. Actual data fetched from cloud when needed
    """
    
    def __init__(self):
        self.hot_client: Optional[AsyncIOMotorClient] = None
        self.hot_db = None
        self.cloud_adapter = None
        self.metadata_db = None  # MongoDB for cold metadata
        
    async def connect(self):
        """Connect to MongoDB and Cloud Storage"""
        try:
            # Connect to hot MongoDB
            self.hot_client = AsyncIOMotorClient(HOT_DB_CONFIG['uri'])
            self.hot_db = self.hot_client[HOT_DB_CONFIG['database']]
            
            # Use same MongoDB for metadata
            self.metadata_db = self.hot_db
            
            # Initialize cloud storage adapter
            if COLD_CLOUD_CONFIG['enabled']:
                self.cloud_adapter = get_cloud_adapter(COLD_CLOUD_CONFIG)
            
            # Test connections
            await self.hot_client.admin.command('ping')
            
            logger.info("✓ Connected to MongoDB (hot)")
            logger.info(f"✓ Connected to {COLD_CLOUD_CONFIG['backend'].upper()} (cold)")
            
        except Exception as e:
            logger.error(f"✗ Connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close connections"""
        if self.hot_client:
            self.hot_client.close()
        logger.info("✓ Disconnected")
    
    async def migrate_to_cloud(
        self,
        collection_name: str,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Migrate collection from MongoDB to Cloud Storage
        
        Process:
        1. Find old documents in hot MongoDB
        2. Upload full document to cloud storage
        3. Replace with metadata stub in MongoDB cold collection
        4. Delete from hot MongoDB
        """
        
        config = get_collection_config(collection_name)
        if not config.get('enabled', False):
            logger.warning(f"Collection '{collection_name}' not enabled")
            return {'migrated': 0, 'failed': 0}
        
        hot_collection = config['hot_collection']
        cold_collection = config['cold_collection']
        date_field = config.get('date_field')
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Migrating to Cloud: {collection_name}")
        logger.info(f"Dry run: {dry_run}")
        logger.info(f"{'='*70}\n")
        
        # Build query for old data
        threshold_date = datetime.utcnow() - timedelta(
            days=TIME_BASED_POLICY['cold_threshold_days']
        )
        query = {date_field: {'$lt': threshold_date}}
        
        # Count documents
        hot_coll = self.hot_db[hot_collection]
        total_count = await hot_coll.count_documents(query)
        
        logger.info(f"Found {total_count} documents to migrate to cloud")
        
        if total_count == 0 or dry_run:
            return {'migrated': 0, 'failed': 0}
        
        # Migrate in batches
        migrated = 0
        failed = 0
        batch_size = MIGRATION_CONFIG['batch_size']
        
        cursor = hot_coll.find(query).batch_size(batch_size)
        
        async for document in cursor:
            try:
                doc_id = str(document['_id'])
                
                # 1. Upload full document to cloud
                storage_key = build_storage_key(collection_name, doc_id)
                upload_success = await self.cloud_adapter.upload(storage_key, document)
                
                if not upload_success:
                    failed += 1
                    continue
                
                # 2. Create metadata stub
                metadata = {
                    '_id': document['_id'],
                    '_storage_location': 'cloud',
                    '_storage_backend': COLD_CLOUD_CONFIG['backend'],
                    '_storage_key': storage_key,
                    '_migrated_at': datetime.utcnow(),
                    '_original_size_bytes': len(str(document)),
                    # Keep searchable fields
                    date_field: document.get(date_field),
                }
                
                # Add any other important fields for search
                for field in ['user_id', 'order_id', 'status', 'type']:
                    if field in document:
                        metadata[field] = document[field]
                
                # 3. Insert metadata into cold collection
                cold_coll = self.metadata_db[cold_collection]
                await cold_coll.insert_one(metadata)
                
                # 4. Delete from hot
                if MIGRATION_CONFIG['delete_after_migration']:
                    await hot_coll.delete_one({'_id': document['_id']})
                
                migrated += 1
                
                if migrated % 100 == 0:
                    logger.info(f"Progress: {migrated}/{total_count}")
                
            except Exception as e:
                logger.error(f"Failed to migrate document: {e}")
                failed += 1
        
        logger.info(f"\n✓ Cloud migration complete:")
        logger.info(f"  - Migrated: {migrated}")
        logger.info(f"  - Failed: {failed}")
        
        return {'migrated': migrated, 'failed': failed}
    
    async def restore_from_cloud(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[Dict]:
        """
        Restore a document from cloud storage to hot MongoDB
        
        Process:
        1. Get metadata from cold collection
        2. Download full document from cloud
        3. Insert into hot MongoDB
        4. Delete metadata from cold collection
        """
        
        config = get_collection_config(collection_name)
        cold_collection = config['cold_collection']
        hot_collection = config['hot_collection']
        
        try:
            # 1. Get metadata
            cold_coll = self.metadata_db[cold_collection]
            metadata = await cold_coll.find_one({'_id': document_id})
            
            if not metadata:
                logger.warning(f"Document not found in cold storage: {document_id}")
                return None
            
            # 2. Download from cloud
            storage_key = metadata['_storage_key']
            document = await self.cloud_adapter.download(storage_key)
            
            if not document:
                logger.error(f"Failed to download from cloud: {storage_key}")
                return None
            
            # 3. Insert into hot
            hot_coll = self.hot_db[hot_collection]
            await hot_coll.insert_one(document)
            
            # 4. Delete metadata from cold
            await cold_coll.delete_one({'_id': document_id})
            
            # 5. Delete from cloud (optional)
            await self.cloud_adapter.delete(storage_key)
            
            logger.info(f"✓ Restored from cloud: {document_id}")
            return document
            
        except Exception as e:
            logger.error(f"✗ Restore failed: {e}")
            return None
    
    async def get_from_cloud(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[Dict]:
        """
        Get document from cloud storage (without restoring to hot)
        """
        
        config = get_collection_config(collection_name)
        cold_collection = config['cold_collection']
        
        try:
            # Get metadata
            cold_coll = self.metadata_db[cold_collection]
            metadata = await cold_coll.find_one({'_id': document_id})
            
            if not metadata:
                return None
            
            # Download from cloud
            storage_key = metadata['_storage_key']
            document = await self.cloud_adapter.download(storage_key)
            
            # Add metadata
            if document:
                document['_retrieved_from'] = 'cloud'
                document['_storage_backend'] = metadata['_storage_backend']
            
            return document
            
        except Exception as e:
            logger.error(f"✗ Cloud retrieval failed: {e}")
            return None


# Convenience function
async def migrate_to_cloud(collection_name: str, dry_run: bool = True):
    """Quick migration to cloud storage"""
    migrator = HybridMigrator()
    try:
        await migrator.connect()
        result = await migrator.migrate_to_cloud(collection_name, dry_run)
        return result
    finally:
        await migrator.disconnect()
