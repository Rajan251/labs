"""
RabbitMQ client for publishing configuration change notifications.
Provides connection management and message publishing.
"""
from typing import Optional, Dict, Any
import json
from aio_pika import connect_robust, Message, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel, AbstractRobustExchange
import structlog

from .config import settings

logger = structlog.get_logger(__name__)


class RabbitMQClient:
    """Async RabbitMQ client for publishing config change events."""
    
    def __init__(self):
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.exchange: Optional[AbstractRobustExchange] = None
    
    async def connect(self) -> None:
        """Initialize RabbitMQ connection and channel."""
        try:
            self.connection = await connect_robust(settings.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Declare exchange for config changes
            self.exchange = await self.channel.declare_exchange(
                settings.rabbitmq_exchange,
                ExchangeType.TOPIC,
                durable=True,
            )
            
            logger.info("rabbitmq_connected", url=settings.rabbitmq_url)
        except Exception as e:
            logger.error("rabbitmq_connection_error", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Close RabbitMQ connections."""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("rabbitmq_disconnected")
    
    async def publish_config_change(
        self,
        app_id: str,
        environment: str,
        config_key: str,
        change_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish configuration change notification.
        
        Args:
            app_id: Application identifier
            environment: Environment (dev/staging/prod)
            config_key: Configuration key that changed
            change_type: Type of change (created/updated/deleted/rollback)
            metadata: Additional metadata about the change
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.exchange:
            logger.warning("rabbitmq_not_connected")
            return False
        
        try:
            message_body = {
                "app_id": app_id,
                "environment": environment,
                "config_key": config_key,
                "change_type": change_type,
                "metadata": metadata or {},
            }
            
            # Routing key format: config.{app_id}.{environment}.{change_type}
            routing_key = f"config.{app_id}.{environment}.{change_type}"
            
            message = Message(
                body=json.dumps(message_body).encode(),
                content_type="application/json",
                delivery_mode=2,  # Persistent
            )
            
            await self.exchange.publish(
                message,
                routing_key=routing_key,
            )
            
            logger.info(
                "config_change_published",
                app_id=app_id,
                environment=environment,
                config_key=config_key,
                change_type=change_type,
            )
            return True
            
        except Exception as e:
            logger.error("rabbitmq_publish_error", error=str(e))
            return False


# Global RabbitMQ client instance
rabbitmq_client = RabbitMQClient()
