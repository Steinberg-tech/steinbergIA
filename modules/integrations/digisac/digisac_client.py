import httpx

from config.settings import settings
from observability.logger import get_logger

_log = get_logger("digisac_client")

_SEND_URL = f"{settings.digisac_base_url}/messages"
_FILES_URL = f"{settings.digisac_base_url}/files"


class DigisacClient:
    """Thin async client for the Digisac API."""

    def __init__(self) -> None:
        self._headers = {
            "Authorization": f"Bearer {settings.digisac_token}",
            "Content-Type": "application/json",
        }
        self._media_headers = {
            "Authorization": f"Bearer {settings.digisac_token}",
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

    async def download_media(self, file_id: str | None = None, media_url: str | None = None) -> bytes:
        """Download a media file (audio or image) from Digisac.

        Tries direct URL first; falls back to GET /files/{file_id}.
        """
        async with httpx.AsyncClient(timeout=30) as client:
            if media_url:
                resp = await client.get(media_url, headers=self._media_headers)
                resp.raise_for_status()
                _log.info("digisac_media_downloaded", source="url", size=len(resp.content))
                return resp.content

            if file_id:
                resp = await client.get(f"{_FILES_URL}/{file_id}", headers=self._media_headers)
                resp.raise_for_status()
                _log.info("digisac_media_downloaded", source="file_id", size=len(resp.content))
                return resp.content

        raise ValueError("download_media requires file_id or media_url")

    async def send_text_mock(self, contact_id: str, text: str) -> dict:
        """Mock send — used when DIGISAC_TOKEN is not set."""
        _log.info("digisac_mock_send", contact_id=contact_id, text=text[:80])
        return {"status": "mock", "contact_id": contact_id}


def get_digisac_client() -> DigisacClient:
    return DigisacClient()
