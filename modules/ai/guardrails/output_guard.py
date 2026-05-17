from shared.exceptions import OutputValidationError
from shared.utils import strip_pii_patterns

_SENSITIVE_LEAKS = ["api_key", "secret", "password", "token", "bearer "]


class OutputGuard:
    def validate(self, text: str) -> str:
        lower = text.lower()
        for leak in _SENSITIVE_LEAKS:
            if leak in lower:
                raise OutputValidationError("Resposta contém dado sensível bloqueado.")
        return strip_pii_patterns(text)
