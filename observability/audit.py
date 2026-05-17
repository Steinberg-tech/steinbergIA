from datetime import datetime, timezone

from observability.logger import get_logger

_log = get_logger("audit")


def log_event(
    event: str,
    session_id: str,
    *,
    agent: str | None = None,
    tool: str | None = None,
    details: dict | None = None,
) -> None:
    _log.info(
        event,
        session_id=session_id,
        agent=agent,
        tool=tool,
        details=details or {},
        ts=datetime.now(timezone.utc).isoformat(),
    )
