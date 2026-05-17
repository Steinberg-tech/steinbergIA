from abc import ABC, abstractmethod

from modules.ai.llm.schemas import IntentClassification, LLMResponse


class LLMClient(ABC):
    """Abstract base for all LLM provider implementations."""

    @abstractmethod
    async def classify_intent(self, user_message: str, context: dict) -> IntentClassification:
        """Classifies the user's intent from their message and conversation context."""
        ...

    @abstractmethod
    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        """Generates the agent's response, optionally with tool definitions."""
        ...
