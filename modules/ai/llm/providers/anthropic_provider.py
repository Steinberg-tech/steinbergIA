import json

import anthropic

from config.settings import settings
from modules.ai.llm.client import LLMClient
from modules.ai.llm.schemas import IntentClassification, LLMResponse
from observability.tracer import trace
from shared.constants import Intent, MessageRole
from shared.exceptions import LLMProviderError

_INTENT_TOOL = {
    "name": "classify_intent",
    "description": "Classifica a intenção do usuário para rotear ao agente correto.",
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": [i.value for i in Intent],
            },
            "confidence": {"type": "number"},
            "reasoning": {"type": "string"},
        },
        "required": ["intent", "confidence"],
    },
}

_CLASSIFICATION_SYSTEM = """Você é um classificador de intenções para um sistema de SAC.
Analise a última mensagem do usuário. Use a ferramenta classify_intent para indicar a intenção.

Intenções: faq | order_status | support | workflow"""


class AnthropicProvider(LLMClient):
    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def classify_intent(self, user_message: str, context: dict) -> IntentClassification:
        history = context.get("history", [])
        messages = []
        for h in history[-6:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        async with trace("anthropic.classify_intent", model=self._model):
            try:
                resp = await self._client.messages.create(
                    model=self._model,
                    max_tokens=256,
                    system=_CLASSIFICATION_SYSTEM,
                    messages=messages,
                    tools=[_INTENT_TOOL],
                    tool_choice={"type": "tool", "name": "classify_intent"},
                )
            except Exception as exc:
                raise LLMProviderError(f"Anthropic classify_intent failed: {exc}") from exc

        tool_block = next(b for b in resp.content if b.type == "tool_use")
        args = tool_block.input
        return IntentClassification(
            intent=Intent(args["intent"]),
            confidence=args.get("confidence", 1.0),
            reasoning=args.get("reasoning", ""),
        )

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        messages = []
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        kwargs: dict = {
            "model": self._model,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        async with trace("anthropic.generate_response", model=self._model):
            try:
                resp = await self._client.messages.create(**kwargs)
            except Exception as exc:
                raise LLMProviderError(f"Anthropic generate_response failed: {exc}") from exc

        text_content = ""
        tool_calls = None
        for block in resp.content:
            if block.type == "text":
                text_content = block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append({"id": block.id, "name": block.name, "arguments": block.input})

        return LLMResponse(
            content=text_content,
            model=resp.model,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            tool_calls=tool_calls,
        )
