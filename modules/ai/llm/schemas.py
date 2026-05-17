from pydantic import BaseModel

from shared.constants import Intent, MessageRole


class LLMMessage(BaseModel):
    role: MessageRole
    content: str


class LLMRequest(BaseModel):
    messages: list[LLMMessage]
    model: str | None = None
    temperature: float = 0.3
    max_tokens: int = 1024
    tools: list[dict] | None = None


class LLMResponse(BaseModel):
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: list[dict] | None = None


class IntentClassification(BaseModel):
    intent: Intent
    confidence: float = 1.0
    reasoning: str = ""
