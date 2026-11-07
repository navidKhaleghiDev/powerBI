from rest_framework.routers import DefaultRouter

from apps.api.viewset.database_viewset import DatabaseViewSet
from apps.api.viewset.database_type_viewset import DatabaseCatalogViewSet

from apps.api.viewset.connect_viewset import ConnectViewSet

router = DefaultRouter()
router.register(r"connect", ConnectViewSet, basename="connect")
router.register(r"database", DatabaseViewSet, basename="database")
router.register(r"database-types", DatabaseCatalogViewSet, basename="database-type")

urlpatterns = router.urls
