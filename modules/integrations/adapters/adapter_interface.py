from abc import ABC, abstractmethod


class AdapterInterface(ABC):
    """Interface for all integration adapters — normalizes data to/from internal models."""

    @abstractmethod
    def to_internal(self, external_data: dict) -> dict:
        """Convert external API format → internal domain model."""
        ...

    @abstractmethod
    def to_external(self, internal_data: dict) -> dict:
        """Convert internal domain model → external API format."""
        ...
