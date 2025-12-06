"""
Query Router - Intelligent routing between hot and cold databases

This module provides transparent query routing to automatically check
hot storage first and fallback to cold storage if needed.
"""

from typing import Dict, List, Optional, Any, Union
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from datetime import datetime
import logging

from .config import (
    HOT_DB_CONFIG,
    COLD_DB_CONFIG,
    ROUTING_CONFIG,
    get_collection_config,
    is_collection_enabled,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryRouter:
    """
    Routes queries between hot and cold databases intelligently
    
    Features:
        - Automatic fallback from hot to cold
        - Query performance tracking
        - Optional promotion of cold data back to hot on access
        - Caching of routing decisions
    """
    
    def __init__(self):
        """Initialize router with database connections"""
        self.hot_client: Optional[AsyncIOMotorClient] = None
        self.cold_client: Optional[AsyncIOMotorClient] = None
        self.hot_db: Optional[AsyncIOMotorDatabase] = None
        self.cold_db: Optional[AsyncIOMotorDatabase] = None
        self.routing_cache: Dict[str, str] = {}  # Cache which DB has the data
        self.stats = {
            'hot_hits': 0,
            'cold_hits': 0,
            'cache_hits': 0,
            'misses': 0,
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
            
            logger.info("✓ Query router connected to databases")
        except Exception as e:
            logger.error(f"✗ Failed to connect: {e}")
            raise
    
    async def disconnect(self):
        """Close database connections"""
        if self.hot_client:
            self.hot_client.close()
        if self.cold_client:
            self.cold_client.close()
        logger.info("✓ Query router disconnected")
    
    async def find_one(
        self,
        collection_name: str,
        query: Dict,
        update_access: bool = True
    ) -> Optional[Dict]:
        """
        Find a single document, checking hot DB first, then cold
        
        Args:
            collection_name: Name of the collection
            query: MongoDB query
            update_access: Whether to update last_accessed field
            
        Returns:
            Document if found, None otherwise
        """
        if not is_collection_enabled(collection_name):
            # If not enabled, only check hot DB
            config = get_collection_config(collection_name)
            hot_collection = config.get('hot_collection', collection_name)
            return await self.hot_db[hot_collection].find_one(query)
        
        config = get_collection_config(collection_name)
        hot_collection = config['hot_collection']
        cold_collection = config['cold_collection']
        access_field = config.get('access_field')
        
        # Check hot database first
        if ROUTING_CONFIG['check_hot_first']:
            document = await self.hot_db[hot_collection].find_one(query)
            
            if document:
                self.stats['hot_hits'] += 1
                
                # Update access timestamp if configured
                if update_access and access_field:
                    await self._update_access_time(
                        self.hot_db[hot_collection],
                        document['_id'],
                        access_field
                    )
                
                return document
        
        # Fallback to cold database
        if ROUTING_CONFIG['fallback_to_cold']:
            document = await self.cold_db[cold_collection].find_one(query)
            
            if document:
                self.stats['cold_hits'] += 1
                
                # Optionally promote to hot storage
                if ROUTING_CONFIG['promote_to_hot_on_access']:
                    await self._promote_to_hot(
                        document,
                        hot_collection,
                        cold_collection
                    )
                
                # Update access timestamp
                if update_access and access_field:
                    await self._update_access_time(
                        self.cold_db[cold_collection],
                        document['_id'],
                        access_field
                    )
                
                return document
        
        self.stats['misses'] += 1
        return None
    
    async def find(
        self,
        collection_name: str,
        query: Dict,
        limit: int = 0,
        skip: int = 0,
        sort: Optional[List] = None
    ) -> List[Dict]:
        """
        Find multiple documents across hot and cold databases
        
        Args:
            collection_name: Name of the collection
            query: MongoDB query
            limit: Maximum number of documents to return
            skip: Number of documents to skip
            sort: Sort specification
            
        Returns:
            List of documents
        """
        if not is_collection_enabled(collection_name):
            config = get_collection_config(collection_name)
            hot_collection = config.get('hot_collection', collection_name)
            cursor = self.hot_db[hot_collection].find(query)
            
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            return await cursor.to_list(length=limit if limit else None)
        
        config = get_collection_config(collection_name)
        hot_collection = config['hot_collection']
        cold_collection = config['cold_collection']
        
        results = []
        
        # Query hot database
        hot_cursor = self.hot_db[hot_collection].find(query)
        if sort:
            hot_cursor = hot_cursor.sort(sort)
        
        hot_results = await hot_cursor.to_list(length=None)
        results.extend(hot_results)
        
        # Query cold database if needed
        if ROUTING_CONFIG['fallback_to_cold']:
            cold_cursor = self.cold_db[cold_collection].find(query)
            if sort:
                cold_cursor = cold_cursor.sort(sort)
            
            cold_results = await cold_cursor.to_list(length=None)
            results.extend(cold_results)
        
        # Apply sorting, skip, and limit to combined results
        if sort:
            # Sort combined results
            sort_fields = [(field, direction) for field, direction in sort]
            for field, direction in reversed(sort_fields):
                results.sort(
                    key=lambda x: x.get(field, ''),
                    reverse=(direction == -1)
                )
        
        if skip:
            results = results[skip:]
        
        if limit:
            results = results[:limit]
        
        return results
    
    async def count_documents(
        self,
        collection_name: str,
        query: Dict
    ) -> int:
        """
        Count documents across hot and cold databases
        
        Args:
            collection_name: Name of the collection
            query: MongoDB query
            
        Returns:
            Total count
        """
        if not is_collection_enabled(collection_name):
            config = get_collection_config(collection_name)
            hot_collection = config.get('hot_collection', collection_name)
            return await self.hot_db[hot_collection].count_documents(query)
        
        config = get_collection_config(collection_name)
        hot_collection = config['hot_collection']
        cold_collection = config['cold_collection']
        
        hot_count = await self.hot_db[hot_collection].count_documents(query)
        cold_count = 0
        
        if ROUTING_CONFIG['fallback_to_cold']:
            cold_count = await self.cold_db[cold_collection].count_documents(query)
        
        return hot_count + cold_count
    
    async def insert_one(
        self,
        collection_name: str,
        document: Dict
    ) -> Any:
        """
        Insert a document into hot storage
        
        Args:
            collection_name: Name of the collection
            document: Document to insert
            
        Returns:
            Insert result
        """
        config = get_collection_config(collection_name)
        hot_collection = config.get('hot_collection', collection_name)
        
        # Always insert new documents into hot storage
        result = await self.hot_db[hot_collection].insert_one(document)
        return result
    
    async def update_one(
        self,
        collection_name: str,
        query: Dict,
        update: Dict
    ) -> Any:
        """
        Update a document (checks both hot and cold)
        
        Args:
            collection_name: Name of the collection
            query: Query to find document
            update: Update operations
            
        Returns:
            Update result
        """
        if not is_collection_enabled(collection_name):
            config = get_collection_config(collection_name)
            hot_collection = config.get('hot_collection', collection_name)
            return await self.hot_db[hot_collection].update_one(query, update)
        
        config = get_collection_config(collection_name)
        hot_collection = config['hot_collection']
        cold_collection = config['cold_collection']
        
        # Try hot first
        result = await self.hot_db[hot_collection].update_one(query, update)
        
        if result.matched_count == 0 and ROUTING_CONFIG['fallback_to_cold']:
            # Try cold
            result = await self.cold_db[cold_collection].update_one(query, update)
        
        return result
    
    async def delete_one(
        self,
        collection_name: str,
        query: Dict
    ) -> Any:
        """
        Delete a document (checks both hot and cold)
        
        Args:
            collection_name: Name of the collection
            query: Query to find document
            
        Returns:
            Delete result
        """
        if not is_collection_enabled(collection_name):
            config = get_collection_config(collection_name)
            hot_collection = config.get('hot_collection', collection_name)
            return await self.hot_db[hot_collection].delete_one(query)
        
        config = get_collection_config(collection_name)
        hot_collection = config['hot_collection']
        cold_collection = config['cold_collection']
        
        # Try hot first
        result = await self.hot_db[hot_collection].delete_one(query)
        
        if result.deleted_count == 0 and ROUTING_CONFIG['fallback_to_cold']:
            # Try cold
            result = await self.cold_db[cold_collection].delete_one(query)
        
        return result
    
    async def _update_access_time(
        self,
        collection,
        doc_id: Any,
        access_field: str
    ):
        """Update the last accessed timestamp for a document"""
        try:
            await collection.update_one(
                {'_id': doc_id},
                {'$set': {access_field: datetime.utcnow()}}
            )
        except Exception as e:
            logger.warning(f"Failed to update access time: {e}")
    
    async def _promote_to_hot(
        self,
        document: Dict,
        hot_collection: str,
        cold_collection: str
    ):
        """
        Promote a document from cold to hot storage
        
        Args:
            document: Document to promote
            hot_collection: Hot collection name
            cold_collection: Cold collection name
        """
        try:
            # Remove migration metadata
            document.pop('_migrated_at', None)
            document.pop('_migrated_from', None)
            
            # Insert into hot
            await self.hot_db[hot_collection].insert_one(document)
            
            # Delete from cold
            await self.cold_db[cold_collection].delete_one({'_id': document['_id']})
            
            logger.info(f"✓ Promoted document {document['_id']} to hot storage")
        except Exception as e:
            logger.error(f"✗ Failed to promote document: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get routing statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset routing statistics"""
        self.stats = {
            'hot_hits': 0,
            'cold_hits': 0,
            'cache_hits': 0,
            'misses': 0,
        }


# Global router instance
_router_instance: Optional[QueryRouter] = None


async def get_router() -> QueryRouter:
    """Get or create global router instance"""
    global _router_instance
    
    if _router_instance is None:
        _router_instance = QueryRouter()
        await _router_instance.connect()
    
    return _router_instance
