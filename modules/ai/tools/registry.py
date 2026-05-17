from modules.ai.tools.base_tool import BaseTool
from shared.exceptions import ToolExecutionError
from observability.logger import get_logger

_log = get_logger("tool_registry")


class ToolRegistry:
    """Central registry of all tools available to agents."""

    def __init__(self, tools: list[BaseTool]) -> None:
        self._tools: dict[str, BaseTool] = {t.name: t for t in tools}

    def get_tool_schemas(self) -> list[dict]:
        """Returns OpenAI-compatible tool definitions for all registered tools."""
        return [t.to_openai_schema() for t in self._tools.values()]

    def get(self, name: str) -> BaseTool:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolExecutionError(f"Tool '{name}' not found in registry.")
        return tool

    async def execute(self, name: str, **params) -> dict:
        tool = self.get(name)
        _log.info("tool_execute", tool=name, params=list(params.keys()))
        try:
            return await tool.execute(**params)
        except Exception as exc:
            _log.error("tool_error", tool=name, error=str(exc))
            raise ToolExecutionError(f"Tool '{name}' failed: {exc}") from exc
