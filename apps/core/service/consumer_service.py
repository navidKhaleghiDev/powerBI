import clickhouse_connect
from clickhouse_connect.driver.exceptions import Error
from django.conf import settings
from rest_framework import status

from apps.core.choices import DatabaseType

from apps.core.service.interface import ConsumerServiceInterface
from utils.consumers import quote_identifier


class ClickHouseConsumerService(ConsumerServiceInterface):
    """Provision validated client-defined CDC tables in an existing database."""

    @staticmethod
    def statements(database: str, table: dict) -> list[str]:
        raw, current, kafka, current_mv, ingest_mv = (
            f"{quote_identifier(database)}.{quote_identifier(table['target_table'] + suffix)}"
            for suffix in ('_raw', '_current', '_kafka', '_current_mv', '_mv')
        )
        columns = ', '.join(
            f"{quote_identifier(column['target'])} {column['type']}" for column in table['columns']
        )
        source_columns = ', '.join(
            f"{quote_identifier(column['source'])} {column['type']}" for column in table['columns']
        )
        mapping = ', '.join(
            f"{quote_identifier(column['source'])} AS {quote_identifier(column['target'])}"
            for column in table['columns']
        )
        names = ', '.join(quote_identifier(column['target']) for column in table['columns'])
        order_by = '(' + ', '.join(quote_identifier(key) for key in table['order_by']) + ')'
        metadata = "__deleted String DEFAULT 'false', __op String DEFAULT '', __lsn UInt64 DEFAULT 0"
        kafka_metadata = '__deleted String, __op String, __lsn UInt64'
        return [
            f'CREATE TABLE IF NOT EXISTS {raw} ({columns}, {metadata}) '
            f'ENGINE = MergeTree() ORDER BY {order_by}',
            f'CREATE TABLE IF NOT EXISTS {current} ({columns}, version UInt64, is_deleted UInt8) '
            f'ENGINE = ReplacingMergeTree(version) ORDER BY {order_by}',
            f'CREATE MATERIALIZED VIEW IF NOT EXISTS {current_mv} TO {current} AS '
            f"SELECT {names}, __lsn AS version, if(__deleted = 'true' OR __op = 'd', 1, 0) "
            f'AS is_deleted FROM {raw}',
            f'CREATE TABLE IF NOT EXISTS {kafka} ({source_columns}, {kafka_metadata}) ENGINE = Kafka SETTINGS '
            'kafka_broker_list = %(brokers)s, kafka_topic_list = %(topic)s, '
            "kafka_security_protocol = 'plaintext', "
            "kafka_group_name = %(group)s, kafka_format = 'JSONEachRow', "
            "date_time_input_format = 'best_effort', "
            'input_format_skip_unknown_fields = 1, kafka_num_consumers = 1',
            f'CREATE MATERIALIZED VIEW IF NOT EXISTS {ingest_mv} TO {raw} AS '
            f"SELECT {mapping}, if(__deleted = 'true' OR __op = 'd', 'true', 'false') AS __deleted, "
            f'__op, __lsn FROM {kafka}',
        ]

    def create(self, topic: str, tables: list[dict]) -> tuple[dict, int]:
        """Provision tables consuming topic.source_table for the supplied prefix."""
        database = settings.CONSUMER_DATABASE
        completed = []
        try:
            with clickhouse_connect.get_client(
                host=settings.CONSUMER_HOST,
                port=settings.CONSUMER_PORT,
                username=settings.CONSUMER_USER,
                password=settings.CONSUMER_PASSWORD,
                database=database,
                connect_timeout=5,
                send_receive_timeout=30,
            ) as client:
                for table in tables:
                    kafka_topic = f"{topic}.{table['source_table']}"
                    for statement in self.statements(database, table):
                        parameters = None
                        if '%(brokers)s' in statement:
                            parameters = {
                                'brokers': settings.CLICKHOUSE_KAFKA_BROKERS,
                                'topic': kafka_topic,
                                'group': f"clickhouse-{database}-{table['target_table']}-{kafka_topic}",
                            }
                        client.command(statement, parameters=parameters)
                    completed.append(table['target_table'])
        except Error as e:
            return {
                'success': False,
                'database': database,
                'tables': completed,
                'message': str(e),
            }, status.HTTP_400_BAD_REQUEST
        return {'success': True, 'database': database, 'tables': completed}, status.HTTP_200_OK


class ConsumerServiceFactory:
    """Select a consumer backend using the shared database choices."""

    @staticmethod
    def get_service(db_type: str) -> ConsumerServiceInterface | None:
        services = {
            DatabaseType.CLICKHOUSE: ClickHouseConsumerService,
        }
        service_class = services.get(db_type)
        return service_class() if service_class is not None else None
