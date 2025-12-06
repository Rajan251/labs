"""
Basic usage example for config client SDK.
"""
import asyncio
from config_client import ConfigClient


async def main():
    # Initialize client
    client = ConfigClient(
        base_url="http://localhost:8000/api/v1",
        app_id="my-app",
        environment="development",
        cache_ttl=60,
    )
    
    # Fetch initial configs
    await client.initialize()
    
    # Get configuration values
    db_host = client.get("database.host", default="localhost")
    db_port = client.get("database.port", default=5432)
    feature_enabled = client.get("features.new_ui", default=False)
    
    print(f"Database: {db_host}:{db_port}")
    print(f"New UI Feature: {'Enabled' if feature_enabled else 'Disabled'}")
    
    # Get all configs
    all_configs = client.get_all()
    print(f"\nAll configurations ({len(all_configs)} keys):")
    for key, value in all_configs.items():
        print(f"  {key}: {value}")
    
    # Close client
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
