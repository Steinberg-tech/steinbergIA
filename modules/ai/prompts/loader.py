from pathlib import Path

_MESSAGES_DIR = Path(__file__).parent / "messages"


def load_message_template(name: str) -> str:
    """Load a message template .md by name, returning only the message body."""
    path = _MESSAGES_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Template '{name}' not found at {path}")
    return _extract_message(path.read_text(encoding="utf-8"))


def load_message_template_full(name: str) -> str:
    """Load a message template .md by name, returning full content (message + instructions)."""
    path = _MESSAGES_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Template '{name}' not found at {path}")
    return path.read_text(encoding="utf-8")


def list_available_templates() -> list[str]:
    """Return names of all available message templates."""
    return [p.stem for p in sorted(_MESSAGES_DIR.glob("*.md"))]


def _extract_message(content: str) -> str:
    """Extract only the text under the '## Mensagem' section."""
    lines = content.splitlines()
    capturing = False
    message_lines: list[str] = []

    for line in lines:
        if line.strip() == "## Mensagem":
            capturing = True
            continue
        if capturing:
            if line.startswith("## "):
                break
            message_lines.append(line)

    return "\n".join(message_lines).strip()
