from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.api.analytics_serializers import (
    AnalyticsDetailsSerializer,
    AnalyticsQuerySerializer,
    DashboardSerializer,
    DatasetSerializer,
)
from apps.api.schema import analytics_dataset_viewset_schema, analytics_viewset_schema
from apps.kpi.models import AnalyticsDashboard, AnalyticsDataset
from apps.kpi.service.analytics_service import AnalyticsService
from apps.kpi.service.catalog import TEMPLATES


@analytics_dataset_viewset_schema
class AnalyticsDatasetViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    """Administrators configure draft mappings; publishing makes KPIs visible to signed-in users."""

    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = DatasetSerializer
    queryset = AnalyticsDataset.objects.prefetch_related("metrics")
    pagination_class = None
    http_method_names = ["get", "post", "put", "head", "options"]

    def update(self, request, pk=None):
        with transaction.atomic():
            dataset = AnalyticsDataset.objects.select_for_update().get(pk=self.get_object().pk)
            if dataset.status == "published" or dataset.published_at or dataset.history_table:
                return Response(
                    {
                        "detail": "Published or history-enabled definitions are immutable. Create a new dataset version."
                    },
                    status=409,
                )
            if request.data.get("revision") != dataset.revision:
                return Response({"detail": "Dataset changed. Reload before editing."}, status=409)
            serializer = self.get_serializer(dataset, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="enable-history")
    def enable_history(self, request, pk=None):
        with transaction.atomic():
            dataset = AnalyticsDataset.objects.select_for_update().get(pk=self.get_object().pk)
            if dataset.status != "draft" or dataset.published_at:
                return Response(
                    {"detail": "Enable history on a draft dataset before publication."}, status=409
                )
            AnalyticsService().enable_history(dataset)
        return Response(self.get_serializer(dataset).data)

    @action(detail=True, methods=["post"])
    def preview(self, request, pk=None):
        return Response(AnalyticsService().preview(self.get_object()))

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        # Validate and execute before publication. The row lock serializes publish attempts.
        with transaction.atomic():
            dataset = AnalyticsDataset.objects.select_for_update().get(pk=self.get_object().pk)
            if dataset.status == "published":
                return Response(self.get_serializer(dataset).data)
            AnalyticsService().preview(dataset)
            dataset.status = "published"
            dataset.approved_by = request.user
            dataset.published_at = timezone.now()
            dataset.save(update_fields=["status", "approved_by", "published_at"])
        return Response(self.get_serializer(dataset).data)

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        with transaction.atomic():
            dataset = AnalyticsDataset.objects.select_for_update().get(pk=self.get_object().pk)
            dataset.status = "draft"
            dataset.revision += 1
            dataset.save(update_fields=["status", "revision"])
        return Response(self.get_serializer(dataset).data)


@analytics_viewset_schema
class AnalyticsViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AnalyticsQuerySerializer
    http_method_names = ["get", "post", "put", "head", "options"]

    @action(detail=False, methods=["get"])
    def metadata(self, request):
        datasets = AnalyticsDataset.objects.filter(status="published").prefetch_related("metrics")
        # Source mapping details are management-only, even though logical metadata is shared.
        data = []
        for dataset in datasets:
            data.append(
                {
                    "id": dataset.id,
                    "slug": dataset.slug,
                    "title": dataset.title,
                    "description": dataset.description,
                    "grain": dataset.grain,
                    "revision": dataset.revision,
                    "unit": dataset.unit,
                    "timezone": dataset.timezone,
                    "history_start": dataset.history_start,
                    "supports_history": bool(dataset.history_table),
                    "mapping": {
                        key: {"type": field["type"]} for key, field in dataset.mapping.items()
                    },
                    "metrics": [
                        {
                            "key": m.key,
                            "title": m.title,
                            "description": m.description,
                            "aggregation": m.aggregation,
                            "field": m.field,
                            "filters": m.filters,
                            "dimensions": m.dimensions,
                        }
                        for m in dataset.metrics.all()
                    ],
                }
            )
        return Response(
            {"can_manage": request.user.is_staff, "datasets": data, "templates": TEMPLATES}
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsAdminUser])
    def sources(self, request):
        return Response({"tables": AnalyticsService().sources()})

    @action(detail=False, methods=["post"])
    def query(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        options = serializer.validated_data
        dataset = get_object_or_404(AnalyticsDataset, slug=options["dataset"], status="published")
        metric = get_object_or_404(dataset.metrics, key=options["metric"])
        return Response(AnalyticsService().execute(dataset, metric, options))

    @action(detail=False, methods=["post"])
    def details(self, request):
        serializer = AnalyticsDetailsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        options = serializer.validated_data
        dataset = get_object_or_404(AnalyticsDataset, slug=options["dataset"], status="published")
        metric = get_object_or_404(dataset.metrics, key=options["metric"])
        return Response(AnalyticsService().execute(dataset, metric, options, details=True))

    @action(detail=False, methods=["get", "put"])
    def dashboard(self, request):
        if request.method == "GET":
            dashboard = AnalyticsDashboard.objects.filter(owner=request.user).first()
            return Response(
                {
                    "sheets": dashboard.sheets if dashboard else [],
                    "revision": dashboard.revision if dashboard else 0,
                }
            )
        serializer = DashboardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            # Lock the owner as well, to serialize first-time creation.
            type(request.user).objects.select_for_update().get(pk=request.user.pk)
            dashboard = AnalyticsDashboard.objects.filter(owner=request.user).first()
            revision = dashboard.revision if dashboard else 0
            if serializer.validated_data["revision"] != revision:
                return Response(
                    {"detail": "Dashboard changed in another session. Reload before saving."},
                    status=status.HTTP_409_CONFLICT,
                )
            dashboard, _ = AnalyticsDashboard.objects.update_or_create(
                owner=request.user,
                defaults={
                    "sheets": serializer.validated_data["sheets"],
                    "revision": revision + 1,
                },
            )
        return Response({"sheets": dashboard.sheets, "revision": dashboard.revision})
