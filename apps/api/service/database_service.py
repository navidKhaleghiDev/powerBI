import os

import psycopg2

class POSTGRES:
    COLUMN_QUERY = """
        SELECT
            current_database() AS database_name,
            table_schema AS schema_name,
            table_name,
            column_name,
            data_type,
            character_maximum_length AS max_length,
            numeric_precision,
            numeric_scale
        FROM
            information_schema.columns
        WHERE
            table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY
            table_schema, table_name, ordinal_position;
    """

    @staticmethod
    def get_connection_kwargs(db_name="postgres"):
        return {
            "dbname": db_name,
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
        }

    @staticmethod
    def get_databases():
        with psycopg2.connect(**POSTGRES.get_connection_kwargs()) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
                return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def fetch_columns_for_database(db_name):
        with psycopg2.connect(**POSTGRES.get_connection_kwargs(db_name)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(POSTGRES.COLUMN_QUERY)
                rows = cursor.fetchall()

        columns = []
        for row in rows:
            columns.append(
                {
                    "database_name": row[0],
                    "schema_name": row[1],
                    "table_name": row[2],
                    "column_name": row[3],
                    "data_type": row[4],
                    "max_length": row[5],
                    "numeric_precision": row[6],
                    "numeric_scale": row[7],
                }
            )
        return columns


def get_postgres_connection_kwargs(db_name="postgres"):
    return POSTGRES.get_connection_kwargs(db_name)


def get_databases():
    return POSTGRES.get_databases()


def fetch_columns_for_database(db_name):
    return POSTGRES.fetch_columns_for_database(db_name)
