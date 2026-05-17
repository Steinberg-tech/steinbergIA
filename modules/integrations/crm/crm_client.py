from config.settings import settings
from modules.integrations.base_client import BaseClient
from observability.logger import get_logger

_log = get_logger("crm_client")


class CRMClient(BaseClient):
    """
    Client for CRM integration. Returns customer profile and preferences.
    Falls back to mock data when CRM_BASE_URL is not configured.
    """

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.crm_base_url or "http://crm-mock",
            api_key=settings.crm_api_key,
            timeout=settings.crm_timeout_seconds,
        )
        self._mock_mode = not bool(settings.crm_base_url)

    async def get_customer(self, phone: str) -> dict:
        if self._mock_mode:
            return _mock_customer(phone)
        data = await self._get(f"/customers", params={"phone": phone})
        return data

    async def update_customer(self, phone: str, **fields) -> dict:
        if self._mock_mode:
            return {"updated": True, **fields}
        return await self._post("/customers/update", {"phone": phone, **fields})


def _mock_customer(phone: str) -> dict:
    return {
        "phone": phone,
        "name": "Cliente Demo",
        "email": "cliente@exemplo.com.br",
        "segment": "standard",
        "total_orders": 3,
    }
