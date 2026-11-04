from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api.schema import database_viewset_schema
from apps.api.serializers import DatabaseColumnsQuerySerializer, DatabaseConnectionQuerySerializer
from apps.api.service.database_service import DatabaseServiceFactory


@database_viewset_schema
class DatabaseViewSet(viewsets.GenericViewSet):
    serializer_class = DatabaseConnectionQuerySerializer
    http_method_names = ["post", "options"]

    @action(detail=False, methods=["post"], url_path="columns")
    def columns(self, request):
        query = DatabaseColumnsQuerySerializer(data=request.data)
        query.is_valid(raise_exception=True)
        connection_data = dict(query.validated_data)
        table = connection_data.pop("table")
        service = DatabaseServiceFactory.get_service(**connection_data)
        if not service:
            return Response(
                {"error": f"Unsupported database type: {connection_data['db_type']}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = service.get_columns(table)
        return Response(result, status=status.HTTP_200_OK if result["success"] else status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=["post"], url_path="connection-test")
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
