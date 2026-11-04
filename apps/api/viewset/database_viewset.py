from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api.models import DatabaseMetadata
from apps.api.schema import database_viewset_schema
from apps.api.serializers import DatabaseConnectionQuerySerializer, DatabaseMetadataSerializer
from apps.api.service.database_service import DatabaseServiceFactory
from apps.core.models import DataBase


@database_viewset_schema
class DatabaseViewSet(viewsets.GenericViewSet):
    queryset = DatabaseMetadata.objects.none()
    serializer_class = DatabaseMetadataSerializer
    http_method_names = ["post", "options"]

    @action(detail=False, methods=["post"], url_path="databases")
    def connection_test(self, request):
        query = DatabaseConnectionQuerySerializer(data=request.data)
        query.is_valid(raise_exception=True)
        service = DatabaseServiceFactory.get_service(**query.validated_data)
        if not service:
            return Response(
                {"error": f"Unsupported database type: {query.validated_data['db_type']}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = service.connection_test()
        if result["success"]:
            DataBase.objects.get_or_create(
                **{key: value for key, value in query.validated_data.items() if key != "password"}
            )
        return Response(result, status=status.HTTP_200_OK if result["success"] else status.HTTP_400_BAD_REQUEST)



    @action(detail=False, methods=["post"], url_path="tables")
    def tables(self, request):
        query = DatabaseConnectionQuerySerializer(data=request.data)
        query.is_valid(raise_exception=True)
        service = DatabaseServiceFactory.get_service(**query.validated_data)
        if not service:
            return Response(
                {"error": f"Unsupported database type: {query.validated_data['db_type']}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = service.get_tables()
        return Response(result, status=status.HTTP_200_OK if result["success"] else status.HTTP_400_BAD_REQUEST)
