"""Simple consumer example demonstrating basic message consumption."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.consumer import Consumer, ConsumerConfig, OffsetResetPolicy
import time


def main():
    """Run a simple consumer example."""
    print("=== Simple Consumer Example ===\n")
    
    # Configure consumer
    config = ConsumerConfig(
        bootstrap_servers=['localhost:9092'],
        group_id='example-consumer-group',
        auto_offset_reset=OffsetResetPolicy.EARLIEST,
        enable_auto_commit=True,
        auto_commit_interval_ms=5000
    )
    
    # Create consumer
    consumer = Consumer(config)
    consumer.subscribe(['events'])
    
    print("Subscribed to 'events' topic")
    print("Polling for messages (Ctrl+C to stop)...\n")
    
    try:
        message_count = 0
        
        while True:
            # Poll for messages
            messages = consumer.poll(timeout_ms=1000)
            
            if messages:
                for msg in messages:
                    message_count += 1
                    print(f"[{message_count}] Received message:")
                    print(f"    Topic: {msg['topic']}")
                    print(f"    Partition: {msg['partition']}")
                    print(f"    Offset: {msg['offset']}")
                    print(f"    Key: {msg['key']}")
                    print(f"    Value: {msg['value']}")
                    print(f"    Timestamp: {msg['timestamp']}")
                    print()
            else:
                print(".", end="", flush=True)
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print(f"\n\n✓ Consumed {message_count} messages")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    finally:
        consumer.close()
        print("Consumer closed.")


if __name__ == '__main__':
    main()
