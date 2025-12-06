# Data Format Guide - Hybrid Storage (MongoDB Hot + S3 Cold)

## 🎯 Overview

This guide explains **exactly** what data format is used in each storage location and how data flows between them.

---

## 📊 Data Format Comparison

### Hot Data (MongoDB)
**Format:** BSON (Binary JSON) - MongoDB's native format
**Structure:** Full document with all fields

### Cold Data (S3)
**Format:** JSON (Text)
**Structure:** Full document as compressed JSON file

### Cold Metadata (MongoDB)
**Format:** BSON
**Structure:** Minimal document with searchable fields + S3 reference

---

## 🔍 Detailed Examples

### Example 1: User Document

#### **Original in Hot MongoDB**
```json
{
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
    "newsletter": true,
    "notifications": ["email", "sms"],
    "theme": "dark"
  },
  "profile_image": "https://cdn.example.com/users/john.jpg",
  "bio": "Software engineer with 10 years experience...",
  "created_at": ISODate("2023-01-15T10:30:00Z"),
  "last_login": ISODate("2024-11-15T14:20:00Z"),
  "last_accessed": ISODate("2024-11-15T14:20:00Z"),
  "status": "active",
  "total_orders": 45,
  "lifetime_value": 12500.50
}
```

**Size:** ~500 bytes

---

#### **After Migration to S3**

**1. S3 Storage (Full Document)**

**Bucket:** `cold-data-archive`
**Key:** `users/2024/12/507f1f77bcf86cd799439011.json`
**Format:** JSON (gzip compressed)
**Content:**

```json
{
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
    "newsletter": true,
    "notifications": ["email", "sms"],
    "theme": "dark"
  },
  "profile_image": "https://cdn.example.com/users/john.jpg",
  "bio": "Software engineer with 10 years experience...",
  "created_at": "2023-01-15T10:30:00.000Z",
  "last_login": "2024-11-15T14:20:00.000Z",
  "last_accessed": "2024-11-15T14:20:00.000Z",
  "status": "active",
  "total_orders": 45,
  "lifetime_value": 12500.5,
  "_migrated_at": "2024-12-03T10:00:00.000Z",
  "_migrated_from": "hot_mongodb"
}
```

**S3 Metadata (Object Tags):**
```
Content-Type: application/json
Content-Encoding: gzip
x-amz-meta-collection: users
x-amz-meta-migrated-at: 2024-12-03T10:00:00Z
x-amz-meta-source: hot_cold_migration
```

**Size:** ~250 bytes (compressed)
**Storage Class:** S3 Standard (can transition to Glacier)

---

**2. MongoDB Metadata (Searchable Stub)**

