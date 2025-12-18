from ...application.services import OrderService
from .....shared.kernel.observability.logging import logger

class OrderEventsConsumer:
    """
    Consumes events from other services (e.g. PaymentProcessed, InventoryReserved)
    to advance the Saga state.
    """
    def __init__(self, order_service: OrderService):
        self.order_service = order_service

    async def handle_payment_processed(self, payload: dict):
        order_id = payload.get("order_id")
        logger.info(f"Received PaymentProcessed for Order {order_id}")
        # await self.order_service.confirm_payment(order_id)
        
    async def handle_inventory_reserved(self, payload: dict):
        order_id = payload.get("order_id")
        logger.info(f"Received InventoryReserved for Order {order_id}")
        # await self.order_service.mark_ready_for_shipment(order_id)
