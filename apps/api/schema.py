"""OpenAPI annotations for API viewsets."""

from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view

from apps.api.serializers import DataTypeQuerySerializer, DataTypeResponseSerializer
from apps.api.serializers import KPIQuerySerializer, KPIResponseSerializer
kpi_viewset_schema = extend_schema_view(
    query=extend_schema(
        tags=['KPIs'],
        summary='Query ClickHouse for chart axes',
        description=(
            'Submit a table, dimension and aggregate measure without saving a dataset. '
            'x contains dimensions and y contains their aggregate values at matching indexes. '
            'Results are ordered by dimension. Unqualified columns use the main table; '
            'source.column and joined.column select the main or optional joined table. '
            'An empty measure is allowed only for count. Requires an authenticated admin. '
            'The default limit is 100 groups, maximum 1000. Empty results return empty axes. '
            'ClickHouse JSON encoding may represent large integers as strings.'
        ),
        request=KPIQuerySerializer,
        responses={200: KPIResponseSerializer, 400: {
            'description': 'Field validation errors or success=false with empty axes and a generic message.'
        }},
        examples=[
            OpenApiExample('Request', request_only=True, value={
                'table_name': 'orders', 'dimension': 'country',
                'measure': 'amount', 'aggregation': 'sum', 'limit': 100,
            }),
            OpenApiExample('Chart axes', response_only=True, status_codes=['200'], value={
                'success': True, 'x': ['Germany', 'US'], 'y': [350, 1200],
            }),
        ],
        filters=False,
    ),
)


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
