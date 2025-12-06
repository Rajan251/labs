"""
Configuration for Hot-Cold Data Separation with Flexible Storage Options

This module supports multiple storage backends:
- MongoDB (same instance, different collections) - DEFAULT
- MongoDB (different instances/URLs)
- Cloud Storage (S3, MinIO, etc.) for cold data
- Hybrid (MongoDB hot + Cloud cold)
"""

import os
from datetime import timedelta

# ============================================================================
# STORAGE BACKEND CONFIGURATION
# ============================================================================

# Storage backend type for cold data
# Options: 'mongodb', 's3', 'minio', 'filesystem'
COLD_STORAGE_BACKEND = os.environ.get('COLD_STORAGE_BACKEND', 'mongodb')

# ============================================================================
# DATABASE CONNECTIONS
# ============================================================================

# Hot Database (Primary - High Performance)
HOT_DB_CONFIG = {
    'uri': os.environ.get('HOT_MONGO_URI', 'mongodb://mongo:27017'),
    'database': os.environ.get('HOT_DB_NAME', 'hot_cold_db'),
    'description': 'Primary database for frequently accessed data',
    'read_preference': 'primary',  # Always read from primary
}

# Cold Database (Archive - Cost Optimized)
# Can be same instance (different collections) or different instance
COLD_DB_CONFIG = {
    'uri': os.environ.get('COLD_MONGO_URI', 'mongodb://mongo:27017'),
    'database': os.environ.get('COLD_DB_NAME', 'hot_cold_db'),
    'description': 'Archive database for rarely accessed data',
    'read_preference': 'secondaryPreferred',  # Can read from secondary
    # For different instance/cluster:
    # 'uri': 'mongodb://cold-mongo-cluster:27017',
    # 'database': 'cold_archive_db',
}

# Alternative: Cloud Storage for Cold Data (S3/MinIO)
COLD_CLOUD_CONFIG = {
    'enabled': os.environ.get('USE_CLOUD_COLD_STORAGE', 'False') == 'True',
    'backend': os.environ.get('CLOUD_BACKEND', 's3'),  # 's3', 'minio', 'gcs'
    'endpoint': os.environ.get('CLOUD_ENDPOINT', 'https://s3.amazonaws.com'),
    'bucket': os.environ.get('COLD_BUCKET', 'cold-data-archive'),
    'access_key': os.environ.get('CLOUD_ACCESS_KEY', ''),
    'secret_key': os.environ.get('CLOUD_SECRET_KEY', ''),
    'region': os.environ.get('CLOUD_REGION', 'us-east-1'),
}

# ============================================================================
# READ URL CONFIGURATION (for different access patterns)
# ============================================================================

# Hot Data Read URLs (fast, direct access)
HOT_READ_CONFIG = {
    'base_url': os.environ.get('HOT_READ_URL', 'http://localhost:8001'),
    'endpoint_prefix': '/api',
    'cache_enabled': True,
    'cache_ttl': 300,  # 5 minutes
}

# Cold Data Read URLs (can be different service/CDN)
COLD_READ_CONFIG = {
    'base_url': os.environ.get('COLD_READ_URL', 'http://localhost:8001'),
    'endpoint_prefix': '/api/archive',  # Different endpoint for cold data
    'cache_enabled': True,
    'cache_ttl': 3600,  # 1 hour (cold data changes less)
    # For separate cold data service:
    # 'base_url': 'http://cold-data-service:8002',
    # For CDN:
    # 'base_url': 'https://cdn.example.com/cold-data',
}

# ============================================================================
# SEPARATION POLICIES
# ============================================================================

# Time-based separation thresholds
TIME_BASED_POLICY = {
    'hot_threshold_days': int(os.environ.get('HOT_THRESHOLD_DAYS', '90')),
    'cold_threshold_days': int(os.environ.get('COLD_THRESHOLD_DAYS', '90')),
}

# Access-based separation thresholds
ACCESS_BASED_POLICY = {
    'hot_access_days': int(os.environ.get('HOT_ACCESS_DAYS', '30')),
    'cold_access_days': int(os.environ.get('COLD_ACCESS_DAYS', '30')),
    'track_access': os.environ.get('TRACK_ACCESS', 'True') == 'True',
}

# Hybrid policy (combines time and access)
HYBRID_POLICY = {
    'enabled': os.environ.get('HYBRID_POLICY', 'True') == 'True',
    'min_age_days': 60,
    'min_inactive_days': 30,
}

# ============================================================================
# COLLECTION MAPPINGS
# ============================================================================

