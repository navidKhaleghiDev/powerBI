from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.api.filterset.database_catalog_filter import DatabaseCatalogFilter
from apps.api.schema import data_type_viewset_schema
from apps.api.serializers import DataTypeQuerySerializer
from apps.core.choices import DatabaseType
from apps.core.models import DatabaseCatalog
from apps.core.schema import database_catalog_viewset_schema
from apps.core.serializers import DatabaseCatalogSerializer
from utils.data_types import ClickHouseDataType, PostgresDataType
from utils.pagination import DatabaseTypePagination


@database_catalog_viewset_schema
class DatabaseCatalogViewSet(GenericViewSet, ListModelMixin):
    queryset = DatabaseCatalog.objects.order_by("db_type", "id")
    serializer_class = DatabaseCatalogSerializer
    pagination_class = DatabaseTypePagination
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DatabaseCatalogFilter
    search_fields = ["db_type"]


@data_type_viewset_schema
class DataTypeViewSet(ListModelMixin, GenericViewSet):
    serializer_class = DataTypeQuerySerializer
    pagination_class = None
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]
    filter_backends = []

    def list(self, request, *args, **kwargs):
        return Response(self.get_queryset())

    def get_queryset(self):
        query = self.get_serializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        data_type_choices = {
            DatabaseType.POSTGRESQL.value: PostgresDataType,
            DatabaseType.CLICKHOUSE.value: ClickHouseDataType,
        }
        data_type_class = data_type_choices[query.validated_data["db_type"]]
        return [
            {"name": "smallint", "value": data_type_class.SMALLINT},
            {"name": "integer", "value": data_type_class.INTEGER},
            {"name": "bigint", "value": data_type_class.BIGINT},
            {"name": "real", "value": data_type_class.REAL},
            {"name": "double_precision", "value": data_type_class.DOUBLE_PRECISION},
            {"name": "boolean", "value": data_type_class.BOOLEAN},
            {"name": "character", "value": data_type_class.CHARACTER},
            {"name": "character_varying", "value": data_type_class.CHARACTER_VARYING},
            {"name": "text", "value": data_type_class.TEXT},
            {"name": "bytea", "value": data_type_class.BYTEA},
            {"name": "uuid", "value": data_type_class.UUID},
            {"name": "json", "value": data_type_class.JSON},
            {"name": "jsonb", "value": data_type_class.JSONB},
            {"name": "date", "value": data_type_class.DATE},
            {
                "name": "time_without_time_zone",
                "value": data_type_class.TIME_WITHOUT_TIME_ZONE,
            },
            {
                "name": "time_with_time_zone",
                "value": data_type_class.TIME_WITH_TIME_ZONE,
            },
            {"name": "interval", "value": data_type_class.INTERVAL},
            {"name": "xml", "value": data_type_class.XML},
            {"name": "inet", "value": data_type_class.INET},
            {"name": "cidr", "value": data_type_class.CIDR},
            {"name": "macaddr", "value": data_type_class.MACADDR},
            {"name": "macaddr8", "value": data_type_class.MACADDR8},

        ]
