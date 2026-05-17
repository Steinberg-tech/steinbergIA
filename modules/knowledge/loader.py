import pathlib
from typing import Iterator


def load_text(path: str) -> Iterator[dict]:
    """Loads a plain text file as a single document."""
    p = pathlib.Path(path)
    yield {"title": p.stem, "content": p.read_text(encoding="utf-8"), "source": str(p)}


def load_markdown(path: str) -> Iterator[dict]:
    """Loads a markdown file, splitting on H2 headings."""
    p = pathlib.Path(path)
    text = p.read_text(encoding="utf-8")
    sections = text.split("\n## ")
    for section in sections:
        lines = section.strip().splitlines()
        if not lines:
            continue
        title = lines[0].lstrip("# ").strip()
        content = "\n".join(lines[1:]).strip()
        if content:
            yield {"title": title, "content": content, "source": str(p)}


def load_jsonl(path: str) -> Iterator[dict]:
    """Loads a JSONL file where each line is {"title": ..., "content": ...}."""
    import json
    p = pathlib.Path(path)
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)
