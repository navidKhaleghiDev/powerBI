from rest_framework.permissions import AllowAny
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from utils.pagination import DatabaseTypePagination
from apps.core.models import AnalyticDatabase, NoSqlDatabase, SqlDatabase
from apps.core.schema import analytic_database_viewset_schema, no_sql_database_viewset_schema, sql_database_viewset_schema
from apps.core.serializers import AnalyticDatabaseSerializer, NoSqlDatabaseSerializer, SqlDatabaseSerializer


@sql_database_viewset_schema
class SqlDatabaseViewSet(ListModelMixin, GenericViewSet):
    queryset = SqlDatabase.objects.order_by("name")
    serializer_class = SqlDatabaseSerializer
    pagination_class = DatabaseTypePagination
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]


@analytic_database_viewset_schema
class AnalyticDatabaseViewSet(ListModelMixin, GenericViewSet):
    queryset = AnalyticDatabase.objects.order_by("name")
    serializer_class = AnalyticDatabaseSerializer
    pagination_class = DatabaseTypePagination
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]


@no_sql_database_viewset_schema
class NoSqlDatabaseViewSet(ListModelMixin, GenericViewSet):
    queryset = NoSqlDatabase.objects.order_by("name")
    serializer_class = NoSqlDatabaseSerializer
    pagination_class = DatabaseTypePagination
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]
