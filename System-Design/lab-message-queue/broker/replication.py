"""
Replication manager for handling leader-follower replication.

Implements:
- Leader-follower replication protocol
- In-Sync Replica (ISR) management
- Failover and leader election
- High watermark propagation
"""

import threading
import time
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from enum import Enum


class ReplicaRole(Enum):
    LEADER = "leader"
    FOLLOWER = "follower"


@dataclass
class ReplicaState:
    """State of a replica."""
    broker_id: int
    role: ReplicaRole
    log_end_offset: int
    last_fetch_time: float
    is_in_sync: bool


class ReplicationManager:
    """
    Manages replication for a partition.
    
    The leader maintains state about all replicas and determines which
    replicas are in-sync (ISR). Followers fetch data from the leader.
    """
    
    def __init__(self, topic: str, partition_id: int, broker_id: int,
                 replica_ids: List[int], min_isr: int = 2,
                 replica_lag_time_max_ms: int = 10000):
        self.topic = topic
        self.partition_id = partition_id
        self.broker_id = broker_id
        self.replica_ids = replica_ids
        self.min_isr = min_isr
        self.replica_lag_time_max_ms = replica_lag_time_max_ms
        
        # Current role
        self.role = ReplicaRole.FOLLOWER
        self.leader_id: Optional[int] = None
        self.epoch = 0  # Leader epoch for fencing
        
        # Replica state (only maintained by leader)
        self.replica_states: Dict[int, ReplicaState] = {}
        self.in_sync_replicas: Set[int] = set()
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Initialize replica states
        for replica_id in replica_ids:
            self.replica_states[replica_id] = ReplicaState(
                broker_id=replica_id,
                role=ReplicaRole.FOLLOWER,
                log_end_offset=0,
                last_fetch_time=time.time(),
                is_in_sync=False
            )
    
    def become_leader(self, epoch: int):
        """Transition to leader role."""
        with self.lock:
            self.role = ReplicaRole.LEADER
            self.leader_id = self.broker_id
            self.epoch = epoch
            
            # Mark self as in-sync
            self.in_sync_replicas = {self.broker_id}
            
            print(f"[Replication] Broker {self.broker_id} became leader for "
                  f"{self.topic}-{self.partition_id} (epoch {epoch})")
    
    def become_follower(self, leader_id: int, epoch: int):
        """Transition to follower role."""
        with self.lock:
            self.role = ReplicaRole.FOLLOWER
            self.leader_id = leader_id
            self.epoch = epoch
            
            print(f"[Replication] Broker {self.broker_id} became follower for "
                  f"{self.topic}-{self.partition_id} (leader: {leader_id}, epoch {epoch})")
    
    def update_replica_state(self, replica_id: int, log_end_offset: int):
        """
        Update the state of a replica (called by leader when follower fetches).
        """
        if self.role != ReplicaRole.LEADER:
            return
        
        with self.lock:
            if replica_id not in self.replica_states:
                return
            
            state = self.replica_states[replica_id]
            state.log_end_offset = log_end_offset
            state.last_fetch_time = time.time()
            
            # Update ISR membership
            self._update_isr()
    
    def _update_isr(self):
        """Update the in-sync replica set based on replica lag."""
        if self.role != ReplicaRole.LEADER:
            return
        
        current_time = time.time()
        new_isr = {self.broker_id}  # Leader is always in ISR
        
        for replica_id, state in self.replica_states.items():
            if replica_id == self.broker_id:
                continue
            
            # Check if replica is caught up
            time_since_fetch = (current_time - state.last_fetch_time) * 1000
            
            if time_since_fetch <= self.replica_lag_time_max_ms:
                new_isr.add(replica_id)
                state.is_in_sync = True
            else:
                state.is_in_sync = False
        
        # Update ISR if changed
        if new_isr != self.in_sync_replicas:
            old_isr = self.in_sync_replicas.copy()
            self.in_sync_replicas = new_isr
            
            print(f"[Replication] ISR updated for {self.topic}-{self.partition_id}: "
                  f"{old_isr} -> {new_isr}")
            
            # Check if we have enough ISR members
            if len(self.in_sync_replicas) < self.min_isr:
                print(f"[Replication] WARNING: ISR size ({len(self.in_sync_replicas)}) "
                      f"below min.insync.replicas ({self.min_isr})")
    
    def compute_high_watermark(self, leader_leo: int) -> int:
        """
        Compute the high watermark as the minimum LEO of all ISR members.
        Only committed messages (up to HW) are visible to consumers.
        """
        if self.role != ReplicaRole.LEADER:
            return 0
        
        with self.lock:
            if not self.in_sync_replicas:
                return 0
            
            # Get LEO of all ISR members
            isr_leos = [leader_leo]  # Leader's LEO
            
            for replica_id in self.in_sync_replicas:
                if replica_id == self.broker_id:
                    continue
                if replica_id in self.replica_states:
                    isr_leos.append(self.replica_states[replica_id].log_end_offset)
            
            # High watermark is the minimum LEO of all ISR members
            return min(isr_leos) if isr_leos else 0
    
    def can_accept_write(self, ack_mode: str) -> bool:
        """
        Check if the partition can accept writes based on acknowledgment mode.
        
        ack_mode:
            - '0': No acknowledgment required
            - '1': Leader acknowledgment only
            - 'all': All ISR members must acknowledge
        """
        if self.role != ReplicaRole.LEADER:
            return False
        
        if ack_mode == '0':
            return True
        elif ack_mode == '1':
            return True
        elif ack_mode == 'all':
            with self.lock:
                return len(self.in_sync_replicas) >= self.min_isr
        
        return False
    
    def get_isr(self) -> Set[int]:
        """Get the current in-sync replica set."""
        with self.lock:
            return self.in_sync_replicas.copy()
    
    def is_leader(self) -> bool:
        """Check if this broker is the leader."""
        return self.role == ReplicaRole.LEADER
    
    def get_leader_id(self) -> Optional[int]:
        """Get the current leader ID."""
        return self.leader_id
    
    def get_epoch(self) -> int:
        """Get the current leader epoch."""
        return self.epoch
    
    def validate_epoch(self, epoch: int) -> bool:
        """Validate that the request epoch matches current epoch (fencing)."""
        return epoch == self.epoch


