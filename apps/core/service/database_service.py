import psycopg
from apps.core.service.interface import DatabaseService
from apps.core.choices import DatabaseType


class POSTGRES(DatabaseService):

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
                            numeric_scale
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


