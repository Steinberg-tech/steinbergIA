import asyncio
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

    async def get_message(self, message_id: str, retries: int = 5, delay: float = 2.0) -> dict:
        """Fetch a message by ID, retrying until the file is ready (isDownloading=False)."""
        url = f"{settings.digisac_base_url}/messages/{message_id}"
        data: dict = {}
        async with httpx.AsyncClient(timeout=15) as client:
            for attempt in range(retries):
                resp = await client.get(url, headers=self._media_headers)
                resp.raise_for_status()
                data = resp.json()
                inner = data.get("data", {}) or {}
                file_download = inner.get("fileDownload", {}) or {}
                if not file_download.get("isDownloading", False):
                    _log.info("digisac_message_fetched", message_id=message_id, attempt=attempt)
                    if settings.debug:
                        import json as _json
                        print(f"\n[DEBUG] full message response:\n{_json.dumps(data, indent=2, ensure_ascii=False)}\n")
                    return data
                _log.info("digisac_file_still_downloading", message_id=message_id, attempt=attempt)
                await asyncio.sleep(delay)
        _log.warning("digisac_file_download_timeout", message_id=message_id)
        return data

    async def download_media(self, file_id: str | None = None, media_url: str | None = None) -> bytes:
        """Download a media file (audio or image) from Digisac.

        Tries multiple URL patterns since Digisac doesn't return the file URL in the message payload.
        """
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            if media_url:
                resp = await client.get(media_url, headers=self._media_headers)
                resp.raise_for_status()
                _log.info("digisac_media_downloaded", source="url", size=len(resp.content))
                return resp.content

            if file_id:
                candidates = [
                    f"{settings.digisac_base_url}/messages/{file_id}/file",
                    f"{settings.digisac_base_url}/messages/{file_id}/download",
                    f"{settings.digisac_base_url}/files/{file_id}/download",
                    f"{settings.digisac_base_url}/files/{file_id}",
                ]
                for url in candidates:
                    try:
                        resp = await client.get(url, headers=self._media_headers)
                        if resp.status_code == 200 and len(resp.content) > 0:
                            _log.info("digisac_media_downloaded", source=url, size=len(resp.content))
                            return resp.content
                        _log.info("digisac_media_candidate_failed", url=url, status=resp.status_code)
                    except Exception as exc:
                        _log.info("digisac_media_candidate_error", url=url, error=str(exc))

                raise ValueError(f"Could not download media for file_id={file_id} — all endpoints returned non-200")

        raise ValueError("download_media requires file_id or media_url")

    async def send_text_mock(self, contact_id: str, text: str) -> dict:
        """Mock send — used when DIGISAC_TOKEN is not set."""
        _log.info("digisac_mock_send", contact_id=contact_id, text=text[:80])
        return {"status": "mock", "contact_id": contact_id}


def get_digisac_client() -> DigisacClient:
    return DigisacClient()
