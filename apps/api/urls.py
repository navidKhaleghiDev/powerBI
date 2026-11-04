from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.api.viewset.database_viewset import DatabaseViewSet

router = DefaultRouter()
router.register(r"database", DatabaseViewSet, basename="database")

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
] + router.urls
