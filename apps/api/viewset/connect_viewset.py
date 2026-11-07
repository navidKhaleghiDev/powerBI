from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.core.schema import connect_viewset_schema
from apps.core.serializers import CreateConnectorSerializer
from apps.core.service.connect_service import ConnectService


@connect_viewset_schema
class ConnectViewSet(viewsets.GenericViewSet, viewsets.mixins.CreateModelMixin):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = CreateConnectorSerializer

    def list(self, request):
        """Return all connector names from Kafka Connect."""
        result, response_status = ConnectService().list_connectors()
        return Response(result, status=response_status)

    def create(self, request):
        """Validate connector settings and return the service result."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result, response_status = ConnectService().create_connector(**serializer.validated_data)
        # Preserve the status selected by the service, including upstream failures.
        return Response(result, status=response_status)

    
