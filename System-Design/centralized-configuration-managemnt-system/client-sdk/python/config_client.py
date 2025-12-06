"""
Python client SDK for configuration management service.
Provides caching, auto-refresh, and change notifications.
"""
import asyncio
import hashlib
import json
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timedelta
import httpx
import structlog

logger = structlog.get_logger(__name__)


class ConfigClient:
    """
    Async client for fetching and caching configurations.
    
    Features:
    - Local in-memory caching with TTL
    - Automatic cache refresh
    - Change notifications via polling
    - Fallback to local config file
    - Retry logic with exponential backoff
    
    Example:
        client = ConfigClient(
            base_url="http://localhost:8000/api/v1",
            app_id="my-app",
            environment="production"
        )
        
        await client.initialize()
        
        # Get config value
        db_host = client.get("database.host", default="localhost")
        
        # Register change listener
        client.on_change(lambda configs: print("Configs updated!"))
        
        # Start auto-refresh
        await client.start_auto_refresh(interval=60)
    """
    
    def __init__(
        self,
        base_url: str,
        app_id: str,
        environment: str,
        cache_ttl: int = 60,
        retry_max_attempts: int = 3,
        retry_backoff_factor: int = 2,
        fallback_config_path: Optional[str] = None,
    ):
        """
        Initialize config client.
        
        Args:
            base_url: Base URL of config service
            app_id: Application identifier
            environment: Environment (development, staging, production)
            cache_ttl: Cache TTL in seconds
            retry_max_attempts: Maximum retry attempts
            retry_backoff_factor: Backoff multiplier for retries
            fallback_config_path: Path to fallback config file
        """
        self.base_url = base_url.rstrip("/")
        self.app_id = app_id
        self.environment = environment
        self.cache_ttl = cache_ttl
        self.retry_max_attempts = retry_max_attempts
        self.retry_backoff_factor = retry_backoff_factor
        self.fallback_config_path = fallback_config_path
        
        self._configs: Dict[str, Any] = {}
        self._version: Optional[str] = None
        self._cache_expires_at: Optional[datetime] = None
        self._change_listeners: List[Callable] = []
        self._refresh_task: Optional[asyncio.Task] = None
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self) -> None:
        """Initialize client and fetch initial configs."""
        self._http_client = httpx.AsyncClient(timeout=10.0)
        await self.refresh()
        logger.info("config_client_initialized", app_id=self.app_id, env=self.environment)
    
    async def close(self) -> None:
        """Close client and cleanup resources."""
        if self._refresh_task:
            self._refresh_task.cancel()
        if self._http_client:
            await self._http_client.aclose()
        logger.info("config_client_closed")
    
    async def refresh(self) -> bool:
        """
        Fetch latest configs from service.
        
        Returns:
            True if configs were updated, False otherwise
        """
        for attempt in range(self.retry_max_attempts):
            try:
                response = await self._http_client.post(
                    f"{self.base_url}/configs/fetch",
                    json={
                        "app_id": self.app_id,
                        "environment": self.environment,
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    new_version = data.get("version")
                    
                    # Check if configs changed
                    if new_version != self._version:
                        self._configs = data.get("configs", {})
                        self._version = new_version
                        self._cache_expires_at = datetime.utcnow() + timedelta(
                            seconds=data.get("cache_ttl", self.cache_ttl)
                        )
                        
                        # Notify listeners
                        await self._notify_listeners()
                        
                        logger.info(
                            "configs_refreshed",
                            app_id=self.app_id,
                            version=new_version,
                            count=len(self._configs)
                        )
                        return True
                    
                    return False
                
                elif response.status_code >= 500:
                    # Server error, retry
                    if attempt < self.retry_max_attempts - 1:
                        wait_time = self.retry_backoff_factor ** attempt
                        logger.warning(
                            "config_fetch_retry",
                            attempt=attempt + 1,
                            wait_time=wait_time
                        )
                        await asyncio.sleep(wait_time)
                        continue
                
                logger.error("config_fetch_failed", status=response.status_code)
                return await self._load_fallback()
                
            except Exception as e:
                logger.error("config_fetch_error", error=str(e), attempt=attempt + 1)
                
                if attempt < self.retry_max_attempts - 1:
                    wait_time = self.retry_backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    return await self._load_fallback()
        
        return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        # Check if cache expired
        if self._cache_expires_at and datetime.utcnow() > self._cache_expires_at:
            logger.warning("config_cache_expired", key=key)
        
        return self._configs.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configurations."""
        return self._configs.copy()
    
    def on_change(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback for config changes.
        
        Args:
            callback: Function to call when configs change
        """
        self._change_listeners.append(callback)
    
    async def start_auto_refresh(self, interval: int = 60) -> None:
        """
        Start automatic config refresh.
        
        Args:
            interval: Refresh interval in seconds
        """
        async def refresh_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    await self.refresh()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("auto_refresh_error", error=str(e))
        
        self._refresh_task = asyncio.create_task(refresh_loop())
        logger.info("auto_refresh_started", interval=interval)
    
    async def _notify_listeners(self) -> None:
        """Notify all change listeners."""
        for listener in self._change_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(self._configs)
                else:
                    listener(self._configs)
            except Exception as e:
                logger.error("listener_error", error=str(e))
    
    async def _load_fallback(self) -> bool:
        """Load configuration from fallback file."""
        if not self.fallback_config_path:
            logger.warning("no_fallback_config")
            return False
        
        try:
            with open(self.fallback_config_path, 'r') as f:
                fallback_configs = json.load(f)
                self._configs = fallback_configs
                logger.info("fallback_config_loaded", path=self.fallback_config_path)
                return True
        except Exception as e:
            logger.error("fallback_load_error", error=str(e))
            return False
