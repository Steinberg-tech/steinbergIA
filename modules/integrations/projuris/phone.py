import re


def phone_candidates(raw: str) -> list[str]:
    """Gera candidatos de telefone no formato esperado pelo Projuris.

    Projuris exige DDD + 9 + 8 dígitos (11 dígitos), sem o código de país 55.
    O Digisac entrega com '55' e, às vezes, sem o 9º dígito. Devolvemos os
    formatos plausíveis em ordem de probabilidade, sem duplicatas.
    """
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("55") and len(digits) in (12, 13):
        digits = digits[2:]

    candidates: list[str] = []

    def add(value: str) -> None:
        if value and value not in candidates:
            candidates.append(value)

    if len(digits) == 10:                      # DDD + 8 -> insere o 9 móvel
        add(digits[:2] + "9" + digits[2:])
        add(digits)
    elif len(digits) == 11:                    # DDD + 9 + 8
        add(digits)
        if digits[2] == "9":                   # também tenta sem o 9
            add(digits[:2] + digits[3:])
    else:
        # Inputs que não batem com 10/11 dígitos são repassados como estão.
        # Candidatos inválidos não geram match no Projuris downstream.
        add(digits)

    return candidates
