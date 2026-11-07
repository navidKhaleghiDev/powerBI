from abc import ABC, abstractmethod


class DatabaseService(ABC):
    """Contract implemented by configured database services."""

    @abstractmethod
    def connection_test(self) -> dict:
        pass

    @abstractmethod
    def get_tables(self) -> dict:
        """List accessible user tables as schema-qualified names."""
        pass

    @abstractmethod
    def get_columns(self, table: str) -> dict:
        """List columns for a schema-qualified table."""
        pass


class ConnectServiceInterface(ABC):
    """Contract implemented by Kafka Connect services."""

    @abstractmethod
    def create_connector(self, name: str, db_type: str, config: dict) -> tuple[dict, int]:
        """Return (sanitized body, DRF HTTP status code) for connector creation."""
        pass
