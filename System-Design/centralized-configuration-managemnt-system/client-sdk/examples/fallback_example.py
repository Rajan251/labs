"""
Example with fallback configuration.
"""
import asyncio
from config_client import ConfigClient


async def main():
    # Initialize client with fallback config
    client = ConfigClient(
        base_url="http://localhost:8000/api/v1",
        app_id="my-app",
        environment="production",
        fallback_config_path="./fallback_config.json",
    )
    
    try:
        await client.initialize()
        print("✅ Connected to config service")
    except Exception as e:
        print(f"⚠️  Failed to connect to config service: {e}")
        print("Using fallback configuration")
    
    # Get configs (will use fallback if service unavailable)
    db_host = client.get("database.host", default="localhost")
    api_key = client.get("api.key", default="default-key")
    
    print(f"\nDatabase Host: {db_host}")
    print(f"API Key: {api_key}")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
