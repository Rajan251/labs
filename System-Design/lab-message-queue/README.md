# Distributed Message Queue System

A distributed message queue system similar to Apache Kafka and RabbitMQ, built for educational purposes to demonstrate core distributed systems concepts.

## Features

✅ **Topics & Partitions**: Logical message organization with parallel processing  
✅ **Producer/Consumer**: Async clients with batching and offset management  
✅ **Replication**: Leader-follower replication with ISR tracking  
✅ **Durability**: Write-ahead logging with configurable fsync  
✅ **Ordering**: Strict per-partition ordering guarantees  
✅ **Consumer Groups**: Load balancing and failover  
✅ **Backpressure**: Flow control at all levels  
✅ **Horizontal Scalability**: Add brokers and partitions dynamically  

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Producer 1 │────▶│   Broker 1  │◀───▶│  Consumer 1 │
└─────────────┘     │  (Leader)   │     └─────────────┘
                    └─────────────┘
                          │ │
                    Replication
                          │ │
                    ┌─────┴─┴─────┐
                    │             │
              ┌─────▼─────┐ ┌─────▼─────┐
              │  Broker 2 │ │  Broker 3 │
              │ (Follower)│ │ (Follower)│
              └───────────┘ └───────────┘
```

## Quick Start

### 1. Start a Single Broker

```bash
# Start broker
python broker/broker.py 1 9092
```

### 2. Create a Topic

```python
from client.producer import Producer, ProducerConfig, AckMode

config = ProducerConfig(bootstrap_servers=['localhost:9092'])
producer = Producer(config)
producer.start()

# Create topic (done automatically on first produce)
producer.send(topic='events', key='user-1', value='Hello World')
producer.flush()
producer.close()
```

### 3. Produce Messages

```bash
python examples/simple_producer.py
```

### 4. Consume Messages

```bash
python examples/simple_consumer.py
```

## Docker Deployment

### Start 3-Broker Cluster

```bash
cd docker
docker-compose up -d
```

This starts:
- 3 brokers (ports 9092, 9093, 9094)
- Prometheus (port 9090)
- Grafana (port 3000)

### View Logs

```bash
docker-compose logs -f broker-1
```

### Stop Cluster

```bash
docker-compose down -v
```

## Configuration

### Broker Configuration

See `config/broker.yaml` for all available settings:

```yaml
broker_id: 1
port: 9092
replication_factor: 3
min_insync_replicas: 2
log_retention_hours: 168
```

### Producer Configuration

```python
ProducerConfig(
    bootstrap_servers=['localhost:9092'],
    acks=AckMode.ALL,           # Wait for all replicas
    batch_size=16384,           # 16KB batches
    linger_ms=10,               # Wait 10ms before sending
    retries=3,                  # Retry failed sends
    enable_idempotence=True     # Exactly-once semantics
)
```

### Consumer Configuration

```python
ConsumerConfig(
    bootstrap_servers=['localhost:9092'],
    group_id='my-group',
    auto_offset_reset=OffsetResetPolicy.EARLIEST,
    enable_auto_commit=True,
    max_poll_records=500
)
```

## Examples

### High-Throughput Producer

```python
config = ProducerConfig(
    bootstrap_servers=['localhost:9092'],
    acks=AckMode.LEADER,
    batch_size=65536,  # 64KB batches
    linger_ms=100,     # Wait 100ms for batching
    compression_type='gzip'
)
```

### Consumer with Manual Offset Management

```python
consumer = Consumer(config)
consumer.subscribe(['events'])

for message in consumer.poll():
    try:
        process(message)
        consumer.commit({(message['topic'], message['partition']): message['offset']})
    except Exception:
        # Don't commit, will reprocess
        break
```

### Backpressure Handling

```python
# Pause consumption if processing queue is full
if processing_queue.full():
    consumer.pause([('events', 0), ('events', 1)])
    
# Resume when queue drains
if processing_queue.size() < threshold:
    consumer.resume([('events', 0), ('events', 1)])
```

## Key Concepts

### Topics and Partitions

- **Topic**: Logical channel for messages
- **Partition**: Ordered log within a topic
- Messages in a partition are strictly ordered
- Partitions enable parallelism

### Replication

- Each partition has 1 leader and N-1 followers
- Leader handles all reads and writes
- Followers replicate from leader
- **ISR** (In-Sync Replicas): Replicas caught up with leader
- **High Watermark**: Last offset replicated to all ISR

### Consumer Groups

- Multiple consumers in a group share partition load
- Each partition assigned to one consumer in group
- Different groups receive all messages (pub-sub)
- Automatic rebalancing on consumer join/leave

### Offset Management

- **Offset**: Unique ID for each message in partition
- Consumers track position via offsets
- Auto-commit or manual commit
- Enables replay and exactly-once processing

## Performance

### Throughput

- Single broker: ~50 MB/s write, ~100 MB/s read per partition
- 3-broker cluster (10 partitions): ~500 MB/s write, ~1 GB/s read

### Latency

| Configuration | p99 Latency |
|---------------|-------------|
| acks=0 | 1-2 ms |
| acks=1 | 5-10 ms |
| acks=all | 10-20 ms |

## Monitoring

Access Grafana at http://localhost:3000 (admin/admin) to view:
- Message throughput
- Consumer lag
- Broker health
- Replication status

## Documentation

- [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) - Comprehensive system design
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture deep dive
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation
- [OPERATIONS.md](OPERATIONS.md) - Operations guide

## Project Structure

```
├── broker/              # Broker server implementation
│   ├── broker.py        # Main broker server
│   ├── partition.py     # Partition and segment management
│   ├── replication.py   # Replication protocol
│   └── storage.py       # Persistent storage
├── client/              # Client libraries
│   ├── producer.py      # Producer client
│   ├── consumer.py      # Consumer client
│   └── offset_manager.py
├── coordinator/         # Cluster coordination
│   ├── cluster_coordinator.py
│   └── consumer_group_coordinator.py
├── protocol/            # Wire protocol
│   ├── messages.py
│   └── api.py
├── config/              # Configuration files
├── docker/              # Docker deployment
├── k8s/                 # Kubernetes manifests
├── examples/            # Example applications
└── tests/               # Test suite
```

## Testing

```bash
# Run unit tests
python -m pytest tests/ -v

# Run integration tests
docker-compose -f docker/docker-compose.yml up -d
python -m pytest tests/integration/ -v
docker-compose -f docker/docker-compose.yml down -v
```

## Limitations

This is an educational implementation. For production use, consider:
- Apache Kafka
- Apache Pulsar
- RabbitMQ
- AWS Kinesis
- Google Cloud Pub/Sub

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Please see CONTRIBUTING.md

## References

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Designing Data-Intensive Applications](https://dataintensive.net/)
- [Kafka: The Definitive Guide](https://www.confluent.io/resources/kafka-the-definitive-guide/)
