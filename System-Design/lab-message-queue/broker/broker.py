"""
Main broker server implementation.

The broker handles:
- Client connections (producers and consumers)
- Topic and partition management
- Message routing and storage
- Replication coordination
"""

import socket
import threading
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time

from partition import Partition
from replication import ReplicationCoordinator, ReplicationManager


@dataclass
class BrokerConfig:
    """Broker configuration."""
    broker_id: int
    host: str
    port: int
    data_dir: str
    num_network_threads: int = 3
    num_io_threads: int = 8
    socket_send_buffer_bytes: int = 102400
    socket_receive_buffer_bytes: int = 102400
    max_request_size: int = 104857600  # 100MB
    
    # Replication settings
    replication_factor: int = 3
    min_insync_replicas: int = 2
    replica_lag_time_max_ms: int = 10000
    
    # Log settings
    log_segment_bytes: int = 1073741824  # 1GB
    log_retention_hours: int = 168  # 7 days


class TopicPartitionManager:
    """Manages topics and partitions on a broker."""
    
    def __init__(self, config: BrokerConfig):
        self.config = config
        self.partitions: Dict[Tuple[str, int], Partition] = {}
        self.lock = threading.RLock()
    
    def create_partition(self, topic: str, partition_id: int) -> Partition:
        """Create a new partition."""
        key = (topic, partition_id)
        
        with self.lock:
            if key in self.partitions:
                return self.partitions[key]
            
            partition = Partition(
                topic=topic,
                partition_id=partition_id,
                data_dir=self.config.data_dir,
                segment_size=self.config.log_segment_bytes
            )
            
            self.partitions[key] = partition
            print(f"[Broker] Created partition {topic}-{partition_id}")
            return partition
    
    def get_partition(self, topic: str, partition_id: int) -> Optional[Partition]:
        """Get a partition."""
        return self.partitions.get((topic, partition_id))
    
    def list_partitions(self) -> List[Tuple[str, int]]:
        """List all partitions."""
        return list(self.partitions.keys())
    
    def close_all(self):
        """Close all partitions."""
        for partition in self.partitions.values():
            partition.close()


