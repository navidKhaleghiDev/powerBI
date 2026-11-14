import json

import clickhouse_connect
from clickhouse_connect.driver.exceptions import Error
from django.conf import settings

from utils.consumers import quote_identifier


class KPIUnavailable(RuntimeError):
    """ClickHouse could not provide KPI source metadata."""


class KPIService:
    @staticmethod
    def client():
        return clickhouse_connect.get_client(
            host=settings.CONSUMER_HOST,
            port=settings.CONSUMER_PORT,
            username=settings.CONSUMER_USER,
            password=settings.CONSUMER_PASSWORD,
            database=settings.CONSUMER_DATABASE,
            connect_timeout=5,
            send_receive_timeout=30,
        )

    def get_available_tables(self):
        """Return queryable KPI tables and their columns from ClickHouse."""

        query = """
                SELECT
                    t.name,
                    t.engine,
                    c.name,
                    c.type
                FROM system.tables AS t
                INNER JOIN system.columns AS c
                    ON t.database = c.database
                    AND t.name = c.table
                WHERE
                    t.database = {database:String}
                    AND t.is_temporary = 0
                    AND (
                        endsWith(t.engine, 'MergeTree')
                        OR t.engine IN ('View', 'Distributed')
                    )
                ORDER BY t.name, c.position
            """
        try:
            with self.client() as client:
                rows = client.query(
                    query,
                    parameters={
                        "database": settings.CONSUMER_DATABASE
                    },
                    settings={
                        "readonly": 1,
                        "max_execution_time": 20,
                    },
                ).result_rows
        except Error:
            raise KPIUnavailable("Unable to retrieve available ClickHouse KPI tables.") from None

        tables = {}

        for table, engine, column, kind in rows:

            if table.endswith(("_raw", "_kafka", "_mv")):
                continue

            source = tables.setdefault(
                table,
                {
                    "name": table,
                    "engine": engine,
                    "columns": [],
                },
            )

            source["columns"].append({
                "name": column,
                "type": kind,
            })

        return list(tables.values())

    @staticmethod
    def quote_table(value):
        return '.'.join(quote_identifier(part) for part in value.split('.'))

    @staticmethod
    def quote_column(value):
        alias, name = value.split('.', 1) if '.' in value else ('source', value)
        return f'{quote_identifier(alias)}.{quote_identifier(name)}'

    @staticmethod
    def build_where(filters):
        operators = {
            'eq': '=', 'ne': '!=', 'gt': '>', 'gte': '>=', 'lt': '<',
            'lte': '<=', 'in': 'IN', 'not_in': 'NOT IN', 'like': 'LIKE',
            'is_null': 'IS NULL', 'is_not_null': 'IS NOT NULL',
        }
        conditions = []
        parameters = {}
        for index, item in enumerate(filters):
            column = KPIService.quote_column(item['column'])
            operator = operators[item['operator']]
            if item['operator'] in ('is_null', 'is_not_null'):
                conditions.append(f'{column} {operator}')
            else:
                key = f'filter_{index}'
                value = item['value']
                parameters[key] = tuple(value) if item['operator'] in ('in', 'not_in') else value
                conditions.append(f'{column} {operator} %({key})s')
        return (' WHERE ' + ' AND '.join(conditions) if conditions else ''), parameters

    @staticmethod
    def build_query(config, limit):
        dimension = KPIService.quote_column(config['dimension'])
        measure = KPIService.quote_column(config['measure']) if config.get('measure') else '*'
        query = (
            f"SELECT {dimension} AS dimension, {config['aggregation']}({measure}) AS value "
            f"FROM {KPIService.quote_table(config['table_name'])} AS source"
        )
        if config.get('join_table_name'):
            query += (
                f" {config['join_type']} JOIN {KPIService.quote_table(config['join_table_name'])} AS joined"
                f" ON source.{quote_identifier(config['join_left_column'])}"
                f" = joined.{quote_identifier(config['join_right_column'])}"
            )
        where, _ = KPIService.build_where(config.get('filters', []))
        return query + where + f' GROUP BY {dimension} ORDER BY {dimension} LIMIT {limit}'

    def execute(self, config, limit):
        query = self.build_query(config, limit)
        _, parameters = self.build_where(config.get('filters', []))
        try:
            with self.client() as client:
                result = json.loads(client.raw_query(
                    query, fmt='JSON', parameters=parameters,
                    settings={'readonly': 1, 'max_execution_time': 20},
                ))
            return {
                'success': True,
                'x': [row['dimension'] for row in result['data']],
                'y': [row['value'] for row in result['data']],
            }
        except Error:
            return {'success': False, 'x': [], 'y': [], 'message': 'Unable to execute the ClickHouse KPI query.'}
