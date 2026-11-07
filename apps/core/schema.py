"""OpenAPI schema annotations for the API."""

from drf_spectacular.utils import (
    OpenApiExample,
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

connect_viewset_schema = extend_schema_view(
    create=extend_schema(
        tags=["Connect"],
        summary="Create a Kafka Connect connector",
        description=(
            "Requires a JWT access token for a staff user. Send name, db_type, "
            "and a nested config object using dotted Kafka Connect property names. "
            "Successful creation returns HTTP 201. "
            "Inspect message for created, not_configured, upstream_error, or unavailable. "
            "Rejected requests return HTTP 400, missing resources 404, conflicts 409, upstream failures 502, and unavailable or unconfigured services 503."
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
            201: {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Service result or upstream error message."},
                    "error_code": {"type": "integer", "description": "Error code when supplied by Kafka Connect."},
                },
                "additionalProperties": True,
                "description": "Service result or upstream Kafka Connect error JSON.",
            },
            400: {"type": "object", "additionalProperties": True, "description": "Serializer validation errors or a rejected connector request."},
            **{code: {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]} for code in (404, 409, 502, 503)},
            401: connect_detail_response,
            403: connect_detail_response,
        },
        filters=False,
    ),
)
