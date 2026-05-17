from abc import ABC, abstractmethod
from typing import Any


class Repository(ABC):
    """Generic async repository interface."""

    @abstractmethod
    async def get(self, id: str) -> Any | None: ...

    @abstractmethod
    async def save(self, entity: Any) -> Any: ...

    @abstractmethod
    async def delete(self, id: str) -> bool: ...


class CacheBackend(ABC):
    """Generic cache interface (implemented by Redis adapter)."""

    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int | None = None) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...
