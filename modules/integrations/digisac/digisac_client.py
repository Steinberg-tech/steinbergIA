import httpx

from config.settings import settings
from observability.logger import get_logger

_log = get_logger("digisac_client")

# --- Digisac REST field reference (v1) ---
# POST /messages  → send a message to a contact
# Required headers: Authorization: Bearer <token>
# Body fields verified against Digisac docs — adjust if their API version changes.
_SEND_URL = f"{settings.digisac_base_url}/messages"


class DigisacClient:
    """Thin async client for the Digisac API."""

    def __init__(self) -> None:
        self._headers = {
            "Authorization": f"Bearer {settings.digisac_token}",
            "Content-Type": "application/json",
        }

    async def send_text(self, contact_id: str, text: str) -> dict:
        """Send a plain-text message to a contact."""
        payload: dict = {
            "type": "chat",
            "contactId": contact_id,
            "text": text,
        }
        if settings.digisac_service_id:
            payload["serviceId"] = settings.digisac_service_id
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(_SEND_URL, json=payload, headers=self._headers)
            resp.raise_for_status()
            _log.info("digisac_message_sent", contact_id=contact_id, status=resp.status_code)
            return resp.json()

    async def send_text_mock(self, contact_id: str, text: str) -> dict:
        """Mock send — used when DIGISAC_TOKEN is not set."""
        _log.info("digisac_mock_send", contact_id=contact_id, text=text[:80])
        return {"status": "mock", "contact_id": contact_id}


def get_digisac_client() -> DigisacClient:
    return DigisacClient()
