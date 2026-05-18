import base64

from config.settings import settings
from observability.logger import get_logger

_log = get_logger("image_analyzer")

_VISION_PROMPT = (
    "Você é um assistente de atendimento jurídico. "
    "Descreva o conteúdo da imagem de forma clara e objetiva, em português do Brasil. "
    "Se for um documento (contrato, extrato, cartão, RG, CPF), extraia os dados principais visíveis. "
    "Seja conciso — no máximo 3 parágrafos curtos."
)


class ImageAnalyzer:
    """Analyzes image bytes using OpenAI GPT-4o Vision."""

    async def analyze(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        if not settings.openai_api_key:
            _log.warning("image_analyzer_no_key")
            return "[Imagem recebida — análise indisponível: configure OPENAI_API_KEY]"

        from openai import AsyncOpenAI

        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64}"

        client = AsyncOpenAI(api_key=settings.openai_api_key)

        try:
            resp = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": _VISION_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                            {"type": "text", "text": "O que está nesta imagem?"},
                        ],
                    },
                ],
                max_tokens=512,
                temperature=0.2,
            )
            description = resp.choices[0].message.content or ""
            _log.info("image_analyzed", chars=len(description))
            return description.strip()
        except Exception as exc:
            _log.error("image_analysis_error", error=str(exc))
            return "[Imagem recebida — não foi possível analisar no momento]"
