from modules.ai.tools.base_tool import BaseTool
from observability.tracer import trace
from shared.exceptions import IntegrationError


class ProjurisPersonCasesTool(BaseTool):
    """Lista os processos vinculados a um cliente no projurisADV."""

    def __init__(self, projuris_client) -> None:
        self._projuris = projuris_client

    @property
    def name(self) -> str:
        return "consultar_processos_cliente"

    @property
    def description(self) -> str:
        return (
            "Lista os processos vinculados a um cliente pelo identificador da pessoa "
            "no projurisADV. Use após identificar o cliente com buscar_cliente."
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
        async with trace("tool.consultar_processos_cliente", person_id=person_id):
            try:
                cases = await self._projuris.get_person_cases(person_id)
                return {"cases": cases, "count": len(cases)}
            except Exception as exc:
                raise IntegrationError(
                    f"Falha ao consultar processos do cliente {person_id}: {exc}"
                ) from exc
