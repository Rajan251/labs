#!/usr/bin/env python3
"""
Manual Data Migration Script

This script allows you to manually migrate data from hot to cold storage.

Usage:
    python migrate_cold_data.py --collection users --dry-run
    python migrate_cold_data.py --collection orders
    python migrate_cold_data.py --all
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_separation.migrator import DataMigrator
from data_separation.config import COLLECTIONS_CONFIG


async def main():
    parser = argparse.ArgumentParser(
        description='Migrate data from hot to cold storage'
    )
    parser.add_argument(
        '--collection',
        type=str,
        help='Collection name to migrate (e.g., users, orders, logs)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Migrate all enabled collections'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without actually moving data'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if not args.collection and not args.all:
        parser.error('Either --collection or --all must be specified')
    
    # Initialize migrator
    migrator = DataMigrator()
    
    try:
        print("\n" + "="*70)
        print("HOT-COLD DATA MIGRATION SCRIPT")
        print("="*70 + "\n")
        
        await migrator.connect()
        
        if args.all:
            print("Migrating all enabled collections...\n")
            results = await migrator.migrate_all(dry_run=args.dry_run)
            
            # Print summary
            print("\n" + "="*70)
            print("MIGRATION SUMMARY")
            print("="*70)
            
            total_migrated = 0
            total_failed = 0
            total_skipped = 0
            
            for collection, stats in results.items():
                print(f"\n{collection}:")
                print(f"  Migrated: {stats['migrated']}")
                print(f"  Failed: {stats['failed']}")
                print(f"  Skipped: {stats['skipped']}")
                
                total_migrated += stats['migrated']
                total_failed += stats['failed']
                total_skipped += stats['skipped']
            
            print(f"\nTOTAL:")
            print(f"  Migrated: {total_migrated}")
            print(f"  Failed: {total_failed}")
            print(f"  Skipped: {total_skipped}")
            
        else:
            print(f"Migrating collection: {args.collection}\n")
            result = await migrator.migrate_collection(
                args.collection,
                dry_run=args.dry_run
            )
            
            print("\n" + "="*70)
            print("MIGRATION SUMMARY")
            print("="*70)
            print(f"  Migrated: {result['migrated']}")
            print(f"  Failed: {result['failed']}")
            print(f"  Skipped: {result['skipped']}")
        
        print("\n" + "="*70)
        print("✓ Migration completed successfully")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}\n")
        sys.exit(1)
    
    finally:
        await migrator.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
