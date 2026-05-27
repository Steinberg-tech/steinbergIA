from modules.ai.tools.base_tool import BaseTool
from observability.tracer import trace
from shared.exceptions import IntegrationError


class ProjurisPersonDataTool(BaseTool):
    """Consulta os dados cadastrais de um cliente no projurisADV."""

    def __init__(self, projuris_client) -> None:
        self._projuris = projuris_client

    @property
    def name(self) -> str:
        return "consultar_dados_cliente"

    @property
    def description(self) -> str:
        return (
            "Consulta os dados cadastrais de um cliente (CPF, endereço, contatos) "
            "pelo identificador da pessoa no projurisADV."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "person_id": {
                    "type": "string",
                    "description": "Identificador da pessoa no projurisADV.",
                },
            },
            "required": ["person_id"],
        }

    async def execute(self, person_id: str) -> dict:
        async with trace("tool.consultar_dados_cliente", person_id=person_id):
            try:
                return await self._projuris.get_person(person_id)
            except Exception as exc:
                raise IntegrationError(
                    f"Falha ao consultar dados do cliente {person_id}: {exc}"
                ) from exc
