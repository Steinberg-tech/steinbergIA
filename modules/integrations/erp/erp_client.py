from config.settings import settings
from modules.integrations.base_client import BaseClient
from observability.logger import get_logger

_log = get_logger("erp_client")


class ERPClient(BaseClient):
    """
    Client for ERP integration (SAP, TOTVS, etc.).
    Falls back to mock data when ERP_BASE_URL is not configured.
    """

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.erp_base_url or "http://erp-mock",
            api_key=settings.erp_api_key,
            timeout=settings.erp_timeout_seconds,
        )
        self._mock_mode = not bool(settings.erp_base_url)

    async def get_order_status(self, order_id: str) -> dict:
        if self._mock_mode:
            return _mock_order(order_id)
        data = await self._get(f"/orders/{order_id}/status")
        _log.info("erp_order_fetched", order_id=order_id)
        return data

    async def get_customer_orders(self, customer_id: str) -> list[dict]:
        if self._mock_mode:
            return [_mock_order(f"PED-{customer_id[:6]}")]
        return await self._get(f"/customers/{customer_id}/orders")


def _mock_order(order_id: str) -> dict:
    return {
        "order_id": order_id,
        "status": "Em separação",
        "estimated_delivery": "2026-05-20",
        "carrier": "Transportadora XYZ",
        "tracking_code": f"BR{order_id[:8].upper()}00",
        "items": [{"sku": "PROD-001", "qty": 1, "description": "Produto exemplo"}],
    }
