import json

from shared.interfaces import CacheBackend


class SessionMemory:
    """
    Stores transient per-session state in Redis (cleared on TTL expiry).
    Examples: current workflow step, last intent detected, temporary data collected.
    """

    def __init__(self, cache: CacheBackend, ttl: int = 3600) -> None:
        self._cache = cache
        self._ttl = ttl

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    async def get(self, session_id: str) -> dict:
        raw = await self._cache.get(self._key(session_id))
        if raw:
            return json.loads(raw)
        return {}

    async def set(self, session_id: str, data: dict) -> None:
        await self._cache.set(self._key(session_id), json.dumps(data), ttl=self._ttl)

    async def update(self, session_id: str, **kwargs) -> None:
        current = await self.get(session_id)
        current.update(kwargs)
        await self.set(session_id, current)

    async def clear(self, session_id: str) -> None:
        await self._cache.delete(self._key(session_id))
