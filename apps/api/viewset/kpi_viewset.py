from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from apps.api.schema import kpi_viewset_schema
from apps.api.serializers import KPIDataSetQuerySerializer, KPIQuerySerializer
from apps.kpi.models import DataSet
from apps.kpi.service.kpi_service import KPIService, KPIUnavailable


@kpi_viewset_schema
class KPIViewSet(viewsets.GenericViewSet):
    serializer_class = KPIQuerySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    renderer_classes = [JSONRenderer]
    http_method_names = ['get', 'post', 'options']

    @action(detail=False, methods=['get'], url_path='available-tables')
    def available_tables(self, request):
        try:
            tables = KPIService().get_available_tables()
        except KPIUnavailable as exc:
            return Response(
                {'success': False, 'tables': [], 'message': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({'success': True, 'tables': tables})

    @action(detail=False, methods=['post'])
    def query(self, request):
        options = self.get_serializer(data=request.data)
        options.is_valid(raise_exception=True)
        config = dict(options.validated_data)
        limit = config.pop('limit')
        result = KPIService().execute(config, limit)
        return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)

