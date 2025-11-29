"""
Database configuration and connection management
"""
import os
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database connection manager (Singleton)"""
    
    _instance: Optional['Database'] = None
    _client: Optional[MongoClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._connect()
    
    def _connect(self):
        """Establish MongoDB connection with connection pooling"""
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB_NAME", "myapp")
        max_pool_size = int(os.getenv("MONGODB_MAX_POOL_SIZE", "100"))
        min_pool_size = int(os.getenv("MONGODB_MIN_POOL_SIZE", "10"))
        
        try:
            self._client = MongoClient(
                mongodb_url,
                maxPoolSize=max_pool_size,
                minPoolSize=min_pool_size,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                retryWrites=True,
                retryReads=True,
                w='majority',
                journal=True
            )
            
            # Test connection
            self._client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {mongodb_url}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def get_database(self):
        """Get database instance"""
        if self._client is None:
            self._connect()
        
        db_name = os.getenv("MONGODB_DB_NAME", "myapp")
        return self._client[db_name]
    
    def get_collection(self, collection_name: str):
        """Get collection instance"""
        db = self.get_database()
        return db[collection_name]
    
    def health_check(self) -> bool:
        """Check if MongoDB connection is healthy"""
        try:
            if self._client is None:
                return False
            self._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")
            self._client = None


# Global database instance
db = Database()


def get_db():
    """Dependency for FastAPI routes"""
    return db.get_database()


def get_items_collection():
    """Get items collection"""
    return db.get_collection("items")


def get_task_results_collection():
    """Get task results collection"""
    return db.get_collection("task_results")
