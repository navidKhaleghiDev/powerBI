from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from apps.api.schema import kpi_dashboard_schema, kpi_viewset_schema
from apps.api.serializers import (
    DashboardCreateSerializer, DashboardResponseSerializer, KPIChartQuerySerializer, KPIQuerySerializer,
)
from apps.kpi.models import Dashboard, KPIChart
from apps.kpi.service.kpi_service import KPIService
from utils.exceptions import ChartQueryFailed, KPIUnavailable


@kpi_viewset_schema
@kpi_dashboard_schema
class KPIViewSet(viewsets.GenericViewSet):
    serializer_class = KPIQuerySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    http_method_names = ['get', 'post', 'options']

    def get_dashboards(self):
        return Dashboard.objects.filter(owner=self.request.user).prefetch_related('charts__filters').order_by('pk')

    @action(detail=False, methods=['get'], url_path='dashboards', serializer_class=DashboardResponseSerializer)
    def dashboards(self, request):
        return Response(DashboardResponseSerializer(self.get_dashboards(), many=True).data)

    @action(detail=False, methods=['post'], url_path='create-dashboard',
            serializer_class=DashboardCreateSerializer)
    def create_dashboard(self, request):
        options = DashboardCreateSerializer(data=request.data)
        options.is_valid(raise_exception=True)
        try:
            dashboard = KPIService().create_dashboard(request.user, options.validated_data)
        except ChartQueryFailed as exc:
            return Response(
                {'success': False, 'chart_index': exc.chart_index, 'message': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        dashboard = self.get_dashboards().get(pk=dashboard.pk)
        return Response(DashboardResponseSerializer(dashboard).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path=r'dashboards/(?P<dashboard_id>[0-9]+)',
            serializer_class=DashboardResponseSerializer)
    def dashboard(self, request, dashboard_id=None):
        dashboard = get_object_or_404(self.get_dashboards(), pk=dashboard_id)
        return Response(DashboardResponseSerializer(dashboard).data)

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

    @action(detail=False, methods=['post'], url_path='chart-query', serializer_class=KPIChartQuerySerializer)
    def chart_query(self, request):
        # TODO
        # options = self.get_serializer(data=request.data)
        # options.is_valid(raise_exception=True)
        # chart = get_object_or_404(
        #     KPIChart.objects.filter(dashboard__owner=request.user).prefetch_related('filters'),
        #     pk=options.validated_data['chart_id'],
        # )
        # config = KPIService.chart_config(chart)
        # if 'limit' in options.validated_data:
        #     config['limit'] = options.validated_data['limit']
        # query = KPIQuerySerializer(data=config)
        # query.is_valid(raise_exception=True)
        # config = dict(query.validated_data)
        # limit = config.pop('limit')
        # result = KPIService().execute(config, limit)
        # return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)