**Collection:** `users_archive`
**Document:**

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "_storage_location": "cloud",
  "_storage_backend": "s3",
  "_storage_bucket": "cold-data-archive",
  "_storage_key": "users/2024/12/507f1f77bcf86cd799439011.json",
  "_storage_region": "us-east-1",
  "_migrated_at": ISODate("2024-12-03T10:00:00Z"),
  "_original_size_bytes": 500,
  "_compressed_size_bytes": 250,
  
  // Searchable fields (for queries)
  "email": "john@example.com",
  "name": "John Doe",
  "status": "active",
  "created_at": ISODate("2023-01-15T10:30:00Z"),
  "last_login": ISODate("2024-11-15T14:20:00Z"),
  
  // Quick stats (no need to fetch from S3)
  "total_orders": 45,
  "lifetime_value": 12500.50
}
```

**Size:** ~200 bytes
**Purpose:** Fast searches without S3 access

---

### Example 2: Order Document with Large Data

#### **Original in Hot MongoDB**

```json
{
  "_id": ObjectId("65a1b2c3d4e5f6789012345"),
  "order_number": "ORD-2024-001234",
  "customer_id": "507f1f77bcf86cd799439011",
  "items": [
    {
      "product_id": "PROD-001",
      "name": "Laptop",
      "quantity": 1,
      "price": 1299.99,
      "sku": "LAP-15-I7-16GB"
    },
    {
      "product_id": "PROD-002",
      "name": "Mouse",
      "quantity": 2,
      "price": 29.99,
      "sku": "MOU-WIRELESS-BLK"
    }
  ],
  "shipping_address": {
    "name": "John Doe",
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "country": "USA"
  },
  "billing_address": { /* same as shipping */ },
  "payment": {
    "method": "credit_card",
    "last4": "4242",
    "transaction_id": "txn_abc123xyz",
    "amount": 1359.97,
    "currency": "USD"
  },
  "tracking": {
    "carrier": "UPS",
    "tracking_number": "1Z999AA10123456784",
    "shipped_at": ISODate("2024-01-20T10:00:00Z"),
    "delivered_at": ISODate("2024-01-22T15:30:00Z")
  },
  "notes": "Please leave at front door",
  "created_at": ISODate("2024-01-18T14:30:00Z"),
  "updated_at": ISODate("2024-01-22T15:30:00Z"),
  "status": "delivered"
}
```

**Size:** ~1.5 KB

---

#### **After Migration to S3**

**S3 Storage:**

**Key:** `orders/2024/01/65a1b2c3d4e5f6789012345.json`
**Content:** Full document (as shown above) in JSON format
**Size:** ~800 bytes (gzip compressed)

---

**MongoDB Metadata:**

```json
{
  "_id": ObjectId("65a1b2c3d4e5f6789012345"),
  "_storage_location": "cloud",
  "_storage_backend": "s3",
  "_storage_key": "orders/2024/01/65a1b2c3d4e5f6789012345.json",
  "_migrated_at": ISODate("2024-12-03T10:00:00Z"),
  
  // Searchable fields
  "order_number": "ORD-2024-001234",
  "customer_id": "507f1f77bcf86cd799439011",
  "status": "delivered",
  "created_at": ISODate("2024-01-18T14:30:00Z"),
  "total_amount": 1359.97,
  
  // Summary (no need to fetch full order)
  "item_count": 2,
  "tracking_number": "1Z999AA10123456784"
}
```

**Size:** ~150 bytes

---

## 🔄 Data Flow Examples

### Scenario 1: Query Old User

```
1. User Request
   GET /api/users/507f1f77bcf86cd799439011

2. Check Hot MongoDB
   db.users.findOne({_id: "507f1f77bcf86cd799439011"})
   → Not found

3. Check Cold Metadata
   db.users_archive.findOne({_id: "507f1f77bcf86cd799439011"})
   → Found: {
       _storage_key: "users/2024/12/507f1f77bcf86cd799439011.json",
       email: "john@example.com",
       name: "John Doe"
     }

4. Fetch from S3
   s3.get_object(
     Bucket: "cold-data-archive",
     Key: "users/2024/12/507f1f77bcf86cd799439011.json"
   )
   → Download JSON file
   → Decompress gzip
   → Parse JSON

5. Return to User
   {full document from S3}
```

---

### Scenario 2: Search Orders by Customer

```
1. User Request
   GET /api/orders?customer_id=507f1f77bcf86cd799439011

2. Query Hot MongoDB
   db.orders.find({customer_id: "507f1f77bcf86cd799439011"})
   → Returns recent orders

3. Query Cold Metadata
   db.orders_archive.find({customer_id: "507f1f77bcf86cd799439011"})
   → Returns: [
       {
         _id: "65a1b2c3d4e5f6789012345",
         order_number: "ORD-2024-001234",
         total_amount: 1359.97,
         _storage_key: "orders/2024/01/65a1b2c3d4e5f6789012345.json"
       }
     ]

4. User sees summary (no S3 fetch needed)
   → Order number, total, status visible
   
5. If user clicks order details
   → Fetch full document from S3
```

---

## 📦 Storage Format Details

### JSON Format in S3

**Why JSON?**
- ✅ Human-readable
- ✅ Universal format
- ✅ Easy to process with any tool
- ✅ Compresses well (60-80% reduction)
- ✅ Can be queried with S3 Select

**Compression:**
- Default: gzip
- Alternative: zstd (better compression)
- Typical reduction: 60-80%

**Example:**
```
Original: 1000 bytes
Gzipped: 300 bytes (70% reduction)
```

---

### Alternative Formats (Optional)

#### **1. Parquet (for analytics)**

**When to use:** Large datasets, analytics queries

```python
# Convert to Parquet
import pyarrow.parquet as pq
import pandas as pd

