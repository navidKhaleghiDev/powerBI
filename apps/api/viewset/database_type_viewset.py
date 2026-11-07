from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.models import AnalyticDatabase, NoSqlDatabase, SqlDatabase
from apps.core.schema import analytic_database_viewset_schema, no_sql_database_viewset_schema, sql_database_viewset_schema
from apps.core.serializers import AnalyticDatabaseSerializer, NoSqlDatabaseSerializer, SqlDatabaseSerializer


@sql_database_viewset_schema
class SqlDatabaseViewSet(ReadOnlyModelViewSet):
    queryset = SqlDatabase.objects.order_by("name")
    serializer_class = SqlDatabaseSerializer
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]


@analytic_database_viewset_schema
class AnalyticDatabaseViewSet(ReadOnlyModelViewSet):
    queryset = AnalyticDatabase.objects.order_by("name")
    serializer_class = AnalyticDatabaseSerializer
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]


@no_sql_database_viewset_schema
class NoSqlDatabaseViewSet(ReadOnlyModelViewSet):
    queryset = NoSqlDatabase.objects.order_by("name")
    serializer_class = NoSqlDatabaseSerializer
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]