class Broker:
    """
    Main broker server.
    
    Handles client requests for producing and consuming messages,
    manages partitions, and coordinates replication.
    """
    
    def __init__(self, config: BrokerConfig):
        self.config = config
        self.running = False
        
        # Partition management
        self.partition_manager = TopicPartitionManager(config)
        
        # Replication coordination
        self.replication_coordinator = ReplicationCoordinator(config.broker_id)
        
        # Network
        self.server_socket: Optional[socket.socket] = None
        self.client_threads: List[threading.Thread] = []
        
        # Metadata
        self.cluster_metadata = {
            'brokers': {},  # broker_id -> (host, port)
            'topics': {},   # topic -> {partitions: [...], replication_factor: N}
        }
        self.metadata_lock = threading.Lock()
    
    def start(self):
        """Start the broker server."""
        self.running = True
        
        # Start replication coordinator
        self.replication_coordinator.start()
        
        # Start network server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.config.host, self.config.port))
        self.server_socket.listen(100)
        
        print(f"[Broker] Started broker {self.config.broker_id} on "
              f"{self.config.host}:{self.config.port}")
        
        # Accept client connections
        accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
        accept_thread.start()
    
    def _accept_connections(self):
        """Accept incoming client connections."""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"[Broker] Accepted connection from {address}")
                
                # Handle client in a new thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,),
                    daemon=True
                )
                client_thread.start()
                self.client_threads.append(client_thread)
                
            except Exception as e:
                if self.running:
                    print(f"[Broker] Error accepting connection: {e}")
    
    def _handle_client(self, client_socket: socket.socket):
        """Handle a client connection."""
        try:
            while self.running:
                # Read request
                request_data = self._read_request(client_socket)
                if not request_data:
                    break
                
                # Parse request
                request = json.loads(request_data.decode('utf-8'))
                
                # Route request
                response = self._route_request(request)
                
                # Send response
                self._send_response(client_socket, response)
                
        except Exception as e:
            print(f"[Broker] Error handling client: {e}")
        finally:
            client_socket.close()
    
    def _read_request(self, client_socket: socket.socket) -> Optional[bytes]:
        """Read a request from the client."""
        try:
            # Read length prefix (4 bytes)
            length_bytes = client_socket.recv(4)
            if not length_bytes:
                return None
            
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Read request data
            data = b''
            while len(data) < length:
                chunk = client_socket.recv(min(length - len(data), 4096))
                if not chunk:
                    return None
                data += chunk
            
            return data
            
        except Exception:
            return None
    
    def _send_response(self, client_socket: socket.socket, response: dict):
        """Send a response to the client."""
        response_data = json.dumps(response).encode('utf-8')
        length = len(response_data)
        
        # Send length prefix
        client_socket.sendall(length.to_bytes(4, byteorder='big'))
        
        # Send response data
        client_socket.sendall(response_data)
    
    def _route_request(self, request: dict) -> dict:
        """Route a request to the appropriate handler."""
        api = request.get('api')
        
        if api == 'produce':
            return self._handle_produce(request)
        elif api == 'fetch':
            return self._handle_fetch(request)
        elif api == 'metadata':
            return self._handle_metadata(request)
        elif api == 'create_topic':
            return self._handle_create_topic(request)
        elif api == 'offset_commit':
            return self._handle_offset_commit(request)
        elif api == 'offset_fetch':
            return self._handle_offset_fetch(request)
        else:
            return {'error': f'Unknown API: {api}'}
    
    def _handle_produce(self, request: dict) -> dict:
        """Handle a produce request."""
        topic = request['topic']
        partition_id = request['partition']
        messages = request['messages']
        acks = request.get('acks', '1')
        
        # Get partition
        partition = self.partition_manager.get_partition(topic, partition_id)
        if not partition:
            return {'error': f'Partition {topic}-{partition_id} not found'}
        
        # Check if we can accept writes
        replication_mgr = self.replication_coordinator.get_manager(topic, partition_id)
        if replication_mgr and not replication_mgr.can_accept_write(acks):
            return {'error': 'Not enough in-sync replicas'}
        
        # Append messages
        offsets = []
        try:
            for msg in messages:
                offset = partition.append(
                    key=msg.get('key'),
                    value=msg['value'].encode('utf-8'),
                    headers=msg.get('headers', {})
                )
                offsets.append(offset)
            
            # Update high watermark
            if replication_mgr and replication_mgr.is_leader():
                hw = replication_mgr.compute_high_watermark(partition.get_log_end_offset())
                partition.update_high_watermark(hw)
            
            return {
                'status': 'success',
                'offsets': offsets,
                'partition': partition_id
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _handle_fetch(self, request: dict) -> dict:
        """Handle a fetch request."""
        topic = request['topic']
        partition_id = request['partition']
        offset = request['offset']
        max_bytes = request.get('max_bytes', 1024 * 1024)
        
        # Get partition
        partition = self.partition_manager.get_partition(topic, partition_id)
        if not partition:
            return {'error': f'Partition {topic}-{partition_id} not found'}
        
        # Read messages
        messages = partition.read(offset, max_bytes)
        
        # Convert to dict
        message_dicts = [
            {
                'offset': m.offset,
                'key': m.key,
                'value': m.value.decode('utf-8'),
                'timestamp': m.timestamp,
                'headers': m.headers
            }
            for m in messages
        ]
        
        return {
            'status': 'success',
            'messages': message_dicts,
            'high_watermark': partition.get_high_watermark()
        }
    
    def _handle_metadata(self, request: dict) -> dict:
        """Handle a metadata request."""
        with self.metadata_lock:
            return {
                'status': 'success',
                'broker_id': self.config.broker_id,
                'brokers': self.cluster_metadata['brokers'],
                'topics': self.cluster_metadata['topics']
            }
    
    def _handle_create_topic(self, request: dict) -> dict:
        """Handle a create topic request."""
        topic = request['topic']
        num_partitions = request.get('num_partitions', 1)
        replication_factor = request.get('replication_factor', self.config.replication_factor)
        
        # Create partitions
        for partition_id in range(num_partitions):
            partition = self.partition_manager.create_partition(topic, partition_id)
            
            # Register with replication coordinator
            # In a real system, this would coordinate with other brokers
            replica_ids = [self.config.broker_id]  # Simplified
            self.replication_coordinator.register_partition(
                topic, partition_id, replica_ids, self.config.min_insync_replicas
            )
            
            # Make this broker the leader
            replication_mgr = self.replication_coordinator.get_manager(topic, partition_id)
            if replication_mgr:
                replication_mgr.become_leader(epoch=1)
        
        # Update metadata
        with self.metadata_lock:
            self.cluster_metadata['topics'][topic] = {
                'num_partitions': num_partitions,
                'replication_factor': replication_factor
            }
        
        return {
            'status': 'success',
            'topic': topic,
            'num_partitions': num_partitions
        }
    
    def _handle_offset_commit(self, request: dict) -> dict:
        """Handle an offset commit request (simplified)."""
        # In a real system, this would store offsets in a special topic
        return {'status': 'success'}
    
    def _handle_offset_fetch(self, request: dict) -> dict:
        """Handle an offset fetch request (simplified)."""
        # In a real system, this would retrieve offsets from storage
        return {'status': 'success', 'offsets': {}}
    
    def stop(self):
        """Stop the broker server."""
        print(f"[Broker] Stopping broker {self.config.broker_id}")
        self.running = False
        
        # Stop replication coordinator
        self.replication_coordinator.stop()
        
        # Close all partitions
        self.partition_manager.close_all()
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
        
        print(f"[Broker] Broker {self.config.broker_id} stopped")


def main():
    """Main entry point for running a broker."""
    import sys
    
    broker_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9092
    
    config = BrokerConfig(
        broker_id=broker_id,
        host='localhost',
        port=port,
        data_dir=f'/tmp/broker-{broker_id}'
    )
    
    broker = Broker(config)
    broker.start()
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        broker.stop()


if __name__ == '__main__':
    main()
