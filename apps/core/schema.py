"""OpenAPI schema annotations for the API."""

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers

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
