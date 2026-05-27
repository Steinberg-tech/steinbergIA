from config.settings import settings
from modules.integrations.base_client import BaseClient
from observability.logger import get_logger
from shared.exceptions import IntegrationError

_log = get_logger("projuris_client")

# Paths da API projurisADV (SajAdv REST). Ajustar quando a documentação
# definitiva do escritório chegar — toda dependência de endpoint vive aqui.
PERSON_SEARCH_PATH = "/pessoa/consulta"
PERSON_DATA_PATH = "/pessoa/{person_id}"
PERSON_CASES_PATH = "/pessoa/{person_id}/processos"


class ProjurisClient(BaseClient):
    """
    Cliente de integração com o projurisADV (Pessoas/Clientes).
    Somente leitura. Sem mock: lança IntegrationError quando não configurado.
    """

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.projuris_base_url,
            api_key=settings.projuris_api_key,
            timeout=settings.projuris_timeout_seconds,
        )
        self._configured = bool(settings.projuris_base_url)

    def _ensure_configured(self) -> None:
        if not self._configured:
            raise IntegrationError(
                "projurisADV não configurado — defina PROJURIS_BASE_URL no .env"
            )

    async def search_person(self, query: str) -> list[dict]:
        self._ensure_configured()
        data = await self._get(PERSON_SEARCH_PATH, params={"q": query})
        _log.info("projuris_person_search", query=query)
        return data

    async def get_person(self, person_id: str) -> dict:
        self._ensure_configured()
        data = await self._get(PERSON_DATA_PATH.format(person_id=person_id))
        _log.info("projuris_person_fetched", person_id=person_id)
        return data

    async def get_person_cases(self, person_id: str) -> list[dict]:
        self._ensure_configured()
        data = await self._get(PERSON_CASES_PATH.format(person_id=person_id))
        _log.info("projuris_person_cases_fetched", person_id=person_id)
        return data
