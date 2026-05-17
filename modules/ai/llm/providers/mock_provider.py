"""
Mock LLM provider for development without API keys.
Enabled automatically when LLM_PROVIDER=mock or when no API key is configured.
"""

from modules.ai.llm.client import LLMClient
from modules.ai.llm.schemas import IntentClassification, LLMResponse
from shared.constants import Intent

_MOCK_RESPONSES: dict[str, str] = {
    "faq": (
        "Olá! Sou o assistente SAC AI (modo desenvolvimento). "
        "Para usar respostas reais, configure sua OPENAI_API_KEY ou ANTHROPIC_API_KEY no .env."
    ),
    "order_status": (
        "[Mock] Consultando pedido... Seu pedido está em separação e será entregue em breve. "
        "(Configure sua API key para respostas reais do ERP.)"
    ),
    "support": (
        "[Mock] Entendido! Seu chamado foi registrado com protocolo SAC-MOCK-001. "
        "Em breve nossa equipe entrará em contato."
    ),
    "workflow": (
        "[Mock] Iniciando fluxo de atendimento. "
        "Por favor, informe mais detalhes para prosseguirmos."
    ),
}


class MockProvider(LLMClient):
    """Returns static responses — useful for local dev without API keys."""

    async def classify_intent(self, user_message: str, context: dict) -> IntentClassification:
        lower = user_message.lower()
        if any(w in lower for w in ["pedido", "entrega", "rastreio", "status"]):
            intent = Intent.ORDER_STATUS
        elif any(w in lower for w in ["reclamação", "problema", "defeito", "chamado", "suporte"]):
            intent = Intent.SUPPORT
        elif any(w in lower for w in ["troca", "cancelar", "cancelamento", "reembolso", "devol"]):
            intent = Intent.WORKFLOW
        else:
            intent = Intent.FAQ
        return IntentClassification(intent=intent, confidence=0.8, reasoning="mock classification")

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        lower = user_message.lower()
        if any(w in lower for w in ["pedido", "entrega", "rastreio"]):
            content = _MOCK_RESPONSES["order_status"]
        elif any(w in lower for w in ["reclamação", "problema", "defeito"]):
            content = _MOCK_RESPONSES["support"]
        elif any(w in lower for w in ["troca", "cancelar", "reembolso"]):
            content = _MOCK_RESPONSES["workflow"]
        else:
            content = _MOCK_RESPONSES["faq"]
        return LLMResponse(content=content, model="mock", input_tokens=10, output_tokens=30)
