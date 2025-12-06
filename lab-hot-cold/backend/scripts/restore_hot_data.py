#!/usr/bin/env python3
"""
Restore Data from Cold to Hot Storage

This script allows you to restore data from cold storage back to hot storage.

Usage:
    python restore_hot_data.py --collection users --query '{"_id": "123"}'
    python restore_hot_data.py --collection orders --query '{"status": "active"}' --dry-run
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_separation.migrator import DataMigrator


async def main():
    parser = argparse.ArgumentParser(
        description='Restore data from cold to hot storage'
    )
    parser.add_argument(
        '--collection',
        type=str,
        required=True,
        help='Collection name (e.g., users, orders, logs)'
    )
    parser.add_argument(
        '--query',
        type=str,
        required=True,
        help='MongoDB query as JSON string (e.g., \'{"_id": "123"}\')'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate restoration without actually moving data'
    )
    
    args = parser.parse_args()
    
    # Parse query
    try:
        query = json.loads(args.query)
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON query: {e}")
        sys.exit(1)
    
    # Initialize migrator
    migrator = DataMigrator()
    
    try:
        print("\n" + "="*70)
        print("HOT DATA RESTORATION SCRIPT")
        print("="*70 + "\n")
        
        print(f"Collection: {args.collection}")
        print(f"Query: {query}")
        print(f"Dry run: {args.dry_run}\n")
        
        await migrator.connect()
        
        result = await migrator.restore_to_hot(
            args.collection,
            query,
            dry_run=args.dry_run
        )
        
        print("\n" + "="*70)
        print("RESTORATION SUMMARY")
        print("="*70)
        print(f"  Restored: {result['restored']}")
        print(f"  Failed: {result['failed']}")
        
        print("\n" + "="*70)
        print("✓ Restoration completed successfully")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Restoration failed: {e}\n")
        sys.exit(1)
    
    finally:
        await migrator.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
