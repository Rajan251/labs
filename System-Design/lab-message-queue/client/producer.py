"""Producer client for the distributed message queue."""

import socket
import json
import hashlib
import threading
import time
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass
from queue import Queue, Full
from enum import Enum


class AckMode(Enum):
    """Acknowledgment modes for producers."""
    NONE = '0'      # No acknowledgment
    LEADER = '1'    # Leader acknowledgment only
    ALL = 'all'     # All in-sync replicas


@dataclass
class ProducerConfig:
    """Producer configuration."""
    bootstrap_servers: List[str]  # ['localhost:9092', 'localhost:9093']
    acks: AckMode = AckMode.LEADER
    batch_size: int = 16384  # 16KB
    linger_ms: int = 0  # Wait time before sending batch
    buffer_memory: int = 33554432  # 32MB
    max_block_ms: int = 60000  # Block time if buffer full
    retries: int = 3
    retry_backoff_ms: int = 100
    request_timeout_ms: int = 30000
    compression_type: str = 'none'  # 'none', 'gzip', 'snappy'
    max_in_flight_requests: int = 5
    enable_idempotence: bool = False


class Partitioner:
    """Handles partition selection for messages."""
    
    @staticmethod
    def partition(key: Optional[str], num_partitions: int, 
                 strategy: str = 'hash') -> int:
        """
        Select a partition for the message.
        
        Strategies:
        - 'hash': Hash-based partitioning (same key -> same partition)
        - 'round_robin': Round-robin distribution
        """
        if strategy == 'hash' and key:
            # Hash the key and mod by number of partitions
            hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
            return hash_value % num_partitions
        else:
            # Round-robin (simplified - would need counter in real implementation)
            return hash(str(time.time())) % num_partitions


class MessageBatch:
    """A batch of messages for a specific topic-partition."""
    
    def __init__(self, topic: str, partition: int, max_size: int):
        self.topic = topic
        self.partition = partition
        self.max_size = max_size
        self.messages: List[Dict] = []
        self.size = 0
        self.created_at = time.time()
    
    def try_append(self, message: Dict) -> bool:
        """Try to append a message to the batch."""
        message_size = len(json.dumps(message))
        
        if self.size + message_size > self.max_size:
            return False
        
        self.messages.append(message)
        self.size += message_size
        return True
    
    def is_full(self) -> bool:
        """Check if the batch is full."""
        return self.size >= self.max_size
    
    def age_ms(self) -> float:
        """Get the age of the batch in milliseconds."""
        return (time.time() - self.created_at) * 1000


