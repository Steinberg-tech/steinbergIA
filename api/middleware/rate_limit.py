import time

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from config.settings import settings
from observability.logger import get_logger

_log = get_logger("rate_limit")

_WINDOW = settings.rate_limit_window_seconds
_MAX = settings.rate_limit_requests

_buckets: dict[str, list[float]] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-process sliding window rate limiter keyed by session_id query param
    or X-Session-ID header. For production, replace with Redis-backed sliding window.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in ("/health", "/metrics"):
            return await call_next(request)

        key = (
            request.headers.get("X-Session-ID")
            or request.query_params.get("session_id")
            or request.client.host
        )
        now = time.time()
        window_start = now - _WINDOW
        hits = _buckets.get(key, [])
        hits = [t for t in hits if t > window_start]
        hits.append(now)
        _buckets[key] = hits

        if len(hits) > _MAX:
            _log.warning("rate_limit_exceeded", key=key, hits=len(hits))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas requisições. Aguarde um momento e tente novamente.",
            )
        return await call_next(request)
