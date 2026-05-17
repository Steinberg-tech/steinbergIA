import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from observability.logger import get_logger
from shared.exceptions import IntegrationError

_log = get_logger("base_client")


class BaseClient:
    """HTTP base client with retry, timeout, and structured logging."""

    def __init__(self, base_url: str, api_key: str = "", timeout: int = 10) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self._base_url}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(url, params=params, headers=self._headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                _log.error("http_error", url=url, status=exc.response.status_code)
                raise IntegrationError(f"HTTP {exc.response.status_code} from {url}") from exc
            except httpx.RequestError as exc:
                _log.error("request_error", url=url, error=str(exc))
                raise IntegrationError(f"Request failed: {exc}") from exc

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def _post(self, path: str, payload: dict) -> dict:
        url = f"{self._base_url}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=self._headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                raise IntegrationError(f"HTTP {exc.response.status_code} from {url}") from exc
            except httpx.RequestError as exc:
                raise IntegrationError(f"Request failed: {exc}") from exc
