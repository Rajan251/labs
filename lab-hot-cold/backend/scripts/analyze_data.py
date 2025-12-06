#!/usr/bin/env python3
"""
Analyze Data Distribution

This script analyzes the distribution of data across hot and cold storage.

Usage:
    python analyze_data.py
    python analyze_data.py --collection users
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from data_separation.config import (
    HOT_DB_CONFIG,
    COLD_DB_CONFIG,
    COLLECTIONS_CONFIG,
    TIME_BASED_POLICY,
)


async def analyze_collection(hot_db, cold_db, collection_name, config):
    """Analyze a single collection"""
    hot_collection = config['hot_collection']
    cold_collection = config['cold_collection']
    date_field = config.get('date_field')
    
    # Count documents
    hot_count = await hot_db[hot_collection].count_documents({})
    cold_count = await cold_db[cold_collection].count_documents({})
    total_count = hot_count + cold_count
    
    print(f"\n{'='*70}")
    print(f"Collection: {collection_name}")
    print(f"{'='*70}")
    print(f"Hot storage:  {hot_count:,} documents ({hot_count/total_count*100:.1f}%)" if total_count > 0 else "Hot storage:  0 documents")
    print(f"Cold storage: {cold_count:,} documents ({cold_count/total_count*100:.1f}%)" if total_count > 0 else "Cold storage: 0 documents")
    print(f"Total:        {total_count:,} documents")
    
    # Analyze age distribution if date field exists
    if date_field and hot_count > 0:
        threshold_date = datetime.utcnow() - timedelta(
            days=TIME_BASED_POLICY['cold_threshold_days']
        )
        
        old_in_hot = await hot_db[hot_collection].count_documents({
            date_field: {'$lt': threshold_date}
        })
        
        if old_in_hot > 0:
            print(f"\n⚠ Warning: {old_in_hot:,} old documents still in hot storage")
            print(f"  (older than {TIME_BASED_POLICY['cold_threshold_days']} days)")
    
    # Get storage size estimates
    try:
        hot_stats = await hot_db.command('collStats', hot_collection)
        cold_stats = await cold_db.command('collStats', cold_collection)
        
        hot_size_mb = hot_stats.get('size', 0) / (1024 * 1024)
        cold_size_mb = cold_stats.get('size', 0) / (1024 * 1024)
        
        print(f"\nStorage size:")
        print(f"  Hot:  {hot_size_mb:.2f} MB")
        print(f"  Cold: {cold_size_mb:.2f} MB")
        print(f"  Total: {hot_size_mb + cold_size_mb:.2f} MB")
    except:
        pass
    
    return {
        'collection': collection_name,
        'hot_count': hot_count,
        'cold_count': cold_count,
        'total_count': total_count,
    }


async def main():
    parser = argparse.ArgumentParser(
        description='Analyze data distribution across hot and cold storage'
    )
    parser.add_argument(
        '--collection',
        type=str,
        help='Analyze specific collection (default: all)'
    )
    
    args = parser.parse_args()
    
    # Connect to databases
    hot_client = AsyncIOMotorClient(HOT_DB_CONFIG['uri'])
    cold_client = AsyncIOMotorClient(COLD_DB_CONFIG['uri'])
    
    hot_db = hot_client[HOT_DB_CONFIG['database']]
    cold_db = cold_client[COLD_DB_CONFIG['database']]
    
    try:
        print("\n" + "="*70)
        print("HOT-COLD DATA DISTRIBUTION ANALYSIS")
        print("="*70)
        
        results = []
        
        if args.collection:
            # Analyze single collection
            if args.collection in COLLECTIONS_CONFIG:
                config = COLLECTIONS_CONFIG[args.collection]
                if config.get('enabled', False):
                    result = await analyze_collection(
                        hot_db, cold_db, args.collection, config
                    )
                    results.append(result)
                else:
                    print(f"\n⚠ Collection '{args.collection}' not enabled for hot-cold separation")
            else:
                print(f"\n✗ Collection '{args.collection}' not found in configuration")
        else:
            # Analyze all collections
            for collection_name, config in COLLECTIONS_CONFIG.items():
                if config.get('enabled', False):
                    result = await analyze_collection(
                        hot_db, cold_db, collection_name, config
                    )
                    results.append(result)
        
        # Print overall summary
        if len(results) > 1:
            print(f"\n{'='*70}")
            print("OVERALL SUMMARY")
            print(f"{'='*70}")
            
            total_hot = sum(r['hot_count'] for r in results)
            total_cold = sum(r['cold_count'] for r in results)
            total_all = sum(r['total_count'] for r in results)
            
            print(f"Total hot documents:  {total_hot:,}")
            print(f"Total cold documents: {total_cold:,}")
            print(f"Grand total:          {total_all:,}")
            
            if total_all > 0:
                print(f"\nDistribution:")
                print(f"  Hot:  {total_hot/total_all*100:.1f}%")
                print(f"  Cold: {total_cold/total_all*100:.1f}%")
        
        print("\n" + "="*70)
        print("✓ Analysis completed")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Analysis failed: {e}\n")
        sys.exit(1)
    
    finally:
        hot_client.close()
        cold_client.close()


if __name__ == '__main__':
    asyncio.run(main())
