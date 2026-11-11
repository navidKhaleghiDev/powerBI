from rest_framework.routers import DefaultRouter

from apps.api.viewset.kpi_viewset import KPIViewSet
from apps.api.viewset.analytics_viewset import AnalyticsDatasetViewSet, AnalyticsViewSet


router = DefaultRouter()
router.register('kpis', KPIViewSet, basename='kpis')
router.register('analytics/datasets', AnalyticsDatasetViewSet, basename='analytics-datasets')
router.register('analytics', AnalyticsViewSet, basename='analytics')

urlpatterns = router.urls
