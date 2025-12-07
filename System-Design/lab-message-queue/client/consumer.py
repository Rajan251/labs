"""Consumer client for the distributed message queue."""

import socket
import json
import threading
import time
from typing import Optional, Dict, List, Set, Callable
from dataclasses import dataclass
from enum import Enum


class OffsetResetPolicy(Enum):
    """Offset reset policies."""
    EARLIEST = 'earliest'  # Start from beginning
    LATEST = 'latest'      # Start from end
    NONE = 'none'          # Throw exception


@dataclass
class ConsumerConfig:
    """Consumer configuration."""
    bootstrap_servers: List[str]
    group_id: str
    auto_offset_reset: OffsetResetPolicy = OffsetResetPolicy.LATEST
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 5000
    max_poll_records: int = 500
    fetch_min_bytes: int = 1
    fetch_max_wait_ms: int = 500
    fetch_max_bytes: int = 52428800  # 50MB
    max_partition_fetch_bytes: int = 1048576  # 1MB
    session_timeout_ms: int = 10000
    heartbeat_interval_ms: int = 3000
    max_poll_interval_ms: int = 300000  # 5 minutes


class PartitionAssignment:
    """Represents partition assignment for a consumer."""
    
    def __init__(self):
        self.partitions: Dict[str, Set[int]] = {}  # topic -> set of partition ids
        self.lock = threading.Lock()
    
    def assign(self, topic: str, partitions: Set[int]):
        """Assign partitions for a topic."""
        with self.lock:
            self.partitions[topic] = partitions
    
    def revoke(self, topic: str):
        """Revoke all partitions for a topic."""
        with self.lock:
            if topic in self.partitions:
                del self.partitions[topic]
    
    def get_partitions(self, topic: str) -> Set[int]:
        """Get assigned partitions for a topic."""
        with self.lock:
            return self.partitions.get(topic, set()).copy()
    
    def all_partitions(self) -> List[tuple]:
        """Get all assigned topic-partition pairs."""
        with self.lock:
            result = []
            for topic, partitions in self.partitions.items():
                for partition_id in partitions:
                    result.append((topic, partition_id))
            return result


class OffsetManager:
    """Manages consumer offsets."""
    
    def __init__(self, group_id: str):
        self.group_id = group_id
        self.offsets: Dict[tuple, int] = {}  # (topic, partition) -> offset
        self.lock = threading.Lock()
    
    def commit(self, topic: str, partition: int, offset: int):
        """Commit an offset."""
        with self.lock:
            self.offsets[(topic, partition)] = offset
    
    def get_offset(self, topic: str, partition: int) -> Optional[int]:
        """Get the committed offset."""
        with self.lock:
            return self.offsets.get((topic, partition))
    
    def reset(self, topic: str, partition: int):
        """Reset offset for a partition."""
        with self.lock:
            key = (topic, partition)
            if key in self.offsets:
                del self.offsets[key]


