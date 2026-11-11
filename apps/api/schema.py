"""OpenAPI annotations for API viewsets."""

from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view

# Governed analytics schemas live alongside the existing API annotations.
from apps.api.analytics_serializers import (
    AnalyticsDetailsSerializer,
    AnalyticsMetadataSerializer,
    AnalyticsQuerySerializer,
    AnalyticsResultSerializer,
    AnalyticsSourcesSerializer,
    DashboardSerializer,
    DatasetSerializer,
)

from apps.api.serializers import DataTypeQuerySerializer, DataTypeResponseSerializer
from apps.api.serializers import KPIQuerySerializer, KPIResponseSerializer

kpi_viewset_schema = extend_schema_view(
    query=extend_schema(
        tags=["KPIs"],
        summary="Query ClickHouse for chart axes",
        description=(
            "Submit a table, dimension and aggregate measure without saving a dataset. "
            "x contains dimensions and y contains their aggregate values at matching indexes. "
            "Results are ordered by dimension. Unqualified columns use the main table; "
            "source.column and joined.column select the main or optional joined table. "
            "An empty measure is allowed only for count. Requires an authenticated admin. "
            "The default limit is 100 groups, maximum 1000. Empty results return empty axes. "
            "ClickHouse JSON encoding may represent large integers as strings."
        ),
        request=KPIQuerySerializer,
        responses={
            200: KPIResponseSerializer,
            400: {
                "description": "Field validation errors or success=false with empty axes and a generic message."
            },
        },
        examples=[
            OpenApiExample(
                "Request",
                request_only=True,
                value={
                    "table_name": "orders",
                    "dimension": "country",
                    "measure": "amount",
                    "aggregation": "sum",
                    "limit": 100,
                },
            ),
            OpenApiExample(
                "Chart axes",
                response_only=True,
                status_codes=["200"],
                value={
                    "success": True,
                    "x": ["Germany", "US"],
                    "y": [350, 1200],
                },
            ),
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


analytics_dataset_viewset_schema = extend_schema_view(
    list=extend_schema(tags=["Analytics datasets"], responses=DatasetSerializer(many=True)),
    create=extend_schema(
        tags=["Analytics datasets"], request=DatasetSerializer, responses={201: DatasetSerializer}
    ),
    update=extend_schema(
        tags=["Analytics datasets"], request=DatasetSerializer, responses=DatasetSerializer
    ),
    preview=extend_schema(
        tags=["Analytics datasets"], request=None, responses=AnalyticsResultSerializer
    ),
    publish=extend_schema(tags=["Analytics datasets"], request=None, responses=DatasetSerializer),
    unpublish=extend_schema(tags=["Analytics datasets"], request=None, responses=DatasetSerializer),
    enable_history=extend_schema(
        tags=["Analytics datasets"], request=None, responses=DatasetSerializer
    ),
)


def analytics_viewset_schema(cls):
    cls = extend_schema_view(
        metadata=extend_schema(tags=["Analytics"], responses=AnalyticsMetadataSerializer),
        sources=extend_schema(tags=["Analytics"], responses=AnalyticsSourcesSerializer),
        query=extend_schema(
            tags=["Analytics"],
            request=AnalyticsQuerySerializer,
            responses=AnalyticsResultSerializer,
        ),
        details=extend_schema(
            tags=["Analytics"],
            request=AnalyticsDetailsSerializer,
            responses=AnalyticsResultSerializer,
        ),
        dashboard=extend_schema(tags=["Analytics"], methods=["GET"], responses=DashboardSerializer),
    )(cls)
    return extend_schema_view(
        dashboard=extend_schema(
            tags=["Analytics"],
            methods=["PUT"],
            request=DashboardSerializer,
            responses={200: DashboardSerializer},
        )
    )(cls)
