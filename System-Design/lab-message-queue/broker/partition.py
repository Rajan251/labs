"""
Partition implementation for the distributed message queue.

A partition is an ordered, immutable sequence of messages that is continually
appended to—a commit log. Each message in the partition is assigned a sequential
id number called the offset.
"""

import os
import json
import threading
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import mmap


@dataclass
class Message:
    """Represents a single message in the queue."""
    offset: int
    key: Optional[str]
    value: bytes
    timestamp: int
    headers: Dict[str, str]
    
    def serialize(self) -> bytes:
        """Serialize message to bytes."""
        data = {
            'offset': self.offset,
            'key': self.key,
            'value': self.value.hex(),
            'timestamp': self.timestamp,
            'headers': self.headers
        }
        return json.dumps(data).encode('utf-8') + b'\n'
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'Message':
        """Deserialize message from bytes."""
        obj = json.loads(data.decode('utf-8'))
        return cls(
            offset=obj['offset'],
            key=obj.get('key'),
            value=bytes.fromhex(obj['value']),
            timestamp=obj['timestamp'],
            headers=obj.get('headers', {})
        )


class Segment:
    """
    A segment is a portion of the partition log.
    Each segment has a base offset and contains messages up to a certain size.
    """
    
    def __init__(self, base_offset: int, directory: str, max_size: int = 1024 * 1024 * 100):
        self.base_offset = base_offset
        self.directory = directory
        self.max_size = max_size
        
        # File paths
        self.log_path = os.path.join(directory, f"{base_offset:020d}.log")
        self.index_path = os.path.join(directory, f"{base_offset:020d}.index")
        
        # Open files
        self.log_file = open(self.log_path, 'ab+')
        self.index_file = open(self.index_path, 'ab+')
        
        # Track current size and next offset
        self.log_file.seek(0, os.SEEK_END)
        self.current_size = self.log_file.tell()
        self.next_offset = base_offset
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        # Load index
        self._load_index()
    
    def _load_index(self):
        """Load the index file to find the next offset."""
        self.index_file.seek(0)
        last_entry = None
        while True:
            entry = self.index_file.read(16)  # offset (8 bytes) + position (8 bytes)
            if not entry or len(entry) < 16:
                break
            last_entry = entry
        
        if last_entry:
            import struct
            offset, _ = struct.unpack('QQ', last_entry)
            self.next_offset = offset + 1
    
    def append(self, message: Message) -> bool:
        """
        Append a message to the segment.
        Returns True if successful, False if segment is full.
        """
        with self.lock:
            serialized = message.serialize()
            
            # Check if segment is full
            if self.current_size + len(serialized) > self.max_size:
                return False
            
            # Write to log
            position = self.log_file.tell()
            self.log_file.write(serialized)
            self.log_file.flush()
            os.fsync(self.log_file.fileno())
            
            # Update index (every 10th message for efficiency)
            if message.offset % 10 == 0:
                import struct
                index_entry = struct.pack('QQ', message.offset, position)
                self.index_file.write(index_entry)
                self.index_file.flush()
            
            self.current_size += len(serialized)
            self.next_offset = message.offset + 1
            
            return True
    
    def read(self, offset: int, max_bytes: int = 1024 * 1024) -> List[Message]:
        """
        Read messages starting from the given offset.
        Returns up to max_bytes worth of messages.
        """
        with self.lock:
            # Find position in log using index
            position = self._find_position(offset)
            if position is None:
                return []
            
            # Read from log
            self.log_file.seek(position)
            messages = []
            bytes_read = 0
            
            while bytes_read < max_bytes:
                line = self.log_file.readline()
                if not line:
                    break
                
                try:
                    message = Message.deserialize(line)
                    if message.offset >= offset:
                        messages.append(message)
                        bytes_read += len(line)
                except Exception:
                    break
            
            return messages
    
    def _find_position(self, offset: int) -> Optional[int]:
        """Find the file position for the given offset using the index."""
        if offset < self.base_offset:
            return None
        
        # Binary search in index
        self.index_file.seek(0, os.SEEK_END)
        index_size = self.index_file.tell()
        num_entries = index_size // 16
        
        if num_entries == 0:
            return 0
        
        import struct
        left, right = 0, num_entries - 1
        best_position = 0
        
        while left <= right:
            mid = (left + right) // 2
            self.index_file.seek(mid * 16)
            entry = self.index_file.read(16)
            entry_offset, position = struct.unpack('QQ', entry)
            
            if entry_offset <= offset:
                best_position = position
                left = mid + 1
            else:
                right = mid - 1
        
        return best_position
    
    def close(self):
        """Close the segment files."""
        self.log_file.close()
        self.index_file.close()
    
    def is_full(self) -> bool:
        """Check if the segment is full."""
        return self.current_size >= self.max_size


