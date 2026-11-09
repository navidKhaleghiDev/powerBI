"""OpenAPI schema annotations for the API."""

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers

from apps.api.serializers import ConsumerResponseSerializer, ConsumerSerializer

from apps.core.serializers import (
    CreateConnectorSerializer,
    DatabaseCatalogSerializer,
    DatabaseColumnsQuerySerializer,
    DatabaseColumnsResponseSerializer,
    DatabaseTablesResponseSerializer,
    DatabaseConnectionQuerySerializer,
    DatabaseConnectionResponseSerializer,
)

token_view_schema = extend_schema_view(post=extend_schema(tags=["token"]))

database_viewset_schema = extend_schema_view(
    columns=extend_schema(
        tags=["Database"],
        summary="List columns for a table",
        description="Send connection credentials and a schema-qualified table name such as public.orders in the POST body.",
        request=DatabaseColumnsQuerySerializer,
        responses={200: DatabaseColumnsResponseSerializer, 400: DatabaseColumnsResponseSerializer},
        filters=False,
    ),
    tables=extend_schema(
        tags=["Database"],
        summary="List tables and their columns",
        description="Lists accessible user tables and views, grouped by schema and table. System schemas are excluded.",
        request=DatabaseConnectionQuerySerializer,
        responses={200: DatabaseTablesResponseSerializer, 400: DatabaseTablesResponseSerializer},
        filters=False,
    ),
    connection_test=extend_schema(
        tags=["Database"],
        summary="Test a PostgreSQL connection",
        description=(
            "Connect using the credentials supplied in the request body. "
            "Valid db_type choices: "
            + ", ".join(DatabaseConnectionQuerySerializer().fields["db_type"].choices)
            + ". Only PostgreSQL connection testing is currently implemented."
        ),
        request=DatabaseConnectionQuerySerializer,
        examples=[
            OpenApiExample(
                "PostgreSQL connection",
                value={
                    "db_type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "database": "bi",
                    "username": "postgres",
                    "password": "your-password",
                },
                request_only=True,
            ),
        ],
        responses={200: DatabaseConnectionResponseSerializer, 400: DatabaseConnectionResponseSerializer},
        filters=False,
    ),
)

database_catalog_viewset_schema = extend_schema_view(
    list=extend_schema(
        tags=["Database types"],
        summary="List database types",
        description=(
            "List stored database types with id, db_type, category, and image URL. "
            "Filter by category (sql, analytic, nosql) or exact db_type; search by db_type. "
            "Order by db_type, category, or id, using a minus prefix for descending order. "
            "Results contain 20 entries per page. Authentication is not required."
        ),
        responses={200: DatabaseCatalogSerializer(many=True)},
        filters=True,
    ),
)

connect_detail_response = inline_serializer(
    name="ConnectDetailResponse",
    fields={"detail": serializers.CharField()},
)

connect_message_response = inline_serializer(
    name="ConnectMessageResponse",
    fields={"message": serializers.CharField()},
)

connect_error_response = inline_serializer(
    name="ConnectErrorResponse",
    fields={"error": serializers.CharField()},
)

connect_auth_responses = {401: connect_detail_response, 403: connect_detail_response}

connect_viewset_schema = extend_schema_view(
    delete_connector=extend_schema(
        tags=["Connect"],
        summary="Delete a Kafka Connect connector",
        description="Requires a JWT access token for a staff user. Deletes the named connector from Kafka Connect and returns HTTP 204 with no response body.",
        parameters=[OpenApiParameter("name", OpenApiTypes.STR, OpenApiParameter.PATH, description="Connector name.")],
        request=None,
        responses={
            204: None,
            **connect_auth_responses,
        },
        filters=False,
    ),
    connector_config=extend_schema(
        tags=["Connect"],
        summary="Get connector configuration",
        description="Staff users only. Fetches connector configuration by source name through the Debezium UI proxy at /api/connectors/1/{source}/config. Sensitive properties are redacted.",
        parameters=[OpenApiParameter("source", OpenApiTypes.STR, OpenApiParameter.PATH, description="Kafka Connect connector name.", required=True)],
        responses={
            200: {"type": "object", "additionalProperties": {"type": "string"}},
            **connect_auth_responses,
        },
        filters=False,
    ),
    list=extend_schema(
        tags=["Connect"],
        summary="List Kafka Connect connectors",
        description="Requires a JWT access token for a staff user. Returns all connector names from the configured Kafka Connect service.",
        responses={
            200: {"type": "array", "items": {"type": "string"}},
            **connect_auth_responses,
        },
        filters=False,
    ),
    create=extend_schema(
        tags=["Connect"],
        summary="Create a Kafka Connect connector",
        description=(
            "Staff users only. Send name, db_type, and config with dotted Kafka Connect "
            "property names. Returns 201 when created."
        ),
        request=CreateConnectorSerializer,
        examples=[
            OpenApiExample(
                "PostgreSQL connector",
                request_only=True,
                value={
                    "name": "orders-connector",
                    "db_type": "postgresql",
                    "config": {
                        "database.hostname": "postgres",
                        "database.port": 5432,
                        "database.user": "replicator",
                        "database.password": "your-password",
                        "database.dbname": "bi",
                        "topic.prefix": "bi",
                        "slot.name": "orders_slot",
                        "publication.name": "orders_publication",
                        "table.include.list": "public.orders",
                    },
                },
            ),
            OpenApiExample(
                "Connector created",
                value={"message": "created"},
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "Kafka Connect unavailable",
                value={"message": "unavailable"},
                response_only=True,
                status_codes=["503"],
            ),
        ],
        responses={
            201: connect_message_response,
            400: OpenApiTypes.OBJECT,
            404: connect_error_response,
            409: connect_error_response,
            502: connect_error_response,
            503: connect_message_response,
            **connect_auth_responses,
        },
        filters=False,
    ),
)

