import json

from openai import AsyncOpenAI

from config.settings import settings
from modules.ai.llm.client import LLMClient
from modules.ai.llm.schemas import IntentClassification, LLMResponse
from observability.logger import get_logger
from observability.tracer import trace
from shared.constants import Intent
from shared.exceptions import LLMProviderError

_log = get_logger("deepseek_provider")

_DEEPSEEK_BASE_URL = "https://api.deepseek.com"

_INTENT_TOOL = {
    "type": "function",
    "function": {
        "name": "classify_intent",
        "description": "Classifica a intenção do usuário para rotear ao agente correto.",
        "parameters": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": [i.value for i in Intent],
                    "description": "Intenção identificada",
                },
                "confidence": {
                    "type": "number",
                    "description": "Confiança de 0.0 a 1.0",
                },
                "reasoning": {
                    "type": "string",
                    "description": "Breve justificativa da classificação",
                },
            },
            "required": ["intent", "confidence"],
        },
    },
}

_CLASSIFICATION_SYSTEM = """Você é um classificador de intenções para um sistema de SAC jurídico.
Analise a última mensagem do usuário e o histórico da conversa.
Use a função classify_intent para indicar a intenção correta.

Intenções disponíveis:
- faq: dúvidas gerais, perguntas sobre processos, direitos, documentos, honorários
- order_status: consulta de andamento de processo, prazos, audiências
- support: reclamações, problemas, solicitação de atendimento humano
- workflow: processo multi-etapa como agendamento de consulta, envio de documentos

Responda SEMPRE usando a função classify_intent."""


class DeepSeekProvider(LLMClient):
    """DeepSeek provider — uses the OpenAI-compatible API with a different base_url."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=_DEEPSEEK_BASE_URL,
        )
        self._model = settings.deepseek_model

    async def classify_intent(self, user_message: str, context: dict) -> IntentClassification:
        history = context.get("history", [])
        messages = [{"role": "system", "content": _CLASSIFICATION_SYSTEM}]
        for h in history[-6:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        async with trace("deepseek.classify_intent", model=self._model):
            try:
                resp = await self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    tools=[_INTENT_TOOL],
                    tool_choice={"type": "function", "function": {"name": "classify_intent"}},
                    temperature=0.0,
                )
            except Exception as exc:
                raise LLMProviderError(f"DeepSeek classify_intent failed: {exc}") from exc

        tool_call = resp.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
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
        messages = [{"role": "system", "content": system_prompt}]
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        kwargs: dict = {"model": self._model, "messages": messages, "temperature": 0.4}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        async with trace("deepseek.generate_response", model=self._model):
            try:
                resp = await self._client.chat.completions.create(**kwargs)
            except Exception as exc:
                raise LLMProviderError(f"DeepSeek generate_response failed: {exc}") from exc

        choice = resp.choices[0].message
        tool_calls = None
        if choice.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                }
                for tc in choice.tool_calls
            ]

        return LLMResponse(
            content=choice.content or "",
            model=resp.model,
            input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            output_tokens=resp.usage.completion_tokens if resp.usage else 0,
            tool_calls=tool_calls,
        )