class Producer:
    """
    Producer client for sending messages to the queue.
    
    Features:
    - Asynchronous batching
    - Automatic retries
    - Partitioning strategies
    - Callbacks for success/error
    """
    
    def __init__(self, config: ProducerConfig):
        self.config = config
        self.running = False
        
        # Connection pool
        self.connections: Dict[str, socket.socket] = {}
        self.connection_lock = threading.Lock()
        
        # Batching
        self.batches: Dict[str, MessageBatch] = {}  # key: topic-partition
        self.batch_lock = threading.Lock()
        
        # Async send queue
        self.send_queue: Queue = Queue(maxsize=1000)
        
        # Background threads
        self.sender_thread: Optional[threading.Thread] = None
        
        # Metadata cache
        self.metadata: Dict[str, Any] = {}
        self.metadata_lock = threading.Lock()
        
        # Sequence numbers for idempotence
        self.sequence_numbers: Dict[str, int] = {}
        
    def start(self):
        """Start the producer."""
        self.running = True
        
        # Fetch initial metadata
        self._refresh_metadata()
        
        # Start sender thread
        self.sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self.sender_thread.start()
        
        print("[Producer] Started")
    
    def send(self, topic: str, value: str, key: Optional[str] = None,
             headers: Optional[Dict[str, str]] = None,
             partition: Optional[int] = None,
             callback: Optional[Callable] = None):
        """
        Send a message asynchronously.
        
        Args:
            topic: Topic name
            value: Message value
            key: Optional message key
            headers: Optional headers
            partition: Optional partition (auto-selected if None)
            callback: Optional callback(metadata, error)
        """
        # Get partition
        if partition is None:
            num_partitions = self._get_num_partitions(topic)
            partition = Partitioner.partition(key, num_partitions)
        
        # Create message
        message = {
            'key': key,
            'value': value,
            'headers': headers or {},
            'timestamp': int(time.time() * 1000)
        }
        
        # Add to batch
        batch_key = f"{topic}-{partition}"
        
        with self.batch_lock:
            if batch_key not in self.batches:
                self.batches[batch_key] = MessageBatch(
                    topic, partition, self.config.batch_size
                )
            
            batch = self.batches[batch_key]
            
            # Try to append to existing batch
            if not batch.try_append(message):
                # Batch is full, send it
                self._send_batch(batch)
                
                # Create new batch
                self.batches[batch_key] = MessageBatch(
                    topic, partition, self.config.batch_size
                )
                self.batches[batch_key].try_append(message)
    
    def _sender_loop(self):
        """Background thread for sending batches."""
        while self.running:
            time.sleep(0.01)  # 10ms
            
            # Check for batches ready to send
            with self.batch_lock:
                batches_to_send = []
                
                for batch_key, batch in list(self.batches.items()):
                    # Send if batch is full or linger time exceeded
                    if batch.is_full() or batch.age_ms() >= self.config.linger_ms:
                        batches_to_send.append(batch)
                        del self.batches[batch_key]
                
                # Send batches
                for batch in batches_to_send:
                    self._send_batch(batch)
    
    def _send_batch(self, batch: MessageBatch):
        """Send a batch of messages to the broker."""
        if not batch.messages:
            return
        
        # Prepare request
        request = {
            'api': 'produce',
            'topic': batch.topic,
            'partition': batch.partition,
            'messages': batch.messages,
            'acks': self.config.acks.value
        }
        
        # Send with retries
        for attempt in range(self.config.retries + 1):
            try:
                # Get broker for partition
                broker_addr = self._get_leader_broker(batch.topic, batch.partition)
                
                # Send request
                response = self._send_request(broker_addr, request)
                
                if response.get('status') == 'success':
                    print(f"[Producer] Sent batch to {batch.topic}-{batch.partition}: "
                          f"{len(batch.messages)} messages, offsets: {response['offsets']}")
                    return
                else:
                    error = response.get('error', 'Unknown error')
                    print(f"[Producer] Error sending batch: {error}")
                    
            except Exception as e:
                print(f"[Producer] Send attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.retries:
                    time.sleep(self.config.retry_backoff_ms / 1000)
        
        print(f"[Producer] Failed to send batch after {self.config.retries + 1} attempts")
    
    def _send_request(self, broker_addr: str, request: dict) -> dict:
        """Send a request to a broker."""
        # Get connection
        conn = self._get_connection(broker_addr)
        
        # Serialize request
        request_data = json.dumps(request).encode('utf-8')
        length = len(request_data)
        
        # Send length prefix + request
        conn.sendall(length.to_bytes(4, byteorder='big'))
        conn.sendall(request_data)
        
        # Read response length
        length_bytes = conn.recv(4)
        length = int.from_bytes(length_bytes, byteorder='big')
        
        # Read response data
        response_data = b''
        while len(response_data) < length:
            chunk = conn.recv(min(length - len(response_data), 4096))
            response_data += chunk
        
        # Parse response
        return json.loads(response_data.decode('utf-8'))
    
    def _get_connection(self, broker_addr: str) -> socket.socket:
        """Get or create a connection to a broker."""
        with self.connection_lock:
            if broker_addr not in self.connections:
                host, port = broker_addr.split(':')
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.connect((host, int(port)))
                self.connections[broker_addr] = conn
            
            return self.connections[broker_addr]
    
    def _refresh_metadata(self):
        """Refresh metadata from brokers."""
        for broker_addr in self.config.bootstrap_servers:
            try:
                request = {'api': 'metadata'}
                response = self._send_request(broker_addr, request)
                
                with self.metadata_lock:
                    self.metadata = response
                
                print(f"[Producer] Refreshed metadata from {broker_addr}")
                return
                
            except Exception as e:
                print(f"[Producer] Failed to get metadata from {broker_addr}: {e}")
        
        raise Exception("Failed to get metadata from any broker")
    
    def _get_num_partitions(self, topic: str) -> int:
        """Get the number of partitions for a topic."""
        with self.metadata_lock:
            topics = self.metadata.get('topics', {})
            if topic in topics:
                return topics[topic]['num_partitions']
        
        # Default to 1 if not found
        return 1
    
    def _get_leader_broker(self, topic: str, partition: int) -> str:
        """Get the leader broker for a topic-partition."""
        # Simplified: just use first bootstrap server
        return self.config.bootstrap_servers[0]
    
    def flush(self):
        """Flush all pending messages."""
        with self.batch_lock:
            for batch in list(self.batches.values()):
                self._send_batch(batch)
            self.batches.clear()
    
    def close(self):
        """Close the producer."""
        print("[Producer] Closing")
        self.running = False
        
        # Flush pending messages
        self.flush()
        
        # Wait for sender thread
        if self.sender_thread:
            self.sender_thread.join(timeout=5)
        
        # Close connections
        with self.connection_lock:
            for conn in self.connections.values():
                conn.close()
        
        print("[Producer] Closed")


def main():
    """Example usage."""
    config = ProducerConfig(
        bootstrap_servers=['localhost:9092'],
        acks=AckMode.LEADER,
        batch_size=1024,
        linger_ms=100
    )
    
    producer = Producer(config)
    producer.start()
    
    try:
        # Send some messages
        for i in range(10):
            producer.send(
                topic='test-topic',
                key=f'key-{i % 3}',
                value=f'Message {i}'
            )
            time.sleep(0.1)
        
        # Flush and close
        producer.flush()
        
    finally:
        producer.close()


if __name__ == '__main__':
    main()
