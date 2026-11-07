from apps.core.choices import DatabaseType


def get_connector_class(db_type: str) -> str | None:
    """Return the connector class for an implemented database type."""
    return {
        DatabaseType.POSTGRESQL: "io.debezium.connector.postgresql.PostgresConnector",
    }.get(db_type)


def get_plugin_name(db_type: str) -> str | None:
    """Return the replication plugin for an implemented database type."""
    return {
        DatabaseType.POSTGRESQL: "pgoutput",
    }.get(db_type)
