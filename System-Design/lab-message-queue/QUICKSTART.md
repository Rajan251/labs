# Quick Start Guide

Get started with the distributed message queue system in 5 minutes.

## Prerequisites

- Python 3.8+
- Docker (optional, for cluster deployment)

## Option 1: Single Broker (Quickest)

### 1. Start Broker

```bash
cd /home/rk/Documents/labs/System-Design/lab-message-queue
python broker/broker.py 1 9092
```

### 2. Run Producer (New Terminal)

```bash
cd /home/rk/Documents/labs/System-Design/lab-message-queue
python examples/simple_producer.py
```

### 3. Run Consumer (New Terminal)

```bash
cd /home/rk/Documents/labs/System-Design/lab-message-queue
python examples/simple_consumer.py
```

## Option 2: 3-Broker Cluster with Docker

### 1. Start Cluster

```bash
cd /home/rk/Documents/labs/System-Design/lab-message-queue/docker
docker-compose up -d
```

### 2. View Logs

```bash
docker-compose logs -f broker-1
```

### 3. Run Examples

```bash
# Producer
docker-compose run --rm producer

# Consumer
docker-compose run --rm consumer
```

### 4. Access Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### 5. Stop Cluster

```bash
docker-compose down -v
```

## Next Steps

- Read [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) for comprehensive design documentation
- Read [ARCHITECTURE.md](ARCHITECTURE.md) for architecture deep dive
- Read [OPERATIONS.md](OPERATIONS.md) for operational guidance
- Explore [examples/](examples/) for more usage patterns

## Common Commands

```bash
# Check broker status
docker-compose ps

# View broker logs
docker-compose logs -f broker-1

# Restart broker
docker-compose restart broker-1

# Scale consumers
docker-compose up -d --scale consumer=3
```

## Troubleshooting

**Broker won't start**:
```bash
# Check if port is in use
lsof -i :9092

# Kill existing process
kill -9 <PID>
```

**Connection refused**:
```bash
# Verify broker is running
docker-compose ps

# Check network
docker network ls
```

**No messages received**:
```bash
# Check producer sent messages
docker-compose logs producer

# Verify topic exists
# (In this implementation, topics are auto-created)
```

## Configuration

Edit `config/broker.yaml` to customize:
- Replication factor
- Retention period
- Performance settings

Edit `docker/docker-compose.yml` to:
- Add more brokers
- Change ports
- Adjust resources