class Partition:
    """
    A partition is an ordered, immutable sequence of messages.
    It consists of multiple segments for efficient management.
    """
    
    def __init__(self, topic: str, partition_id: int, data_dir: str, 
                 segment_size: int = 1024 * 1024 * 100):
        self.topic = topic
        self.partition_id = partition_id
        self.segment_size = segment_size
        
        # Create partition directory
        self.directory = os.path.join(data_dir, f"{topic}-{partition_id}")
        os.makedirs(self.directory, exist_ok=True)
        
        # Segments (ordered by base offset)
        self.segments: List[Segment] = []
        self.lock = threading.RLock()
        
        # Replication state
        self.high_watermark = 0  # Last offset replicated to all ISR
        self.log_end_offset = 0  # Last offset in the log
        
        # Load existing segments
        self._load_segments()
        
        # Create initial segment if none exist
        if not self.segments:
            self.segments.append(Segment(0, self.directory, self.segment_size))
    
    def _load_segments(self):
        """Load existing segments from disk."""
        log_files = sorted([f for f in os.listdir(self.directory) if f.endswith('.log')])
        
        for log_file in log_files:
            base_offset = int(log_file.split('.')[0])
            segment = Segment(base_offset, self.directory, self.segment_size)
            self.segments.append(segment)
            self.log_end_offset = max(self.log_end_offset, segment.next_offset - 1)
    
    def append(self, key: Optional[str], value: bytes, 
               headers: Optional[Dict[str, str]] = None) -> int:
        """
        Append a message to the partition.
        Returns the offset of the appended message.
        """
        with self.lock:
            # Get current offset
            offset = self.log_end_offset + 1
            
            # Create message
            message = Message(
                offset=offset,
                key=key,
                value=value,
                timestamp=int(datetime.now().timestamp() * 1000),
                headers=headers or {}
            )
            
            # Get active segment
            active_segment = self.segments[-1]
            
            # Create new segment if current is full
            if active_segment.is_full():
                new_segment = Segment(offset, self.directory, self.segment_size)
                self.segments.append(new_segment)
                active_segment = new_segment
            
            # Append to segment
            if active_segment.append(message):
                self.log_end_offset = offset
                return offset
            else:
                raise Exception("Failed to append message")
    
    def read(self, offset: int, max_bytes: int = 1024 * 1024) -> List[Message]:
        """
        Read messages starting from the given offset.
        Only returns messages up to the high watermark (committed messages).
        """
        with self.lock:
            # Find the segment containing the offset
            segment = self._find_segment(offset)
            if not segment:
                return []
            
            # Read from segment
            messages = segment.read(offset, max_bytes)
            
            # Filter messages beyond high watermark
            return [m for m in messages if m.offset <= self.high_watermark]
    
    def _find_segment(self, offset: int) -> Optional[Segment]:
        """Find the segment containing the given offset."""
        for segment in reversed(self.segments):
            if segment.base_offset <= offset:
                return segment
        return None
    
    def update_high_watermark(self, offset: int):
        """Update the high watermark (used by replication)."""
        with self.lock:
            self.high_watermark = min(offset, self.log_end_offset)
    
    def get_log_end_offset(self) -> int:
        """Get the log end offset."""
        return self.log_end_offset
    
    def get_high_watermark(self) -> int:
        """Get the high watermark."""
        return self.high_watermark
    
    def close(self):
        """Close all segments."""
        for segment in self.segments:
            segment.close()
    
    def __repr__(self):
        return f"Partition(topic={self.topic}, id={self.partition_id}, " \
               f"LEO={self.log_end_offset}, HW={self.high_watermark})"
