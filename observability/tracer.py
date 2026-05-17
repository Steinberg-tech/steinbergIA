import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from observability.logger import get_logger

_log = get_logger("tracer")


@asynccontextmanager
async def trace(operation: str, **attrs) -> AsyncIterator[dict]:
    """Lightweight async context manager that logs duration of any operation."""
    span: dict = {"operation": operation, **attrs}
    start = time.perf_counter()
    try:
        yield span
        span["status"] = "ok"
    except Exception as exc:
        span["status"] = "error"
        span["error"] = str(exc)
        raise
    finally:
        span["duration_ms"] = round((time.perf_counter() - start) * 1000, 2)
        _log.info("trace", **span)
