#!/usr/bin/env python3
"""
Migrate Data to Cloud Storage (S3/MinIO/GCS)

This script migrates old data from MongoDB to cloud storage.

Usage:
    python migrate_to_cloud.py --collection users --dry-run
    python migrate_to_cloud.py --collection orders
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_separation.hybrid_migrator import HybridMigrator


async def main():
    parser = argparse.ArgumentParser(
        description='Migrate data from MongoDB to Cloud Storage'
    )
    parser.add_argument(
        '--collection',
        type=str,
        required=True,
        help='Collection name to migrate (e.g., users, orders)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without actually moving data'
    )
    
    args = parser.parse_args()
    
    # Initialize migrator
    migrator = HybridMigrator()
    
    try:
        print("\n" + "="*70)
        print("CLOUD STORAGE MIGRATION")
        print("="*70 + "\n")
        
        await migrator.connect()
        
        result = await migrator.migrate_to_cloud(
            args.collection,
            dry_run=args.dry_run
        )
        
        print("\n" + "="*70)
        print("MIGRATION SUMMARY")
        print("="*70)
        print(f"  Migrated: {result['migrated']}")
        print(f"  Failed: {result['failed']}")
        
        print("\n" + "="*70)
        print("✓ Migration completed")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}\n")
        sys.exit(1)
    
    finally:
        await migrator.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
