"""OpenAPI schema annotations for the database API."""

from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    extend_schema_view,
)

from apps.api.serializers import (
    DatabaseTablesResponseSerializer,
    DatabaseConnectionQuerySerializer,
    DatabaseConnectionResponseSerializer,
)


database_viewset_schema = extend_schema_view(
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
                    "db_type": "postgres",
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
