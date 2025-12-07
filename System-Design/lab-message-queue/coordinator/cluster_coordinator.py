"""Cluster coordinator for managing broker metadata and leader election."""

import threading
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class BrokerState(Enum):
    """Broker health states."""
    ONLINE = "online"
    OFFLINE = "offline"
    SUSPECTED = "suspected"


@dataclass
class BrokerMetadata:
    """Metadata about a broker."""
    broker_id: int
    host: str
    port: int
    state: BrokerState
    last_heartbeat: float
    rack: Optional[str] = None


@dataclass
class PartitionMetadata:
    """Metadata about a partition."""
    topic: str
    partition_id: int
    leader: int
    replicas: List[int]
    isr: List[int]  # In-sync replicas
    epoch: int


class ClusterCoordinator:
    """
    Manages cluster-wide metadata and coordination.
    
    Responsibilities:
    - Broker discovery and health monitoring
    - Topic and partition metadata
    - Leader election for partitions
    - Cluster state management
    """
    
    def __init__(self, coordinator_id: int):
        self.coordinator_id = coordinator_id
        self.is_leader = False
        self.leader_epoch = 0
        
        # Broker registry
        self.brokers: Dict[int, BrokerMetadata] = {}
        self.broker_lock = threading.RLock()
        
        # Partition metadata
        self.partitions: Dict[tuple, PartitionMetadata] = {}  # (topic, partition_id) -> metadata
        self.partition_lock = threading.RLock()
        
        # Health monitoring
        self.health_check_interval = 5  # seconds
        self.heartbeat_timeout = 15  # seconds
        self.health_thread: Optional[threading.Thread] = None
        
        self.running = False
    
    def start(self):
        """Start the cluster coordinator."""
        self.running = True
        
        # Start health monitoring
        self.health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_thread.start()
        
        print(f"[Coordinator] Started coordinator {self.coordinator_id}")
    
    def stop(self):
        """Stop the cluster coordinator."""
        self.running = False
        
        if self.health_thread:
            self.health_thread.join(timeout=10)
        
        print(f"[Coordinator] Stopped coordinator {self.coordinator_id}")
    
    def register_broker(self, broker_id: int, host: str, port: int, rack: Optional[str] = None):
        """Register a broker with the coordinator."""
        with self.broker_lock:
            self.brokers[broker_id] = BrokerMetadata(
                broker_id=broker_id,
                host=host,
                port=port,
                state=BrokerState.ONLINE,
                last_heartbeat=time.time(),
                rack=rack
            )
        
        print(f"[Coordinator] Registered broker {broker_id} at {host}:{port}")
    
    def update_broker_heartbeat(self, broker_id: int):
        """Update the last heartbeat time for a broker."""
        with self.broker_lock:
            if broker_id in self.brokers:
                self.brokers[broker_id].last_heartbeat = time.time()
                
                # Mark as online if it was suspected
                if self.brokers[broker_id].state == BrokerState.SUSPECTED:
                    self.brokers[broker_id].state = BrokerState.ONLINE
                    print(f"[Coordinator] Broker {broker_id} recovered")
    
    def _health_check_loop(self):
        """Periodically check broker health."""
        while self.running:
            time.sleep(self.health_check_interval)
            self._check_broker_health()
    
    def _check_broker_health(self):
        """Check health of all brokers."""
        current_time = time.time()
        
        with self.broker_lock:
            for broker_id, broker in self.brokers.items():
                time_since_heartbeat = current_time - broker.last_heartbeat
                
                if time_since_heartbeat > self.heartbeat_timeout:
                    if broker.state == BrokerState.ONLINE:
                        broker.state = BrokerState.SUSPECTED
                        print(f"[Coordinator] Broker {broker_id} suspected (no heartbeat for {time_since_heartbeat:.1f}s)")
                    
                    elif broker.state == BrokerState.SUSPECTED:
                        broker.state = BrokerState.OFFLINE
                        print(f"[Coordinator] Broker {broker_id} marked offline")
                        
                        # Trigger leader election for affected partitions
                        self._handle_broker_failure(broker_id)
    
    def _handle_broker_failure(self, failed_broker_id: int):
        """Handle broker failure by triggering leader elections."""
        with self.partition_lock:
            for (topic, partition_id), metadata in self.partitions.items():
                # If failed broker was leader, elect new leader
                if metadata.leader == failed_broker_id:
                    self._elect_partition_leader(topic, partition_id)
                
                # Remove from ISR
                if failed_broker_id in metadata.isr:
                    metadata.isr.remove(failed_broker_id)
                    print(f"[Coordinator] Removed broker {failed_broker_id} from ISR of {topic}-{partition_id}")
    
    def create_topic(self, topic: str, num_partitions: int, replication_factor: int):
        """Create a new topic with partitions."""
        with self.broker_lock, self.partition_lock:
            # Get available brokers
            available_brokers = [
                broker_id for broker_id, broker in self.brokers.items()
                if broker.state == BrokerState.ONLINE
            ]
            
            if len(available_brokers) < replication_factor:
                raise Exception(f"Not enough brokers for replication factor {replication_factor}")
            
            # Create partitions
            for partition_id in range(num_partitions):
                # Assign replicas (round-robin)
                replicas = []
                for i in range(replication_factor):
                    broker_idx = (partition_id + i) % len(available_brokers)
                    replicas.append(available_brokers[broker_idx])
                
                # Leader is first replica
                leader = replicas[0]
                
                # Create partition metadata
                metadata = PartitionMetadata(
                    topic=topic,
                    partition_id=partition_id,
                    leader=leader,
                    replicas=replicas,
                    isr=replicas.copy(),
                    epoch=1
                )
                
                self.partitions[(topic, partition_id)] = metadata
                
                print(f"[Coordinator] Created partition {topic}-{partition_id}: "
                      f"leader={leader}, replicas={replicas}")
    
    def _elect_partition_leader(self, topic: str, partition_id: int):
        """Elect a new leader for a partition."""
        with self.partition_lock:
            key = (topic, partition_id)
            if key not in self.partitions:
                return
            
            metadata = self.partitions[key]
            
            # Try to elect from ISR
            available_isr = [
                broker_id for broker_id in metadata.isr
                if self.brokers.get(broker_id, BrokerMetadata(0, '', 0, BrokerState.OFFLINE, 0)).state == BrokerState.ONLINE
            ]
            
            if available_isr:
                # Elect first available ISR member
                new_leader = available_isr[0]
                old_leader = metadata.leader
                metadata.leader = new_leader
                metadata.epoch += 1
                
                print(f"[Coordinator] Elected new leader for {topic}-{partition_id}: "
                      f"{old_leader} -> {new_leader} (epoch {metadata.epoch})")
            else:
                print(f"[Coordinator] WARNING: No available ISR members for {topic}-{partition_id}")
    
    def get_partition_metadata(self, topic: str, partition_id: int) -> Optional[PartitionMetadata]:
        """Get metadata for a partition."""
        with self.partition_lock:
            return self.partitions.get((topic, partition_id))
    
    def get_topic_metadata(self, topic: str) -> List[PartitionMetadata]:
        """Get metadata for all partitions of a topic."""
        with self.partition_lock:
            return [
                metadata for (t, _), metadata in self.partitions.items()
                if t == topic
            ]
    
    def get_all_brokers(self) -> List[BrokerMetadata]:
        """Get all registered brokers."""
        with self.broker_lock:
            return list(self.brokers.values())
    
    def get_online_brokers(self) -> List[BrokerMetadata]:
        """Get all online brokers."""
        with self.broker_lock:
            return [
                broker for broker in self.brokers.values()
                if broker.state == BrokerState.ONLINE
            ]
    
    def update_partition_isr(self, topic: str, partition_id: int, isr: List[int]):
        """Update the ISR for a partition."""
        with self.partition_lock:
            key = (topic, partition_id)
            if key in self.partitions:
                old_isr = self.partitions[key].isr
                self.partitions[key].isr = isr
                
                print(f"[Coordinator] Updated ISR for {topic}-{partition_id}: {old_isr} -> {isr}")
    
    def __repr__(self):
        return f"ClusterCoordinator(id={self.coordinator_id}, " \
               f"brokers={len(self.brokers)}, partitions={len(self.partitions)})"


def main():
    """Example usage."""
    coordinator = ClusterCoordinator(coordinator_id=1)
    coordinator.start()
    
    try:
        # Register brokers
        coordinator.register_broker(1, 'localhost', 9092)
        coordinator.register_broker(2, 'localhost', 9093)
        coordinator.register_broker(3, 'localhost', 9094)
        
        # Create topic
        coordinator.create_topic('test-topic', num_partitions=6, replication_factor=3)
        
        # Print metadata
        print("\nTopic metadata:")
        for metadata in coordinator.get_topic_metadata('test-topic'):
            print(f"  Partition {metadata.partition_id}: leader={metadata.leader}, "
                  f"replicas={metadata.replicas}, ISR={metadata.isr}")
        
        # Keep running
        time.sleep(30)
        
    finally:
        coordinator.stop()


if __name__ == '__main__':
    main()
