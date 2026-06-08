from modules.ai.tools.base_tool import BaseTool
from observability.tracer import trace
from shared.exceptions import IntegrationError, ToolExecutionError


class ProcessTool(BaseTool):
    """Consulta dados de processo jurídico via Projuris pelo número CNJ."""

    def __init__(self, projuris_client) -> None:
        self._projuris = projuris_client

    @property
    def name(self) -> str:
        return "get_process_info"

    @property
    def description(self) -> str:
        return (
            "Consulta dados gerais de um processo jurídico pelo número CNJ. "
            "Retorna classe processual, vara/órgão julgador, magistrado e partes envolvidas."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "numero_processo": {
                    "type": "string",
                    "description": "Número do processo no formato CNJ (ex: 0001234-12.2023.8.26.0000).",
                },
            },
            "required": ["numero_processo"],
        }

    async def execute(self, numero_processo: str) -> dict:
        async with trace("tool.get_process_info", numero=numero_processo):
            try:
                processo = await self._projuris.get_processo_by_numero(numero_processo)
                codigo = processo.get("codigoProcesso")
                envolvidos_raw = (
                    await self._projuris.get_processo_envolvidos(codigo) if codigo else []
                )
            except IntegrationError as exc:
                raise ToolExecutionError(
                    f"Falha ao consultar processo {numero_processo}: {exc}"
                ) from exc

        processo["envolvidos"] = [
            {
                "codigo_pessoa": e.get("codigoPessoaEnvolvido"),
                "nome": e.get("nomePessoaEnvolvido"),
                "participacao": e.get("participacaoTipo"),
            }
            for e in envolvidos_raw
        ]
        return processo
