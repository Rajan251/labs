"""
Example with change listener for real-time config updates.
"""
import asyncio
from config_client import ConfigClient


async def on_config_change(configs):
    """Callback when configs change."""
    print("\n🔔 Configuration changed!")
    print(f"Total configs: {len(configs)}")
    for key, value in configs.items():
        print(f"  {key}: {value}")


async def main():
    # Initialize client
    client = ConfigClient(
        base_url="http://localhost:8000/api/v1",
        app_id="my-app",
        environment="development",
    )
    
    await client.initialize()
    
    # Register change listener
    client.on_change(on_config_change)
    
    # Start auto-refresh (checks for changes every 30 seconds)
    await client.start_auto_refresh(interval=30)
    
    print("Listening for config changes... (Press Ctrl+C to stop)")
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
