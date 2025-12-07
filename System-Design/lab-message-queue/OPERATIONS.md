# Operations Guide

Operational guide for running and maintaining the distributed message queue system.

## Table of Contents

1. [Cluster Setup](#cluster-setup)
2. [Monitoring](#monitoring)
3. [Troubleshooting](#troubleshooting)
4. [Performance Tuning](#performance-tuning)
5. [Backup and Recovery](#backup-and-recovery)
6. [Scaling](#scaling)

---

## Cluster Setup

### Single-Node Setup

For development and testing:

```bash
# Start broker
python broker/broker.py 1 9092

# Create topic
python -c "
from client.producer import Producer, ProducerConfig
p = Producer(ProducerConfig(bootstrap_servers=['localhost:9092']))
p.start()
p.send('test-topic', 'test')
p.close()
"
```

### Multi-Node Cluster

#### Using Docker Compose

```bash
# Start 3-broker cluster
cd docker
docker-compose up -d

# View logs
docker-compose logs -f broker-1

# Stop cluster
docker-compose down -v
```

#### Manual Setup

**Broker 1:**
```bash
python broker/broker.py 1 9092
```

**Broker 2:**
```bash
python broker/broker.py 2 9093
```

**Broker 3:**
```bash
python broker/broker.py 3 9094
```

### Kubernetes Deployment

```bash
# Deploy brokers
kubectl apply -f k8s/statefulset.yaml

# Deploy services
kubectl apply -f k8s/service.yaml

# Check status
kubectl get pods -l app=message-queue

# View logs
kubectl logs -f message-queue-0
```

---

## Monitoring

### Key Metrics

#### Broker Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `messages_in_per_sec` | Message ingestion rate | - |
| `bytes_in_per_sec` | Data ingestion rate | > 80% capacity |
| `messages_out_per_sec` | Message consumption rate | - |
| `active_connections` | Number of client connections | > 1000 |
| `isr_shrinks` | ISR shrink events | > 0 |
| `isr_expands` | ISR expand events | - |
| `under_replicated_partitions` | Partitions with ISR < replication factor | > 0 |
| `offline_partitions` | Partitions without leader | > 0 |

#### Producer Metrics

| Metric | Description |
|--------|-------------|
| `record_send_rate` | Records sent per second |
| `record_error_rate` | Failed sends per second |
| `batch_size_avg` | Average batch size |
| `request_latency_avg` | Average request latency |

#### Consumer Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `records_consumed_rate` | Records consumed per second | - |
| `fetch_latency_avg` | Average fetch latency | > 1000ms |
| `consumer_lag` | Offset lag behind producer | > 10000 |
| `rebalance_rate` | Rebalances per hour | > 5 |

### Monitoring Tools

#### Prometheus

Access at http://localhost:9090

**Example Queries:**

```promql
# Message throughput
rate(messages_in_total[5m])

# Consumer lag
consumer_lag{group="my-group"}

# Under-replicated partitions
under_replicated_partitions > 0
```

#### Grafana

Access at http://localhost:3000 (admin/admin)

**Dashboards:**
- Broker Overview
- Producer Performance
- Consumer Lag
- Cluster Health

---

## Troubleshooting

### Common Issues

#### 1. Broker Not Starting

**Symptoms:**
- Broker fails to start
- Port already in use error

**Solutions:**
```bash
# Check if port is in use
lsof -i :9092

# Kill existing process
kill -9 <PID>

# Check data directory permissions
ls -la /var/lib/message-queue/data
chmod 755 /var/lib/message-queue/data
```

#### 2. Producer Timeout

**Symptoms:**
- Producer hangs or times out
- `request_timeout_ms` exceeded

**Solutions:**
```python
# Increase timeout
config = ProducerConfig(
    request_timeout_ms=60000,  # 60 seconds
    retries=5
)

# Check broker health
# Verify network connectivity
ping broker-host
telnet broker-host 9092
```

#### 3. Consumer Lag

**Symptoms:**
- Consumer falling behind producer
- High `consumer_lag` metric

**Solutions:**
```python
# Increase consumer parallelism
# Add more consumers to group (up to num_partitions)

# Increase fetch size
config = ConsumerConfig(
    max_poll_records=1000,
    fetch_max_bytes=10485760  # 10MB
)

# Optimize processing
# Use async processing with worker threads
```

#### 4. Under-Replicated Partitions

**Symptoms:**
- `under_replicated_partitions` > 0
- ISR smaller than replication factor

**Solutions:**
```bash
# Check broker health
# Verify network connectivity between brokers

# Check broker logs for replication errors
docker-compose logs broker-1 | grep -i replication

# Restart slow/failed broker
docker-compose restart broker-2
```

#### 5. Out of Memory

**Symptoms:**
- Broker crashes with OOM
- High memory usage

**Solutions:**
```yaml
# Reduce buffer sizes in config/broker.yaml
socket_send_buffer_bytes: 51200  # Reduce from 102400
socket_receive_buffer_bytes: 51200

# Reduce log segment size
log_segment_bytes: 536870912  # 512MB instead of 1GB

# Increase broker memory
# In docker-compose.yml:
services:
  broker-1:
    mem_limit: 2g
```

---

## Performance Tuning

### Producer Optimization

#### High Throughput

```python
config = ProducerConfig(
    acks=AckMode.LEADER,        # Don't wait for all replicas
    batch_size=65536,           # 64KB batches
    linger_ms=100,              # Wait for batching
    compression_type='lz4',     # Fast compression
    max_in_flight_requests=10   # More concurrent requests
)
```

#### Low Latency

```python
config = ProducerConfig(
    acks=AckMode.LEADER,
    batch_size=1024,            # Small batches
    linger_ms=0,                # Send immediately
    compression_type='none'     # No compression overhead
)
```

#### High Durability

```python
config = ProducerConfig(
    acks=AckMode.ALL,           # Wait for all ISR
    retries=10,
    enable_idempotence=True,    # Exactly-once
    max_in_flight_requests=1    # Strict ordering
)
```

### Consumer Optimization

#### High Throughput

```python
config = ConsumerConfig(
    max_poll_records=1000,
    fetch_min_bytes=10240,      # 10KB minimum
    fetch_max_wait_ms=100,      # Wait for batching
    max_partition_fetch_bytes=2097152  # 2MB per partition
)
```

#### Low Latency

```python
config = ConsumerConfig(
    max_poll_records=100,
    fetch_min_bytes=1,          # Don't wait for data
    fetch_max_wait_ms=10        # Short wait time
)
```

### Broker Tuning

```yaml
# config/broker.yaml

# Network threads (1 per core)
num_network_threads: 8

# I/O threads (2x cores)
num_io_threads: 16

# Larger buffers for high throughput
socket_send_buffer_bytes: 1048576    # 1MB
socket_receive_buffer_bytes: 1048576

# Replica fetcher threads
num_replica_fetchers: 8

# Larger log segments for sequential I/O
log_segment_bytes: 2147483648  # 2GB
```

### OS-Level Tuning

```bash
# Increase file descriptors
ulimit -n 100000

# Increase socket buffers
sysctl -w net.core.rmem_max=134217728  # 128MB
sysctl -w net.core.wmem_max=134217728

# Disable swap
swapoff -a

# Use deadline I/O scheduler
echo deadline > /sys/block/sda/queue/scheduler
```

---

## Backup and Recovery

### Backup Strategy

#### Data Backup

```bash
# Stop broker
docker-compose stop broker-1

# Backup data directory
tar -czf broker-1-backup-$(date +%Y%m%d).tar.gz /var/lib/message-queue/data

# Restart broker
docker-compose start broker-1
```

#### Metadata Backup

```bash
# Export topic metadata
python -c "
from coordinator.cluster_coordinator import ClusterCoordinator
coordinator = ClusterCoordinator(1)
# Export metadata to JSON
import json
with open('metadata-backup.json', 'w') as f:
    json.dump(coordinator.cluster_metadata, f)
"
```

### Disaster Recovery

#### Broker Failure

```bash
# 1. Remove failed broker from cluster
# 2. Start new broker with same broker_id
# 3. Data will be replicated from other brokers

docker-compose up -d broker-1
```

#### Complete Cluster Loss

```bash
# 1. Restore data from backups
tar -xzf broker-1-backup.tar.gz -C /

# 2. Start brokers
docker-compose up -d

# 3. Verify data integrity
python examples/simple_consumer.py
```

---

## Scaling

### Adding Brokers

```bash
# 1. Start new broker
docker-compose up -d broker-4

# 2. Broker will join cluster automatically

# 3. Reassign partitions (manual in this implementation)
# In production, use partition reassignment tools
```

### Adding Partitions

```python
# Create topic with more partitions
from client.producer import Producer, ProducerConfig

producer = Producer(ProducerConfig(bootstrap_servers=['localhost:9092']))
producer.start()

# Send to new topic (auto-creates with default partitions)
# Or use admin API to specify partition count
```

### Scaling Consumers

```bash
# Add more consumers to group (up to num_partitions)
# Each consumer will be assigned partitions automatically

# Terminal 1
python examples/simple_consumer.py

# Terminal 2
python examples/simple_consumer.py

# Terminal 3
python examples/simple_consumer.py
```

### Capacity Planning

#### Storage

```
Daily messages: 1 billion
Avg message size: 1 KB
Retention: 7 days
Replication: 3x

Storage = 1B * 1KB * 7 * 3 = 21 TB
Add 20% overhead = 25 TB
```

#### Brokers

```
Target throughput: 500 MB/s
Broker capacity: 50 MB/s (with replication)
Replication factor: 3

Brokers = (500 / 50) * 3 = 30 brokers
```

#### Partitions

```
Consumer throughput: 10 MB/s per consumer
Total throughput: 500 MB/s

Partitions = 500 / 10 = 50 partitions
```

---

## Best Practices

### Production Checklist

- [ ] Enable replication (factor ≥ 3)
- [ ] Set `min.insync.replicas` ≥ 2
- [ ] Disable `unclean.leader.election`
- [ ] Configure log retention
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure alerts for critical metrics
- [ ] Implement backup strategy
- [ ] Document runbooks
- [ ] Test disaster recovery procedures
- [ ] Tune OS parameters
- [ ] Use dedicated hardware/VMs for brokers
- [ ] Separate data and log directories
- [ ] Use RAID for data disks
- [ ] Monitor disk I/O and network

### Security

```yaml
# Enable authentication (not implemented in this version)
# In production, use:
# - SSL/TLS for encryption
# - SASL for authentication
# - ACLs for authorization
```

### Monitoring Alerts

```yaml
# Prometheus alerting rules
groups:
  - name: message_queue
    rules:
      - alert: UnderReplicatedPartitions
        expr: under_replicated_partitions > 0
        for: 5m
        annotations:
          summary: "Partitions are under-replicated"
      
      - alert: OfflinePartitions
        expr: offline_partitions > 0
        for: 1m
        annotations:
          summary: "Partitions are offline"
      
      - alert: HighConsumerLag
        expr: consumer_lag > 10000
        for: 10m
        annotations:
          summary: "Consumer lag is high"
```

---

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review metrics: http://localhost:9090
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Open GitHub issue
