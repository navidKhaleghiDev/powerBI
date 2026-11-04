from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api.models import DatabaseMetadata
from apps.api.schema import database_viewset_schema
from apps.api.serializers import DatabaseMetadataSerializer
from apps.api.service.database_service import DatabaseServiceFactory


@database_viewset_schema
class DatabaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DatabaseMetadata.objects.none()
    serializer_class = DatabaseMetadataSerializer
    http_method_names = ["get"]

    @action(detail=False, methods=["get"], url_path="databases")
    def databases(self, request):
        try:
            service = DatabaseServiceFactory.create("postgres")
            return Response({"databases": service.get_databases()})
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="columns")
    def columns(self, request):
        database = request.query_params.get("database")
        if not database:
            return Response({"error": "The 'database' query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = DatabaseServiceFactory.create("postgres")
            return Response({"database": database, "columns": service.fetch_columns_for_database(database)})
        except Exception as exc:

            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        database = request.query_params.get("database")
        if database:
            return self.columns(request)
        return self.databases(request)
