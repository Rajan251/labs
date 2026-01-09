#!/usr/bin/env python3
"""
MongoDB Connection Example using Environment Variables
Demonstrates how to use .env file with Python application
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.write_concern import WriteConcern
from pymongo.read_preference import ReadPreference
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class MongoDBConfig:
    """MongoDB configuration from environment variables"""
    
    def __init__(self):
        # Option 1: Use full connection string (RECOMMENDED)
        self.uri = os.getenv('MONGODB_URI')
        
        # Option 2: Build connection string from components
        if not self.uri:
            self.uri = self._build_connection_string()
        
        # Connection pool settings
        self.max_pool_size = int(os.getenv('MONGODB_MAX_POOL_SIZE', '100'))
        self.min_pool_size = int(os.getenv('MONGODB_MIN_POOL_SIZE', '10'))
        self.max_idle_time_ms = int(os.getenv('MONGODB_MAX_IDLE_TIME_MS', '30000'))
        
        # Write concern settings
        self.write_concern = os.getenv('MONGODB_WRITE_CONCERN', 'majority')
        self.write_timeout_ms = int(os.getenv('MONGODB_WRITE_TIMEOUT_MS', '5000'))
        self.journal = os.getenv('MONGODB_JOURNAL', 'true').lower() == 'true'
        
        # Read preference settings
        self.read_preference = os.getenv('MONGODB_READ_PREFERENCE', 'primary')
        self.max_staleness_seconds = int(os.getenv('MONGODB_MAX_STALENESS_SECONDS', '90'))
        
        # Timeout settings
        self.server_selection_timeout_ms = int(os.getenv('MONGODB_SERVER_SELECTION_TIMEOUT_MS', '5000'))
        self.connect_timeout_ms = int(os.getenv('MONGODB_CONNECT_TIMEOUT_MS', '10000'))
        self.socket_timeout_ms = int(os.getenv('MONGODB_SOCKET_TIMEOUT_MS', '10000'))
        
        # Retry settings
        self.retry_writes = os.getenv('MONGODB_RETRY_WRITES', 'true').lower() == 'true'
        self.retry_reads = os.getenv('MONGODB_RETRY_READS', 'true').lower() == 'true'
        
        # TLS settings
        self.tls_enabled = os.getenv('MONGODB_TLS_ENABLED', 'false').lower() == 'true'
        self.tls_ca_file = os.getenv('MONGODB_TLS_CA_FILE')
        self.tls_cert_file = os.getenv('MONGODB_TLS_CERT_FILE')
        
        # Application settings
        self.app_name = os.getenv('APP_NAME', 'MyApplication')
        self.app_env = os.getenv('APP_ENV', 'development')
    
    def _build_connection_string(self):
        """Build connection string from individual components"""
        username = os.getenv('MONGODB_USERNAME')
        password = os.getenv('MONGODB_PASSWORD')
        hosts = os.getenv('MONGODB_HOSTS', 'localhost:27017')
        database = os.getenv('MONGODB_DATABASE', 'test')
        replica_set = os.getenv('MONGODB_REPLICA_SET')
        auth_source = os.getenv('MONGODB_AUTH_SOURCE', 'admin')
        
        # Build base URI
        if username and password:
            uri = f"mongodb://{username}:{password}@{hosts}/{database}"
        else:
            uri = f"mongodb://{hosts}/{database}"
        
        # Add query parameters
        params = []
        if replica_set:
            params.append(f"replicaSet={replica_set}")
        if auth_source:
            params.append(f"authSource={auth_source}")
        params.append(f"w={self.write_concern}")
        params.append(f"wtimeout={self.write_timeout_ms}")
        params.append(f"readPreference={self.read_preference}")
        params.append(f"maxPoolSize={self.max_pool_size}")
        params.append(f"minPoolSize={self.min_pool_size}")
        if self.retry_writes:
            params.append("retryWrites=true")
        
        if params:
            uri += "?" + "&".join(params)
        
        return uri
    
    def get_read_preference(self):
        """Get PyMongo ReadPreference object"""
        preference_map = {
            'primary': ReadPreference.PRIMARY,
            'primaryPreferred': ReadPreference.PRIMARY_PREFERRED,
            'secondary': ReadPreference.SECONDARY,
            'secondaryPreferred': ReadPreference.SECONDARY_PREFERRED,
            'nearest': ReadPreference.NEAREST
        }
        return preference_map.get(self.read_preference, ReadPreference.PRIMARY)


class MongoDBConnection:
    """MongoDB connection manager using environment variables"""
    
    def __init__(self):
        self.config = MongoDBConfig()
        self.client = None
        self.db = None
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            logger.info(f"Connecting to MongoDB ({self.config.app_env})...")
            logger.info(f"App Name: {self.config.app_name}")
            
            # Create MongoDB client
            self.client = MongoClient(
                self.config.uri,
                serverSelectionTimeoutMS=self.config.server_selection_timeout_ms,
                connectTimeoutMS=self.config.connect_timeout_ms,
                socketTimeoutMS=self.config.socket_timeout_ms,
                maxPoolSize=self.config.max_pool_size,
                minPoolSize=self.config.min_pool_size,
                maxIdleTimeMS=self.config.max_idle_time_ms,
                retryWrites=self.config.retry_writes,
                retryReads=self.config.retry_reads,
                appName=self.config.app_name
            )
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("✅ Connected to MongoDB successfully")
            
            # Get database
            database_name = os.getenv('MONGODB_DATABASE', 'test')
            self.db = self.client[database_name]
            
            # Log connection info
            self._log_connection_info()
            
            return self.db
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    def _log_connection_info(self):
        """Log connection information"""
        try:
            # Get server info
            server_info = self.client.server_info()
            logger.info(f"MongoDB Version: {server_info.get('version')}")
            
            # Check if replica set
            is_master = self.client.admin.command('isMaster')
            if 'setName' in is_master:
                logger.info(f"Replica Set: {is_master['setName']}")
                logger.info(f"Primary: {is_master.get('primary', 'Unknown')}")
            else:
                logger.info("Running in standalone mode")
            
            # Log configuration
            logger.info(f"Write Concern: {self.config.write_concern}")
            logger.info(f"Read Preference: {self.config.read_preference}")
            logger.info(f"Connection Pool: {self.config.min_pool_size}-{self.config.max_pool_size}")
            
        except Exception as e:
            logger.warning(f"Could not retrieve connection info: {e}")
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB connection closed")
    
    def insert_document(self, collection_name, document):
        """Insert document with configured write concern"""
        try:
            collection = self.db[collection_name]
            
            # Create write concern
            write_concern = WriteConcern(
                w=self.config.write_concern,
                wtimeout=self.config.write_timeout_ms,
                j=self.config.journal
            )
            
            # Insert with write concern
            result = collection.with_options(write_concern=write_concern).insert_one(document)
            
            logger.info(f"✅ Inserted document: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            logger.error(f"❌ Insert failed: {e}")
            raise
    
    def find_documents(self, collection_name, query=None):
        """Find documents with configured read preference"""
        try:
            collection = self.db[collection_name]
            
            # Apply read preference
            collection = collection.with_options(
                read_preference=self.config.get_read_preference()
            )
            
            documents = list(collection.find(query or {}))
            logger.info(f"✅ Found {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Find failed: {e}")
            raise


def main():
    """Example usage"""
    from datetime import datetime
    
    # Create connection
    mongo = MongoDBConnection()
    db = mongo.connect()
    
    print("\n" + "="*60)
    print("MongoDB Connection Test")
    print("="*60 + "\n")
    
    # Insert test document
    print("📝 Inserting test document...")
    doc_id = mongo.insert_document("test_collection", {
        "message": "Hello from .env configuration!",
        "timestamp": datetime.utcnow(),
        "environment": os.getenv('APP_ENV', 'unknown')
    })
    print(f"   Document ID: {doc_id}\n")
    
    # Find documents
    print("📖 Reading documents...")
    documents = mongo.find_documents("test_collection")
    for doc in documents:
        print(f"   - {doc.get('message')} ({doc.get('environment')})")
    
    # Close connection
    mongo.close()
    
    print("\n" + "="*60)
    print("✅ Test completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
