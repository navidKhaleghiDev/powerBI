import json

import clickhouse_connect
from clickhouse_connect.driver.exceptions import Error
from django.conf import settings

from utils.consumers import quote_identifier


class KPIService:
    @staticmethod
    def build_query(config, limit):
    
        def table(value):
            return '.'.join(quote_identifier(part) for part in value.split('.'))

        def column(value):
            alias, name = value.split('.', 1) if '.' in value else ('source', value)
            return f'{quote_identifier(alias)}.{quote_identifier(name)}'

        dimension = column(config['dimension'])
        measure = column(config['measure']) if config.get('measure') else '*'
        query = (
            f"SELECT {dimension} AS dimension, {config['aggregation']}({measure}) AS value "
            f"FROM {table(config['table_name'])} AS source"
        )
        if config.get('join_table_name'):
            query += (
                f" {config['join_type']} JOIN {table(config['join_table_name'])} AS joined"
                f" ON source.{quote_identifier(config['join_left_column'])}"
                f" = joined.{quote_identifier(config['join_right_column'])}"
            )
        return query + f' GROUP BY {dimension} ORDER BY {dimension} LIMIT {limit}'

    def execute(self, config, limit):
        query = self.build_query(config, limit)
        try:
            with clickhouse_connect.get_client(
                host=settings.CONSUMER_HOST,
                port=settings.CONSUMER_PORT,
                username=settings.CONSUMER_USER,
                password=settings.CONSUMER_PASSWORD,
                database=settings.CONSUMER_DATABASE,
                connect_timeout=5,
                send_receive_timeout=30,
            ) as client:
                result = json.loads(client.raw_query(
                    query, fmt='JSON',
                    settings={'readonly': 1, 'max_execution_time': 20},
                ))
            return {
                'success': True,
                'x': [row['dimension'] for row in result['data']],
                'y': [row['value'] for row in result['data']],
            }
        except Error:
            return {'success': False, 'x': [], 'y': [], 'message': 'Unable to execute the ClickHouse KPI query.'}
