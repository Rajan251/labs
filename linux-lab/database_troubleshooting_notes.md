# Database Performance Troubleshooting

**Level:** Expert / DBA / SRE
**Focus:** Systematic diagnosis and resolution of database performance issues.

---

## 1. Symptoms to Investigate

### 1.1 Common Symptoms
*   **High CPU**: Database server CPU >80%.
*   **Slow Queries**: Response times >1s for typical queries.
*   **Connection Timeouts**: Clients can't connect or timeout.
*   **Replication Lag**: Read replicas seconds/minutes behind master.

---

## 2. Data Collection Phase

### 2.1 System Level
```bash
top -b -n 1
vmstat 1 10
iostat -x 1 10
netstat -s
```

### 2.2 Database Level (MySQL)
```sql
SHOW PROCESSLIST;
SHOW ENGINE INNODB STATUS;
SHOW GLOBAL STATUS LIKE '%lock%';
```

### 2.3 Query Level
```sql
-- Enable slow query log
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;

-- Analyze query
EXPLAIN SELECT * FROM orders WHERE user_id = 123;
```

### 2.4 Schema Level
```sql
-- Table sizes
SELECT table_name, 
       ROUND(data_length/1024/1024, 2) AS data_mb
FROM information_schema.tables
WHERE table_schema = 'mydb'
ORDER BY data_length DESC;
```

---

## 3. Analysis Framework

### 3.1 Resource Contention
*   **CPU**: Too many queries, missing indexes.
*   **Memory**: Insufficient buffer pool, swapping.
*   **Disk I/O**: Slow storage, fragmentation.

### 3.2 Query Optimization
*   **Missing Indexes**: Full table scans.
*   **Suboptimal Joins**: Cartesian products.

### 3.3 Configuration Issues
*   **Buffer Pool**: Too small (`innodb_buffer_pool_size`).
*   **Connections**: Max connections too low.

---

## 4. Common Patterns

### 4.1 N+1 Query Problem
```python
# BAD: N+1 queries
for user in users:
    orders = db.query("SELECT * FROM orders WHERE user_id = ?", user.id)

# GOOD: Single query with join
orders = db.query("SELECT * FROM orders JOIN users ON orders.user_id = users.id")
```

### 4.2 Missing Indexes
```sql
-- Symptom: Full table scan
EXPLAIN SELECT * FROM orders WHERE status = 'pending';
-- Shows: type=ALL (bad)

-- Fix: Add index
CREATE INDEX idx_status ON orders(status);
```

### 4.3 Lock Contention
```sql
-- Check for locks
SHOW ENGINE INNODB STATUS;
-- Look for "LATEST DETECTED DEADLOCK"
```

---

## 5. Diagnostic Commands Reference

### 5.1 MySQL
```sql
SHOW ENGINE INNODB STATUS;
SHOW PROCESSLIST;
SELECT * FROM performance_schema.events_statements_summary_by_digest
ORDER BY sum_timer_wait DESC LIMIT 10;
```

### 5.2 PostgreSQL
```sql
SELECT * FROM pg_stat_activity WHERE state = 'active';
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

### 5.3 MongoDB
```javascript
db.currentOp()
db.collection.find().explain("executionStats")
```

### 5.4 Redis
```bash
redis-cli INFO
redis-cli SLOWLOG GET 10
```

---

## 6. Resolution Strategies

### 6.1 Immediate
*   **Kill Queries**: `KILL <query_id>`.
*   **Limit Connections**: Temporarily reduce max_connections.

### 6.2 Short-term
*   **Add Indexes**: `CREATE INDEX`.
*   **Rewrite Queries**: Optimize joins, remove subqueries.

### 6.3 Long-term
*   **Schema Redesign**: Normalize/denormalize.
*   **Hardware Upgrade**: More RAM, faster disks.

### 6.4 Architectural
*   **Read/Write Splitting**: Route reads to replicas.
*   **Sharding**: Partition data across multiple databases.

---

## 7. Real-world Examples

### Example 1: E-commerce Checkout Slowdown
*   **Symptom**: Checkout taking 10s instead of 1s.
*   **Investigation**: Slow query log shows inventory check query.
*   **Root Cause**: Missing index on `products.sku`.
*   **Fix**: `CREATE INDEX idx_sku ON products(sku)`.
*   **Result**: Checkout back to 1s.

### Example 2: Replication Lag During Backups
*   **Symptom**: Read replica 5 minutes behind master.
*   **Investigation**: `SHOW SLAVE STATUS` shows high `Seconds_Behind_Master`.
*   **Root Cause**: Backup process locking tables.
*   **Fix**: Use `mysqldump --single-transaction` (no locks).
*   **Result**: Replication lag <1s.
