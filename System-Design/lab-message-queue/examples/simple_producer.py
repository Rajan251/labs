"""Simple producer example demonstrating basic message publishing."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.producer import Producer, ProducerConfig, AckMode
import time


def main():
    """Run a simple producer example."""
    print("=== Simple Producer Example ===\n")
    
    # Configure producer
    config = ProducerConfig(
        bootstrap_servers=['localhost:9092'],
        acks=AckMode.LEADER,
        batch_size=1024,
        linger_ms=100
    )
    
    # Create producer
    producer = Producer(config)
    producer.start()
    
    try:
        print("Sending 20 messages to 'events' topic...\n")
        
        # Send messages
        for i in range(20):
            key = f"user-{i % 5}"  # 5 different users
            value = f"Event {i}: User {i % 5} performed action"
            
            producer.send(
                topic='events',
                key=key,
                value=value,
                headers={'source': 'example', 'version': '1.0'}
            )
            
            print(f"Sent message {i}: key={key}, value={value}")
            time.sleep(0.2)
        
        # Flush to ensure all messages are sent
        print("\nFlushing pending messages...")
        producer.flush()
        
        print("\n✓ All messages sent successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    finally:
        producer.close()
        print("\nProducer closed.")


if __name__ == '__main__':
    main()
