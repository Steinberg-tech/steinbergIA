from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AgentResponse:
    message: str
    tool_calls: list[dict] | None = None
    escalate: bool = False
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Base contract for all SAC agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique agent identifier registered in the router."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """What this agent handles (used by the router for logging/debug)."""
        ...

    @abstractmethod
    async def handle(self, user_message: str, context: dict) -> AgentResponse:
        """Process the user message and return a structured response."""
        ...
