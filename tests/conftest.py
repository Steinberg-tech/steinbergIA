import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from modules.ai.llm.schemas import IntentClassification, LLMResponse
from modules.ai.llm.client import LLMClient
from modules.ai.tools.registry import ToolRegistry
from modules.ai.tools.base_tool import BaseTool
from memory.context_builder import ContextBuilder
from shared.constants import Intent, MessageRole


@pytest.fixture
def mock_llm() -> LLMClient:
    llm = AsyncMock(spec=LLMClient)
    llm.classify_intent.return_value = IntentClassification(
        intent=Intent.FAQ,
        confidence=0.95,
        reasoning="Test classification",
    )
    llm.generate_response.return_value = LLMResponse(
        content="Resposta de teste do assistente.",
        model="gpt-4o-mock",
        input_tokens=50,
        output_tokens=20,
    )
    return llm


@pytest.fixture
def mock_context() -> dict:
    return {
        "session_id": "test-session-001",
        "history": [
            {"role": MessageRole.USER, "content": "Olá"},
            {"role": MessageRole.ASSISTANT, "content": "Olá! Como posso ajudar?"},
        ],
        "session": {},
        "user": {"name": "Cliente Teste"},
    }


class _MockTool(BaseTool):
    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "Mock tool for tests."

    @property
    def parameters_schema(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **params) -> dict:
        return {"result": "mock_result"}


@pytest.fixture
def mock_registry() -> ToolRegistry:
    return ToolRegistry([_MockTool()])


@pytest.fixture
def mock_context_builder(mock_context) -> ContextBuilder:
    builder = AsyncMock(spec=ContextBuilder)
    builder.build.return_value = mock_context
    return builder
