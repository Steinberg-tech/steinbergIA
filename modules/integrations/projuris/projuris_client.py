import httpx

from modules.integrations.base_client import BaseClient
from modules.integrations.projuris.phone import phone_candidates
from observability.logger import get_logger
from shared.exceptions import IntegrationError
from shared.interfaces import CacheBackend

_log = get_logger("projuris_client")

_AUTH_PATH = "/auth/token"
_PROCESS_CONSULTA_PATH = "/adv-service/processo/consulta"
_PESSOA_CONSULTA_PATH = "/adv-service/pessoa/consulta"


class ProjurisClient(BaseClient):
    """Cliente da API Projuris com OAuth2 password flow (access + refresh token em Redis)."""

    _ACCESS_KEY = "projuris:access_token"
    _REFRESH_KEY = "projuris:refresh_token"

    def __init__(
        self,
        cache: CacheBackend,
        base_url: str,
        service_url: str,
        username: str,
        password: str,
        client_id: str,
        client_secret: str,
        timeout: int = 15,
    ) -> None:
        super().__init__(base_url=base_url, timeout=timeout)
        self._cache = cache
        self._service_url = service_url.rstrip("/")
        self._username = username
        self._password = password
        self._client_id = client_id
        self._client_secret = client_secret

    async def _get_valid_token(self) -> str:
        access_token = await self._cache.get(self._ACCESS_KEY)
        if access_token:
            return access_token

        refresh_token = await self._cache.get(self._REFRESH_KEY)
        if refresh_token:
            try:
                return await self._refresh_access_token(refresh_token)
            except IntegrationError:
                _log.warning("projuris_refresh_failed_using_full_auth")

        return await self._authenticate()

    async def _authenticate(self) -> str:
        _log.info("projuris_full_auth")
        data = await self._post_form(_AUTH_PATH, {
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        })
        return await self._store_tokens(data)

    async def _refresh_access_token(self, refresh_token: str) -> str:
        _log.info("projuris_refresh_auth")
        data = await self._post_form(_AUTH_PATH, {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        })
        return await self._store_tokens(data)

    async def _post_form(self, path: str, form_data: dict) -> dict:
        """POST application/x-www-form-urlencoded — necessário para endpoints OAuth2."""
        url = f"{self._base_url}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(url, data=form_data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                _log.error("http_error", url=url, status=exc.response.status_code)
                raise IntegrationError(f"HTTP {exc.response.status_code} from {url}") from exc
            except httpx.RequestError as exc:
                _log.error("request_error", url=url, error=str(exc))
                raise IntegrationError(f"Request failed: {exc}") from exc

    async def _store_tokens(self, data: dict) -> str:
        access_token = data.get("access_token")
        if not access_token:
            raise IntegrationError("Token não encontrado na resposta de autenticação do Projuris.")

        expires_in = int(data.get("expires_in") or 3600)
        refresh_token = data.get("refresh_token")
        refresh_expires_in = int(data.get("refresh_expires_in") or expires_in * 2)

        await self._cache.set(self._ACCESS_KEY, access_token, ttl=max(expires_in - 60, 60))
        if refresh_token:
            await self._cache.set(self._REFRESH_KEY, refresh_token, ttl=max(refresh_expires_in - 60, 60))

        _log.info("projuris_tokens_stored", access_ttl=expires_in - 60, refresh_ttl=refresh_expires_in - 60)
        return access_token

    async def get_processo_by_numero(self, numero: str) -> dict:
        """Busca processo pelo número CNJ via filtro-geral. Retorna o primeiro resultado."""
        token = await self._get_valid_token()
        url = f"{self._service_url}{_PROCESS_CONSULTA_PATH}"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    params={"filtro-geral": numero, "quan-registros": 5, "pagina": 0},
                )
                response.raise_for_status()
                body = response.json()
            except httpx.HTTPStatusError as exc:
                _log.error("http_error", url=url, status=exc.response.status_code)
                raise IntegrationError(f"HTTP {exc.response.status_code} from {url}") from exc
            except httpx.RequestError as exc:
                _log.error("request_error", url=url, error=str(exc))
                raise IntegrationError(f"Request failed: {exc}") from exc

        processos = body.get("processoConsultaWs") or []
        if not processos:
            raise IntegrationError(f"HTTP 404 — processo '{numero}' não encontrado.")

        return processos[0]

    async def get_pessoa_by_telefone(self, telefone: str) -> dict | None:
        """Busca a pessoa pelo telefone, tentando variações de formato.

        Retorna o primeiro registro encontrado (pessoaConsulta[0]) ou None
        se nenhum candidato casar. A chave de filtro é 'telefone' e a
        paginação é 0-indexed (pagina=0).
        """
        token = await self._get_valid_token()
        url = f"{self._service_url}{_PESSOA_CONSULTA_PATH}"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for candidate in phone_candidates(telefone):
                try:
                    response = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {token}"},
                        params={"quan-registros": 10, "pagina": 0},
                        json={"telefone": candidate},
                    )
                    response.raise_for_status()
                    body = response.json()
                except httpx.HTTPStatusError as exc:
                    _log.error("http_error", url=url, status=exc.response.status_code)
                    raise IntegrationError(f"HTTP {exc.response.status_code} from {url}") from exc
                except httpx.RequestError as exc:
                    _log.error("request_error", url=url, error=str(exc))
                    raise IntegrationError(f"Request failed: {exc}") from exc

                pessoas = body.get("pessoaConsulta") or []
                if pessoas:
                    if len(pessoas) > 1:
                        _log.warning(
                            "projuris_pessoa_ambigua",
                            telefone=candidate,
                            total=body.get("totalRegistros"),
                        )
                    return pessoas[0]

        return None
