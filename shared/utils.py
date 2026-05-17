import re
import uuid
from datetime import datetime, timezone


def generate_id() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def generate_protocol() -> str:
    """Generates a unique support ticket protocol number."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = str(uuid.uuid4())[:6].upper()
    return f"SAC-{ts}-{suffix}"


def truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def strip_pii_patterns(text: str) -> str:
    """Redacts common PII patterns (CPF, phone, email) from text."""
    cpf = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
    phone = re.compile(r"\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}\b")
    email = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
    text = cpf.sub("[CPF]", text)
    text = phone.sub("[TELEFONE]", text)
    text = email.sub("[EMAIL]", text)
    return text
