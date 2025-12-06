#!/usr/bin/env python3
"""
MongoDB Index Setup for Community Edition

This script creates optimized indexes for hot and cold collections
to improve query performance in MongoDB Community Edition.

Run this after starting MongoDB for the first time.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from data_separation.config import HOT_DB_CONFIG, COLLECTIONS_CONFIG


async def create_indexes():
    """Create indexes for all collections"""
    
    client = AsyncIOMotorClient(HOT_DB_CONFIG['uri'])
    db = client[HOT_DB_CONFIG['database']]
    
    print("\n" + "="*70)
    print("MONGODB INDEX SETUP - Community Edition Optimization")
    print("="*70 + "\n")
    
    for collection_name, config in COLLECTIONS_CONFIG.items():
        if not config.get('enabled', False):
            continue
        
        hot_collection = config['hot_collection']
        cold_collection = config['cold_collection']
        date_field = config.get('date_field')
        access_field = config.get('access_field')
        
        print(f"Setting up indexes for: {collection_name}")
        
        # Hot collection indexes
        hot_coll = db[hot_collection]
        
        # Index on date field for time-based queries
        if date_field:
            await hot_coll.create_index(
                [(date_field, -1)],
                name=f"idx_{date_field}_desc",
                background=True
            )
            print(f"  ✓ Created index on {hot_collection}.{date_field}")
        
        # Index on access field for access-based queries
        if access_field:
            await hot_coll.create_index(
                [(access_field, -1)],
                name=f"idx_{access_field}_desc",
                background=True
            )
            print(f"  ✓ Created index on {hot_collection}.{access_field}")
        
        # Compound index for hybrid queries
        if date_field and access_field:
            await hot_coll.create_index(
                [(date_field, -1), (access_field, -1)],
                name=f"idx_{date_field}_{access_field}_desc",
                background=True
            )
            print(f"  ✓ Created compound index on {hot_collection}")
        
        # Cold collection indexes (same as hot)
        cold_coll = db[cold_collection]
        
        if date_field:
            await cold_coll.create_index(
                [(date_field, -1)],
                name=f"idx_{date_field}_desc",
                background=True
            )
            print(f"  ✓ Created index on {cold_collection}.{date_field}")
        
        if access_field:
            await cold_coll.create_index(
                [(access_field, -1)],
                name=f"idx_{access_field}_desc",
                background=True
            )
            print(f"  ✓ Created index on {cold_collection}.{access_field}")
        
        # Migration metadata index for cold collections
        await cold_coll.create_index(
            [("_migrated_at", -1)],
            name="idx_migrated_at_desc",
            background=True
        )
        print(f"  ✓ Created migration index on {cold_collection}")
        
        print()
    
    # Create index on metrics collection
    metrics_coll = db['data_metrics']
    await metrics_coll.create_index(
        [("event_type", 1), ("timestamp", -1)],
        name="idx_event_type_timestamp",
        background=True
    )
    print("✓ Created index on data_metrics collection")
    
    print("\n" + "="*70)
    print("✓ All indexes created successfully")
    print("="*70 + "\n")
    
    client.close()


if __name__ == '__main__':
    asyncio.run(create_indexes())
