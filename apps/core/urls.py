from rest_framework.routers import DefaultRouter

from apps.api.viewset.database_viewset import DatabaseViewSet

router = DefaultRouter()
router.register(r"database", DatabaseViewSet, basename="database")

urlpatterns = router.urls
