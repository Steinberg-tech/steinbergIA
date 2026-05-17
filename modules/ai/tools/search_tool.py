from modules.ai.tools.base_tool import BaseTool
from observability.logger import get_logger
from observability.tracer import trace

_log = get_logger("search_tool")


class SearchTool(BaseTool):
    """Searches the knowledge base for relevant FAQ / document content."""

    def __init__(self, knowledge_service) -> None:
        self._knowledge = knowledge_service

    @property
    def name(self) -> str:
        return "search_knowledge"

    @property
    def description(self) -> str:
        return (
            "Busca na base de conhecimento da empresa para responder dúvidas sobre "
            "produtos, serviços, políticas, prazos e procedimentos."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Pergunta ou termos a buscar na base de conhecimento.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Número máximo de resultados (padrão 3).",
                    "default": 3,
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str, top_k: int = 3) -> dict:
        async with trace("tool.search_knowledge", query=query[:80]):
            results = await self._knowledge.search(query, top_k=top_k)
        _log.info("search_tool_results", query=query[:80], count=len(results))
        return {"results": results, "count": len(results)}