df = pd.DataFrame([document])
pq.write_table(df, 's3://bucket/data.parquet')
```

**Benefits:**
- 90% compression
- Columnar format
- Fast analytics queries
- AWS Athena compatible

---

#### **2. Avro (for streaming)**

**When to use:** Event streams, Kafka integration

```python
# Convert to Avro
import avro.schema
from avro.datafile import DataFileWriter

writer = DataFileWriter(file, DatumWriter(), schema)
writer.append(document)
```

**Benefits:**
- Schema evolution
- Compact binary format
- Good for streaming

---

#### **3. MessagePack (for speed)**

**When to use:** Need faster serialization than JSON

```python
import msgpack

# Serialize
packed = msgpack.packb(document)

# Deserialize
document = msgpack.unpackb(packed)
```

**Benefits:**
- Faster than JSON
- Smaller than JSON
- Binary format

---

## 🎯 Recommended Format: JSON + Gzip

**For most use cases, use JSON with gzip compression:**

```python
import json
import gzip

# Serialize and compress
json_data = json.dumps(document, default=str)
compressed = gzip.compress(json_data.encode('utf-8'))

# Upload to S3
s3.put_object(
    Bucket='cold-data-archive',
    Key='users/2024/12/user123.json',
    Body=compressed,
    ContentType='application/json',
    ContentEncoding='gzip'
)
```

**Why?**
- ✅ Universal compatibility
- ✅ Good compression (60-80%)
- ✅ Human-readable (when decompressed)
- ✅ Works with S3 Select
- ✅ Easy debugging

---

## 📊 Storage Comparison

| Format | Size | Speed | Queryable | Human-Readable |
|--------|------|-------|-----------|----------------|
| **JSON** | 1.0x | Fast | Yes (S3 Select) | ✅ Yes |
| **JSON + Gzip** | 0.3x | Fast | Yes | ✅ Yes (decompress) |
| **Parquet** | 0.1x | Medium | ✅ Best | ❌ No |
| **Avro** | 0.4x | Fast | Yes | ❌ No |
| **MessagePack** | 0.5x | ✅ Fastest | No | ❌ No |

---

## 🔧 Implementation in Code

The hybrid migrator (`hybrid_migrator.py`) automatically:

1. **Serializes** document to JSON
2. **Compresses** with gzip
3. **Uploads** to S3
4. **Creates** metadata stub in MongoDB
5. **Deletes** from hot MongoDB

**No manual format conversion needed!**

---

## 💡 Best Practices

### 1. Keep Searchable Fields in Metadata

```python
# Good: Include fields you'll search by
metadata = {
    '_id': doc['_id'],
    '_storage_key': s3_key,
    'email': doc['email'],        # Searchable
    'status': doc['status'],      # Searchable
    'created_at': doc['created_at']  # Searchable
}
```

### 2. Use Consistent Key Structure

```
Format: {collection}/{year}/{month}/{document_id}.json

Examples:
users/2024/12/507f1f77bcf86cd799439011.json
orders/2024/01/65a1b2c3d4e5f6789012345.json
logs/2024/11/log_abc123.json
```

### 3. Add S3 Lifecycle Policies

```json
{
  "Rules": [{
    "Id": "TransitionToGlacier",
    "Status": "Enabled",
    "Transitions": [{
      "Days": 90,
      "StorageClass": "GLACIER"
    }]
  }]
}
```

### 4. Enable S3 Versioning (Optional)

```bash
aws s3api put-bucket-versioning \
  --bucket cold-data-archive \
  --versioning-configuration Status=Enabled
```

---

## 📝 Summary

**Data Formats:**
- **Hot MongoDB:** BSON (native)
- **Cold S3:** JSON + gzip
- **Cold Metadata:** BSON (minimal)

**Why This Works:**
- ✅ 60-80% storage savings
- ✅ Fast searches (metadata in MongoDB)
- ✅ Full data available (S3)
- ✅ Universal format (JSON)
- ✅ Cost-effective (S3 cheaper than MongoDB)

**No Manual Work:**
- Migration script handles everything
- Automatic format conversion
- Transparent to application

---

**Next:** See `S3_CLOUD_STORAGE_SETUP.md` for setup instructions!
