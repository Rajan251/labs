#!/usr/bin/env python3
"""
Example: Data Format Demonstration

This script shows exactly what data looks like in each storage location.
Run this to see real examples of hot/cold data formats.
"""

import json
from datetime import datetime
from bson import ObjectId

print("\n" + "="*80)
print("DATA FORMAT EXAMPLES - MongoDB Hot + S3 Cold")
print("="*80 + "\n")

# ============================================================================
# EXAMPLE 1: User Document
# ============================================================================

print("EXAMPLE 1: User Document")
print("-" * 80)

# Original document in Hot MongoDB
hot_user = {
    "_id": ObjectId("507f1f77bcf86cd799439011"),
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "address": {
        "street": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip": "10001"
    },
    "preferences": {
        "newsletter": True,
        "notifications": ["email", "sms"],
        "theme": "dark"
    },
    "created_at": datetime(2023, 1, 15, 10, 30, 0),
    "last_login": datetime(2024, 11, 15, 14, 20, 0),
    "last_accessed": datetime(2024, 11, 15, 14, 20, 0),
    "status": "active",
    "total_orders": 45,
    "lifetime_value": 12500.50
}

print("\n1. HOT MONGODB (Full Document):")
print("-" * 40)
print(f"Collection: users")
print(f"Format: BSON")
print(f"Size: ~500 bytes")
print(f"\nDocument:")
# Convert ObjectId to string for display
display_hot = {k: (str(v) if isinstance(v, ObjectId) else v) for k, v in hot_user.items()}
print(json.dumps(display_hot, indent=2, default=str))

# After migration to S3
s3_user = {
    "_id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "address": {
        "street": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip": "10001"
    },
    "preferences": {
        "newsletter": True,
        "notifications": ["email", "sms"],
        "theme": "dark"
    },
    "created_at": "2023-01-15T10:30:00.000Z",
    "last_login": "2024-11-15T14:20:00.000Z",
    "last_accessed": "2024-11-15T14:20:00.000Z",
    "status": "active",
    "total_orders": 45,
    "lifetime_value": 12500.50,
    "_migrated_at": "2024-12-03T10:00:00.000Z",
    "_migrated_from": "hot_mongodb"
}

print("\n2. S3 STORAGE (Full Document as JSON):")
print("-" * 40)
print(f"Bucket: cold-data-archive")
print(f"Key: users/2024/12/507f1f77bcf86cd799439011.json")
print(f"Format: JSON (gzip compressed)")
print(f"Size: ~250 bytes (compressed)")
print(f"\nContent:")
print(json.dumps(s3_user, indent=2))

# Metadata in MongoDB
cold_metadata = {
    "_id": "507f1f77bcf86cd799439011",
    "_storage_location": "cloud",
    "_storage_backend": "s3",
    "_storage_bucket": "cold-data-archive",
    "_storage_key": "users/2024/12/507f1f77bcf86cd799439011.json",
    "_storage_region": "us-east-1",
    "_migrated_at": "2024-12-03T10:00:00Z",
    "_original_size_bytes": 500,
    "_compressed_size_bytes": 250,
    # Searchable fields
    "email": "john@example.com",
    "name": "John Doe",
    "status": "active",
    "created_at": "2023-01-15T10:30:00Z",
    "last_login": "2024-11-15T14:20:00Z",
    "total_orders": 45,
    "lifetime_value": 12500.50
}

print("\n3. MONGODB METADATA (Searchable Stub):")
print("-" * 40)
print(f"Collection: users_archive")
print(f"Format: BSON")
print(f"Size: ~200 bytes")
print(f"\nDocument:")
print(json.dumps(cold_metadata, indent=2))

# ============================================================================
# EXAMPLE 2: Order Document
# ============================================================================

print("\n\n" + "="*80)
print("EXAMPLE 2: Order Document")
print("-" * 80)

hot_order = {
    "_id": "ORD-2024-001234",
    "customer_id": "507f1f77bcf86cd799439011",
    "items": [
        {
            "product_id": "PROD-001",
            "name": "Laptop",
            "quantity": 1,
            "price": 1299.99
        }
    ],
    "total_amount": 1299.99,
    "status": "delivered",
    "created_at": "2024-01-18T14:30:00Z"
}

print("\n1. HOT MONGODB:")
print(json.dumps(hot_order, indent=2))

cold_order_metadata = {
    "_id": "ORD-2024-001234",
    "_storage_location": "cloud",
    "_storage_key": "orders/2024/01/ORD-2024-001234.json",
    # Searchable fields only
    "customer_id": "507f1f77bcf86cd799439011",
    "total_amount": 1299.99,
    "status": "delivered",
    "created_at": "2024-01-18T14:30:00Z",
    "item_count": 1
}

print("\n2. MONGODB METADATA (after migration):")
print(json.dumps(cold_order_metadata, indent=2))

print("\n3. S3 STORAGE:")
print(f"Key: orders/2024/01/ORD-2024-001234.json")
print(f"Content: Full order document (same as hot)")

# ============================================================================
# STORAGE COMPARISON
# ============================================================================

print("\n\n" + "="*80)
print("STORAGE COMPARISON")
print("="*80)

comparison = [
    ["Location", "Format", "Size", "Purpose"],
    ["-" * 15, "-" * 10, "-" * 10, "-" * 30],
    ["Hot MongoDB", "BSON", "500 bytes", "Recent data, fast queries"],
    ["S3 Storage", "JSON+gzip", "250 bytes", "Full archived data"],
    ["Cold Metadata", "BSON", "200 bytes", "Search index, S3 pointer"],
]

for row in comparison:
    print(f"{row[0]:<15} {row[1]:<10} {row[2]:<10} {row[3]:<30}")

print("\n" + "="*80)
print("KEY POINTS:")
print("="*80)
print("✓ Hot data: Full document in MongoDB (BSON)")
print("✓ Cold data: Full document in S3 (JSON)")
print("✓ Metadata: Searchable fields + S3 key in MongoDB")
print("✓ Compression: 50% storage savings")
print("✓ Format: JSON for universal compatibility")
print("="*80 + "\n")
