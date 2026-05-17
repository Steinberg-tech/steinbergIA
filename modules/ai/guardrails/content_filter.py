import re

from config.settings import settings
from shared.exceptions import InputValidationError

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.I),
    re.compile(r"(system\s+prompt|jailbreak|act\s+as\s+(a\s+)?DAN)", re.I),
    re.compile(r"<\s*script.*?>", re.I),
]


class ContentFilter:
    def __init__(self) -> None:
        self._blocked = settings.blocked_terms_list

    def check(self, text: str) -> None:
        lower = text.lower()
        for term in self._blocked:
            if term in lower:
                raise InputValidationError(f"Conteúdo bloqueado detectado.")

        for pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                raise InputValidationError("Tentativa de injeção de prompt detectada.")