class Consumer:
    """
    Consumer client for reading messages from the queue.
    
    Features:
    - Consumer group support
    - Automatic offset management
    - Rebalancing
    - Backpressure handling
    """
    
    def __init__(self, config: ConsumerConfig):
        self.config = config
        self.running = False
        
        # Subscriptions
        self.subscribed_topics: Set[str] = set()
        
        # Partition assignment
        self.assignment = PartitionAssignment()
        
        # Offset management
        self.offset_manager = OffsetManager(config.group_id)
        
        # Current fetch positions
        self.fetch_positions: Dict[tuple, int] = {}  # (topic, partition) -> next offset to fetch
        
        # Connection
        self.connection: Optional[socket.socket] = None
        self.connection_lock = threading.Lock()
        
        # Metadata
        self.metadata: Dict = {}
        self.metadata_lock = threading.Lock()
        
        # Auto-commit thread
        self.auto_commit_thread: Optional[threading.Thread] = None
        
        # Heartbeat thread
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.last_heartbeat = time.time()
        
        # Paused partitions (for backpressure)
        self.paused_partitions: Set[tuple] = set()
        self.pause_lock = threading.Lock()
    
    def subscribe(self, topics: List[str]):
        """Subscribe to topics."""
        self.subscribed_topics = set(topics)
        
        # Trigger rebalancing
        self._rebalance()
        
        print(f"[Consumer] Subscribed to topics: {topics}")
    
    def _rebalance(self):
        """
        Perform rebalancing to assign partitions.
        
        In a real system, this would coordinate with the consumer group coordinator.
        For simplicity, we assign all partitions to this consumer.
        """
        print(f"[Consumer] Rebalancing for group {self.config.group_id}")
        
        # Get metadata
        self._refresh_metadata()
        
        # Assign partitions (simplified - assign all partitions)
        with self.metadata_lock:
            topics = self.metadata.get('topics', {})
            
            for topic in self.subscribed_topics:
                if topic in topics:
                    num_partitions = topics[topic]['num_partitions']
                    partitions = set(range(num_partitions))
                    self.assignment.assign(topic, partitions)
                    
                    print(f"[Consumer] Assigned partitions for {topic}: {partitions}")
    
    def poll(self, timeout_ms: int = 1000) -> List[Dict]:
        """
        Poll for messages.
        
        Returns a list of message records.
        """
        if not self.running:
            self.start()
        
        messages = []
        start_time = time.time()
        
        # Fetch from all assigned partitions
        for topic, partition_id in self.assignment.all_partitions():
            # Check if paused
            if self._is_paused(topic, partition_id):
                continue
            
            # Get fetch position
            offset = self._get_fetch_position(topic, partition_id)
            
            # Fetch messages
            fetched = self._fetch_messages(topic, partition_id, offset)
            messages.extend(fetched)
            
            # Update fetch position
            if fetched:
                last_offset = fetched[-1]['offset']
                self.fetch_positions[(topic, partition_id)] = last_offset + 1
            
            # Check timeout
            if (time.time() - start_time) * 1000 >= timeout_ms:
                break
            
            # Check max records
            if len(messages) >= self.config.max_poll_records:
                break
        
        # Auto-commit if enabled
        if self.config.enable_auto_commit and messages:
            self._maybe_auto_commit()
        
        return messages
    
    def _fetch_messages(self, topic: str, partition: int, offset: int) -> List[Dict]:
        """Fetch messages from a partition."""
        try:
            request = {
                'api': 'fetch',
                'topic': topic,
                'partition': partition,
                'offset': offset,
                'max_bytes': self.config.max_partition_fetch_bytes
            }
            
            response = self._send_request(request)
            
            if response.get('status') == 'success':
                messages = response.get('messages', [])
                
                # Add topic and partition to each message
                for msg in messages:
                    msg['topic'] = topic
                    msg['partition'] = partition
                
                return messages
            else:
                print(f"[Consumer] Fetch error: {response.get('error')}")
                return []
                
        except Exception as e:
            print(f"[Consumer] Fetch exception: {e}")
            return []
    
    def _get_fetch_position(self, topic: str, partition: int) -> int:
        """Get the next offset to fetch."""
        key = (topic, partition)
        
        # Check if we have a fetch position
        if key in self.fetch_positions:
            return self.fetch_positions[key]
        
        # Check committed offset
        committed = self.offset_manager.get_offset(topic, partition)
        if committed is not None:
            self.fetch_positions[key] = committed + 1
            return committed + 1
        
        # Use reset policy
        if self.config.auto_offset_reset == OffsetResetPolicy.EARLIEST:
            self.fetch_positions[key] = 0
            return 0
        elif self.config.auto_offset_reset == OffsetResetPolicy.LATEST:
            # Would fetch latest offset from broker in real system
            self.fetch_positions[key] = 0
            return 0
        else:
            raise Exception(f"No offset found for {topic}-{partition}")
    
    def commit(self, offsets: Optional[Dict[tuple, int]] = None):
        """
        Manually commit offsets.
        
        Args:
            offsets: Dict of (topic, partition) -> offset. If None, commits current positions.
        """
        if offsets is None:
            # Commit current fetch positions
            offsets = self.fetch_positions.copy()
        
        for (topic, partition), offset in offsets.items():
            self.offset_manager.commit(topic, partition, offset)
            
            # Send commit to broker (simplified)
            try:
                request = {
                    'api': 'offset_commit',
                    'group_id': self.config.group_id,
                    'topic': topic,
                    'partition': partition,
                    'offset': offset
                }
                self._send_request(request)
            except Exception as e:
                print(f"[Consumer] Commit error: {e}")
        
        print(f"[Consumer] Committed offsets: {offsets}")
    
    def _maybe_auto_commit(self):
        """Auto-commit if interval has passed."""
        current_time = time.time()
        
        if not hasattr(self, '_last_commit_time'):
            self._last_commit_time = current_time
        
        time_since_commit = (current_time - self._last_commit_time) * 1000
        
        if time_since_commit >= self.config.auto_commit_interval_ms:
            self.commit()
            self._last_commit_time = current_time
    
    def pause(self, partitions: List[tuple]):
        """Pause consumption from partitions (for backpressure)."""
        with self.pause_lock:
            self.paused_partitions.update(partitions)
        
        print(f"[Consumer] Paused partitions: {partitions}")
    
    def resume(self, partitions: List[tuple]):
        """Resume consumption from partitions."""
        with self.pause_lock:
            for partition in partitions:
                self.paused_partitions.discard(partition)
        
        print(f"[Consumer] Resumed partitions: {partitions}")
    
    def _is_paused(self, topic: str, partition: int) -> bool:
        """Check if a partition is paused."""
        with self.pause_lock:
            return (topic, partition) in self.paused_partitions
    
    def _send_request(self, request: dict) -> dict:
        """Send a request to the broker."""
        conn = self._get_connection()
        
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
    
    def _get_connection(self) -> socket.socket:
        """Get or create connection to broker."""
        with self.connection_lock:
            if self.connection is None:
                broker_addr = self.config.bootstrap_servers[0]
                host, port = broker_addr.split(':')
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connect((host, int(port)))
            
            return self.connection
    
    def _refresh_metadata(self):
        """Refresh metadata from broker."""
        try:
            request = {'api': 'metadata'}
            response = self._send_request(request)
            
            with self.metadata_lock:
                self.metadata = response
            
        except Exception as e:
            print(f"[Consumer] Failed to refresh metadata: {e}")
    
    def start(self):
        """Start the consumer."""
        if self.running:
            return
        
        self.running = True
        
        # Refresh metadata
        self._refresh_metadata()
        
        print(f"[Consumer] Started (group: {self.config.group_id})")
    
    def close(self):
        """Close the consumer."""
        print("[Consumer] Closing")
        self.running = False
        
        # Commit final offsets
        if self.config.enable_auto_commit:
            self.commit()
        
        # Close connection
        with self.connection_lock:
            if self.connection:
                self.connection.close()
        
        print("[Consumer] Closed")


def main():
    """Example usage."""
    config = ConsumerConfig(
        bootstrap_servers=['localhost:9092'],
        group_id='test-group',
        auto_offset_reset=OffsetResetPolicy.EARLIEST,
        enable_auto_commit=True
    )
    
    consumer = Consumer(config)
    consumer.subscribe(['test-topic'])
    
    try:
        # Poll for messages
        for _ in range(10):
            messages = consumer.poll(timeout_ms=1000)
            
            for msg in messages:
                print(f"Received: topic={msg['topic']}, partition={msg['partition']}, "
                      f"offset={msg['offset']}, key={msg['key']}, value={msg['value']}")
            
            time.sleep(1)
    
    finally:
        consumer.close()


if __name__ == '__main__':
    main()
