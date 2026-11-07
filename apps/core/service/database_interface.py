from abc import ABC, abstractmethod


class DatabaseService(ABC):
    """Contract implemented by configured database services."""

    @abstractmethod
    def connection_test(self) -> dict:
        pass

    @abstractmethod
    def get_tables(self) -> dict:
        """List accessible user tables and views with their columns."""
        pass

    @abstractmethod
    def get_columns(self, table: str) -> dict:
        """List columns for a schema-qualified table."""
        pass