class ReplicationCoordinator:
    """
    Coordinates replication across all partitions on a broker.
    Manages follower fetch threads and leader state updates.
    """
    
    def __init__(self, broker_id: int):
        self.broker_id = broker_id
        self.replication_managers: Dict[str, ReplicationManager] = {}
        self.lock = threading.Lock()
        
        # Follower fetch threads
        self.fetch_threads: Dict[str, threading.Thread] = {}
        self.running = False
    
    def register_partition(self, topic: str, partition_id: int,
                          replica_ids: List[int], min_isr: int = 2):
        """Register a partition for replication management."""
        key = f"{topic}-{partition_id}"
        
        with self.lock:
            if key not in self.replication_managers:
                manager = ReplicationManager(
                    topic, partition_id, self.broker_id,
                    replica_ids, min_isr
                )
                self.replication_managers[key] = manager
    
    def get_manager(self, topic: str, partition_id: int) -> Optional[ReplicationManager]:
        """Get the replication manager for a partition."""
        key = f"{topic}-{partition_id}"
        return self.replication_managers.get(key)
    
    def start(self):
        """Start the replication coordinator."""
        self.running = True
        print(f"[Replication] Coordinator started for broker {self.broker_id}")
    
    def stop(self):
        """Stop the replication coordinator."""
        self.running = False
        
        # Stop all fetch threads
        for thread in self.fetch_threads.values():
            thread.join(timeout=5)
        
        print(f"[Replication] Coordinator stopped for broker {self.broker_id}")
    
    def __repr__(self):
        return f"ReplicationCoordinator(broker_id={self.broker_id}, " \
               f"partitions={len(self.replication_managers)})"