consumer_viewset_schema = extend_schema_view(
    create=extend_schema(
        tags=['Consumer'],
        summary='Create mapped ClickHouse tables and Kafka consumers',
        description=(
            'Staff users only. Send warehouse_name, table.include.list, topic.prefix, and tables with source_table, '
            'target_table, columns (source/target/type), and order_by using target column names. '
            'Topics are derived as prefix.source_table. Kafka columns use source names; raw and current '
            'columns use target names. The database must already exist. CDC metadata is added automatically. '
            'Existing objects are preserved. DDL is not transactional; failures may leave partial objects.'
            ' Each target creates _raw, _current, _kafka, _current_mv, and _mv objects. '
            'order_by must identify the row using non-nullable target columns. '
            'Source tables must match the comma-separated literal table.include.list exactly. '
            'Requires a JWT access token belonging to a staff user.'
            ' db_type selects the destination backend and defaults to clickhouse; '
            'other backends return HTTP 400 without provisioning objects.'
        ),
        request=ConsumerSerializer,
        examples=[
            OpenApiExample(
                'Map orders to sales',
                request_only=True,
                value={
                    'warehouse_name': 'financial_analytics',
                    'db_type': 'clickhouse',
                    'table.include.list': 'public.orders',
                    'topic.prefix': 'bi',
                    'tables': [{
                        'source_table': 'public.orders',
                        'target_table': 'sales',
                        'columns': [
                            {'source': 'id', 'target': 'record_id', 'type': 'Int32'},
                            {'source': 'customer_name', 'target': 'client_name', 'type': 'Nullable(String)'},
                        ],
                        'order_by': ['record_id'],
                    }],
                },
            ),
            OpenApiExample(
                'Consumer provisioned', response_only=True, status_codes=['200', '201'],
                value={'success': True, 'database': 'financial_analytics', 'tables': ['sales']},
            ),
            OpenApiExample(
                'Provisioning failed', response_only=True, status_codes=['400'],
                value={
                    'success': False, 'database': 'financial_analytics', 'tables': [],
                    'message': 'Unable to provision the consumer pipeline. Partial objects may exist.',
                },
            ),
            OpenApiExample(
                'Invalid table mapping', response_only=True, status_codes=['400'],
                value={'tables': ['source_table entries must match table.include.list exactly.']},
            ),
            OpenApiExample(
                'Authentication required', response_only=True, status_codes=['401'],
                value={'detail': 'Authentication credentials were not provided.'},
            ),
        ],
        responses={
            200: OpenApiResponse(ConsumerResponseSerializer, description='Provisioned or already existing objects; tables lists completed target names.'),
            201: OpenApiResponse(ConsumerResponseSerializer, description='Consumer created (reserved; provisioning currently returns 200).'),
            400: OpenApiResponse(
                response={'oneOf': [
                    {'$ref': '#/components/schemas/ConsumerResponse'},
                    {'type': 'object', 'additionalProperties': {}, 'description': 'DRF field or non-field validation errors.'},
                ]},
                description='Validation errors or a sanitized provisioning failure. Partial objects may exist.',
            ),
            401: OpenApiResponse(connect_detail_response, description='JWT access token missing or invalid.'),
        },
        filters=False,
    ),
)
