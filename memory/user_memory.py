import json

from shared.interfaces import CacheBackend


class UserMemory:
    """
    Stores persistent facts about the contact across sessions.
    Keyed by session_id (phone number, external ID, etc.).
    Backed by Redis with a long TTL — suitable for preferences and known context.
    """

    _TTL = 60 * 60 * 24 * 30  # 30 days

    def __init__(self, cache: CacheBackend) -> None:
        self._cache = cache

    def _key(self, session_id: str) -> str:
        return f"user_memory:{session_id}"

    async def get(self, session_id: str) -> dict:
        raw = await self._cache.get(self._key(session_id))
        if raw:
            return json.loads(raw)
        return {}

    async def update(self, session_id: str, **kwargs) -> None:
        current = await self.get(session_id)
        current.update(kwargs)
        await self._cache.set(self._key(session_id), json.dumps(current), ttl=self._TTL)

    async def remember_name(self, session_id: str, name: str) -> None:
        await self.update(session_id, name=name)

    async def remember_last_order(self, session_id: str, order_id: str) -> None:
        await self.update(session_id, last_order_id=order_id)
