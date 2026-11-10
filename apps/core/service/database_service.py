import psycopg

from apps.core.choices import DatabaseType
from apps.core.service.interface import DatabaseService
from utils.data_types import ClickHouseDataType, PostgresDataType


class POSTGRES(DatabaseService):
    CLICKHOUSE_TYPES = {
        PostgresDataType.SMALLINT: ClickHouseDataType.SMALLINT,
        PostgresDataType.INTEGER: ClickHouseDataType.INTEGER,
        PostgresDataType.BIGINT: ClickHouseDataType.BIGINT,
        PostgresDataType.REAL: ClickHouseDataType.REAL,
        PostgresDataType.DOUBLE_PRECISION: ClickHouseDataType.DOUBLE_PRECISION,
        PostgresDataType.BOOLEAN: ClickHouseDataType.BOOLEAN,
        PostgresDataType.CHARACTER: ClickHouseDataType.CHARACTER,
        PostgresDataType.CHARACTER_VARYING: ClickHouseDataType.CHARACTER_VARYING,
        PostgresDataType.TEXT: ClickHouseDataType.TEXT,
        PostgresDataType.BYTEA: ClickHouseDataType.BYTEA,
        PostgresDataType.UUID: ClickHouseDataType.UUID,
        PostgresDataType.JSON: ClickHouseDataType.JSON,
        PostgresDataType.JSONB: ClickHouseDataType.JSONB,
        PostgresDataType.DATE: ClickHouseDataType.DATE,
        PostgresDataType.TIME_WITHOUT_TIME_ZONE: ClickHouseDataType.TIME_WITHOUT_TIME_ZONE,
        PostgresDataType.TIME_WITH_TIME_ZONE: ClickHouseDataType.TIME_WITH_TIME_ZONE,
        PostgresDataType.INTERVAL: ClickHouseDataType.INTERVAL,
        PostgresDataType.XML: ClickHouseDataType.XML,
        PostgresDataType.INET: ClickHouseDataType.INET,
        PostgresDataType.CIDR: ClickHouseDataType.CIDR,
        PostgresDataType.MACADDR: ClickHouseDataType.MACADDR,
        PostgresDataType.MACADDR8: ClickHouseDataType.MACADDR8,
    }

    @staticmethod
    def to_consumer_type(
        data_type: str,
        nullable: bool = False,
        precision: int | None = None,
        scale: int | None = None,
        datetime_precision: int | None = None,
    ) -> str | None:
        """Suggest a destination type, or None when manual mapping is needed."""
        if data_type == PostgresDataType.NUMERIC:
            if (
                precision is None
                or scale is None
                or not (1 <= precision <= 76 and 0 <= scale <= precision)
            ):
                return None
            target_type = f"{ClickHouseDataType.DECIMAL}({precision}, {scale})"
        elif data_type in {
            PostgresDataType.TIMESTAMP_WITHOUT_TIME_ZONE,
            PostgresDataType.TIMESTAMP_WITH_TIME_ZONE,
        }:
            fractional_digits = 6 if datetime_precision is None else datetime_precision
            timezone = ", 'UTC'" if data_type == PostgresDataType.TIMESTAMP_WITH_TIME_ZONE else ""
            target_type = f"{ClickHouseDataType.DATETIME64}({fractional_digits}{timezone})"
        else:
            target_type = POSTGRES.CLICKHOUSE_TYPES.get(data_type)
        if target_type is None:
            return None
        return f"{ClickHouseDataType.NULLABLE}({target_type})" if nullable else target_type

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
    ):
        self.config = {
            "host": host,
            "port": port,
            "dbname": database,
            "user": username,
            "password": password,
            "connect_timeout": 5,
        }
    

    def connection_test(self) -> dict:
        try:
            with psycopg.connect(**self.config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1;")
                    cursor.fetchone()

            return {
                "success": True,
                "message": "PostgreSQL connection successful",
            }

        except psycopg.Error:
            return {
                "success": False,
                "message": "Unable to connect to the PostgreSQL database.",
            }

    def get_tables(self) -> dict:
        try:
            with psycopg.connect(**self.config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT schemaname, tablename
                        FROM pg_catalog.pg_tables
                        WHERE schemaname NOT IN (
                            'pg_catalog',
                            'information_schema'
                        )
                        ORDER BY schemaname, tablename;
                    """)
                    all_tables = [".".join(table) for table in cursor.fetchall()]

            return {
                "success": True,
                "database": self.config["dbname"],
                "tables": all_tables,
            }
        except psycopg.Error:
            return {
                "success": False,
                "database": self.config["dbname"],
                "tables": [],
                "message": "Unable to read database tables.",
            }


    def get_columns(self, table: str) -> dict:
        try:
            schema, table_name = table.split(".", 1)
            with psycopg.connect(**self.config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            column_name,
                            data_type,
                            is_nullable,
                            column_default,
                            character_maximum_length,
                            numeric_precision,
                            numeric_scale,
                            datetime_precision
                        FROM information_schema.columns
                        WHERE table_schema = %s
                        AND table_name = %s
                        ORDER BY ordinal_position;
                        """,
                        (schema, table_name),
                    )

                    columns = [
                        {
                            "name": row[0],
                            "type": row[1],
                            "consumer_type": self.to_consumer_type(
                                row[1],
                                nullable=row[2] == "YES",
                                precision=row[5],
                                scale=row[6],
                                datetime_precision=row[7],
                            ),
                            "nullable": row[2] == "YES",
                            "default": row[3],
                            "max_length": row[4],
                            "precision": row[5],
                            "scale": row[6],
                        }
                        for row in cursor.fetchall()
                    ]

            return {
                "success": True,
                "database": self.config["dbname"],
                "table": table,
                "columns": columns,
            }

        except ValueError:
            return {
                "success": False,
                "message": "Invalid table name. Expected schema.table.",
                "columns": [],
            }
        except psycopg.Error:
            return {
                "success": False,
                "database": self.config["dbname"],
                "table": table,
                "columns": [],
                "message": "Unable to read table columns.",
            }


class DatabaseServiceFactory:
    @staticmethod
    def get_service(db_type, **connection_kwargs) -> DatabaseService:
        services = {
            DatabaseType.POSTGRESQL: POSTGRES,
        }
        service_class = services.get(db_type)
        if not service_class:
            return None
        return service_class(**connection_kwargs)


