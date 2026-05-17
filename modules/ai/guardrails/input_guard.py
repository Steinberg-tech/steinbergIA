from config.settings import settings
from modules.ai.guardrails.content_filter import ContentFilter
from shared.exceptions import InputValidationError


class InputGuard:
    def __init__(self, content_filter: ContentFilter) -> None:
        self._filter = content_filter
        self._max_len = settings.max_input_length

    def validate(self, text: str) -> str:
        text = text.strip()
        if not text:
            raise InputValidationError("Mensagem vazia.")
        if len(text) > self._max_len:
            raise InputValidationError(
                f"Mensagem excede o limite de {self._max_len} caracteres."
            )
        self._filter.check(text)
        return text
