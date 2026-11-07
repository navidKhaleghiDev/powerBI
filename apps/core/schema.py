"""OpenAPI schema annotations for the API."""

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.core.serializers import (
    AnalyticDatabaseSerializer,
    NoSqlDatabaseSerializer,
    SqlDatabaseSerializer,
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


sql_database_viewset_schema = extend_schema_view(
    list=extend_schema(
        tags=["SQL databases"],
        summary="List SQL databases",
        description=(
            "Return stored SQL database types ordered by name. "
            "Each entry contains id and name. Authentication is not required. "
            "Only entries saved in the catalog are returned."
        ),
        responses={200: SqlDatabaseSerializer(many=True)},
        filters=False,
    ),
    retrieve=extend_schema(
        tags=["SQL databases"],
        summary="Retrieve a SQL database",
        description=(
            "Return a stored SQL database type by its id. "
            "The entry contains id and name. Authentication is not required."
        ),
        responses={
            200: SqlDatabaseSerializer,
            404: OpenApiResponse(description="No database type exists with this id."),
        },
        filters=False,
    ),
)


analytic_database_viewset_schema = extend_schema_view(
    list=extend_schema(
        tags=["Analytic databases"],
        summary="List analytic databases",
        description=(
            "Return stored analytic database types ordered by name. "
            "Each entry contains id and name. Authentication is not required. "
            "Only entries saved in the catalog are returned."
        ),
        responses={200: AnalyticDatabaseSerializer(many=True)},
        filters=False,
    ),
    retrieve=extend_schema(
        tags=["Analytic databases"],
        summary="Retrieve a analytic database",
        description=(
            "Return a stored analytic database type by its id. "
            "The entry contains id and name. Authentication is not required."
        ),
        responses={
            200: AnalyticDatabaseSerializer,
            404: OpenApiResponse(description="No database type exists with this id."),
        },
        filters=False,
    ),
)


no_sql_database_viewset_schema = extend_schema_view(
    list=extend_schema(
        tags=["NoSQL databases"],
        summary="List NoSQL databases",
        description=(
            "Return stored NoSQL database types ordered by name. "
            "Each entry contains id and name. Authentication is not required. "
            "Only entries saved in the catalog are returned."
        ),
        responses={200: NoSqlDatabaseSerializer(many=True)},
        filters=False,
    ),
    retrieve=extend_schema(
        tags=["NoSQL databases"],
        summary="Retrieve a NoSQL database",
        description=(
            "Return a stored NoSQL database type by its id. "
            "The entry contains id and name. Authentication is not required."
        ),
        responses={
            200: NoSqlDatabaseSerializer,
            404: OpenApiResponse(description="No database type exists with this id."),
        },
        filters=False,
    ),
)
