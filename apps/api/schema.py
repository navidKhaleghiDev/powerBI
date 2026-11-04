"""OpenAPI schema annotations for the database API."""

from drf_spectacular.utils import (
    OpenApiParameter,
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)

from apps.api.serializers import (
    DatabaseColumnsResponseSerializer,
    DatabaseErrorSerializer,
    DatabaseListResponseSerializer,
)


database_viewset_schema = extend_schema_view(
    retrieve=extend_schema(exclude=True),
    databases=extend_schema(
        tags=["Database"],
        summary="List PostgreSQL databases",
        responses={200: DatabaseListResponseSerializer, 400: DatabaseErrorSerializer},
        filters=False,
    ),
    columns=extend_schema(
        tags=["Database"],
        summary="List columns in a database",
        parameters=[OpenApiParameter("database", str, required=True, description="Database name.")],
        responses={200: DatabaseColumnsResponseSerializer, 400: DatabaseErrorSerializer},
        filters=False,
    ),
    list=extend_schema(
        tags=["Database"],
        summary="List databases or database columns",
        description="Returns databases when database is omitted; otherwise returns columns for that database.",
        parameters=[OpenApiParameter("database", str, required=False, description="Database to inspect.")],
        responses={
            200: PolymorphicProxySerializer(
                component_name="DatabaseMetadataResponse",
                serializers=[DatabaseListResponseSerializer, DatabaseColumnsResponseSerializer],
                resource_type_field_name=None,
            ),
            400: DatabaseErrorSerializer,
        },
        filters=False,
    ),
)
