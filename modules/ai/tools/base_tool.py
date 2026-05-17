from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Base contract for all AI-invokable tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier used by the LLM to call this tool."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description used by the LLM to decide when to use this tool."""
        ...

    @property
    @abstractmethod
    def parameters_schema(self) -> dict:
        """JSON Schema describing the tool's accepted parameters."""
        ...

    @abstractmethod
    async def execute(self, **params) -> dict:
        """Execute the tool and return a result dict."""
        ...

    def to_openai_schema(self) -> dict:
        """Returns the OpenAI-compatible tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }
