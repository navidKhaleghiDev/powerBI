"""OpenAPI annotations for API viewsets."""

from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.api.serializers import DataTypeQuerySerializer, DataTypeResponseSerializer


data_type_viewset_schema = extend_schema_view(
    list=extend_schema(
        tags=["Database types"],
        summary="List data types for a database backend",
        description=(
            "Returns database type entries in declaration order. Each entry contains a "
            "lowercase identifier in `name` and the backend type string in `value`. "
            "Results are not paginated. Authentication is not required."
        ),
        parameters=[DataTypeQuerySerializer],
        responses={
            200: DataTypeResponseSerializer(many=True),
            400: {
                "type": "object",
                "properties": {
                    "db_type": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        filters=False,
    ),
)
