from rest_framework.routers import DefaultRouter

from apps.api.viewset.kpi_viewset import KPIViewSet


router = DefaultRouter()
router.register('kpis', KPIViewSet, basename='kpis')

urlpatterns = router.urls