COLLECTIONS_CONFIG = {
    'users': {
        'enabled': True,
        'hot_collection': 'users',
        'cold_collection': 'users_archive',
        'policy': 'access_based',
        'date_field': 'last_login',
        'access_field': 'last_accessed',
        # Storage backend override (optional)
        'cold_storage': 'mongodb',  # or 's3', 'minio'
    },
    'orders': {
        'enabled': True,
        'hot_collection': 'orders',
        'cold_collection': 'orders_archive',
        'policy': 'time_based',
        'date_field': 'created_at',
        'access_field': 'last_accessed',
        'cold_storage': 'mongodb',
    },
    'logs': {
        'enabled': True,
        'hot_collection': 'logs',
        'cold_collection': 'logs_archive',
        'policy': 'time_based',
        'date_field': 'timestamp',
        'access_field': None,
        'cold_storage': 'mongodb',
    },
    'transactions': {
        'enabled': True,
        'hot_collection': 'transactions',
        'cold_collection': 'transactions_archive',
        'policy': 'hybrid',
        'date_field': 'transaction_date',
        'access_field': 'last_accessed',
        'cold_storage': 'mongodb',
    },
    'media': {
        'enabled': True,
        'hot_collection': 'media',
        'cold_collection': 'media_archive',
        'policy': 'time_based',
        'date_field': 'upload_date',
        'access_field': 'last_accessed',
        # Large files can use cloud storage
        'cold_storage': 's3' if COLD_CLOUD_CONFIG['enabled'] else 'mongodb',
    },
}

# ============================================================================
# MIGRATION SETTINGS
# ============================================================================

MIGRATION_CONFIG = {
    'batch_size': int(os.environ.get('MIGRATION_BATCH_SIZE', '1000')),
    'dry_run': os.environ.get('MIGRATION_DRY_RUN', 'False') == 'True',
    'delete_after_migration': os.environ.get('DELETE_AFTER_MIGRATION', 'True') == 'True',
    'verify_migration': os.environ.get('VERIFY_MIGRATION', 'True') == 'True',
    'parallel_workers': int(os.environ.get('MIGRATION_WORKERS', '4')),
}

# ============================================================================
# SCHEDULER SETTINGS
# ============================================================================

SCHEDULER_CONFIG = {
    'enabled': os.environ.get('SCHEDULER_ENABLED', 'True') == 'True',
    'schedule': os.environ.get('MIGRATION_SCHEDULE', 'daily'),
    'time': os.environ.get('MIGRATION_TIME', '02:00'),
    'notification_email': os.environ.get('NOTIFICATION_EMAIL', ''),
}

# ============================================================================
# QUERY ROUTING SETTINGS
# ============================================================================

ROUTING_CONFIG = {
    'check_hot_first': True,
    'fallback_to_cold': True,
    'cache_routing_decisions': True,
    'cache_ttl_seconds': 3600,
    'promote_to_hot_on_access': os.environ.get('PROMOTE_ON_ACCESS', 'False') == 'True',
    # URL routing
    'use_different_urls': os.environ.get('USE_DIFFERENT_COLD_URL', 'False') == 'True',
    'cold_url_pattern': os.environ.get('COLD_URL_PATTERN', '/archive/{collection}/{id}'),
}

# ============================================================================
# MONITORING & ANALYTICS
# ============================================================================

MONITORING_CONFIG = {
    'enabled': os.environ.get('MONITORING_ENABLED', 'True') == 'True',
    'metrics_collection': 'data_metrics',
    'track_query_performance': True,
    'track_storage_usage': True,
    'alert_threshold_gb': int(os.environ.get('ALERT_THRESHOLD_GB', '100')),
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_hot_threshold():
    """Get the timedelta for hot data threshold"""
    return timedelta(days=TIME_BASED_POLICY['hot_threshold_days'])

def get_cold_threshold():
    """Get the timedelta for cold data threshold"""
    return timedelta(days=TIME_BASED_POLICY['cold_threshold_days'])

def get_collection_config(collection_name):
    """Get configuration for a specific collection"""
    return COLLECTIONS_CONFIG.get(collection_name, {})

def is_collection_enabled(collection_name):
    """Check if hot-cold separation is enabled for a collection"""
    config = get_collection_config(collection_name)
    return config.get('enabled', False)

def get_cold_storage_backend(collection_name):
    """Get the storage backend for cold data of a collection"""
    config = get_collection_config(collection_name)
    return config.get('cold_storage', COLD_STORAGE_BACKEND)

def get_read_url(is_cold=False):
    """Get the appropriate read URL for hot or cold data"""
    if is_cold:
        return COLD_READ_CONFIG['base_url'] + COLD_READ_CONFIG['endpoint_prefix']
    return HOT_READ_CONFIG['base_url'] + HOT_READ_CONFIG['endpoint_prefix']

def build_cold_url(collection, document_id):
    """Build URL for accessing cold data"""
    if ROUTING_CONFIG['use_different_urls']:
        pattern = ROUTING_CONFIG['cold_url_pattern']
        return COLD_READ_CONFIG['base_url'] + pattern.format(
            collection=collection,
            id=document_id
        )
    return get_read_url(is_cold=True) + f'/{collection}/{document_id}'
