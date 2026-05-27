from modules.ai.tools.base_tool import BaseTool
from observability.tracer import trace
from shared.exceptions import IntegrationError


class ProjurisSearchPersonTool(BaseTool):
    """Busca um cliente no projurisADV por nome, CPF ou telefone."""

    def __init__(self, projuris_client) -> None:
        self._projuris = projuris_client

    @property
    def name(self) -> str:
        return "buscar_cliente"

    @property
    def description(self) -> str:
        return (
            "Busca um cliente no sistema jurídico (projurisADV) por nome, CPF ou "
            "telefone. Retorna a lista de pessoas encontradas com seus identificadores."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Nome, CPF ou telefone do cliente a buscar.",
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str) -> dict:
        async with trace("tool.buscar_cliente", query=query):
            try:
                results = await self._projuris.search_person(query)
                return {"results": results, "count": len(results)}
            except Exception as exc:
                raise IntegrationError(f"Falha ao buscar cliente '{query}': {exc}") from exc
