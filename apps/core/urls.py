from rest_framework.routers import DefaultRouter

from apps.api.viewset.consumer_viewset import ConsumerViewset
from apps.api.viewset.database_viewset import DatabaseViewSet
from apps.api.viewset.database_type_viewset import DatabaseCatalogViewSet, DataTypeViewSet

from apps.api.viewset.connect_viewset import ConnectViewSet

router = DefaultRouter()
router.register(r"consumer", ConsumerViewset, basename="consumer-pipeline")
router.register(r"connect", ConnectViewSet, basename="connect")
router.register(r"database", DatabaseViewSet, basename="database")
router.register(r"database-types", DatabaseCatalogViewSet, basename="database-type")
router.register(r"data-types", DataTypeViewSet, basename="data-type")

urlpatterns = router.urls
