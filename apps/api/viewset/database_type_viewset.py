from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from apps.api.filterset.database_catalog_filter import DatabaseCatalogFilter
from apps.core.models import DatabaseCatalog
from apps.core.schema import database_catalog_viewset_schema
from apps.core.serializers import DatabaseCatalogSerializer
from utils.pagination import DatabaseTypePagination


@database_catalog_viewset_schema
class DatabaseCatalogViewSet(ListModelMixin, GenericViewSet):
    queryset = DatabaseCatalog.objects.order_by("name", "id")
    serializer_class = DatabaseCatalogSerializer
    pagination_class = DatabaseTypePagination
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DatabaseCatalogFilter
    search_fields = ["name"]
    ordering_fields = ["name", "category", "id"]
    ordering = ["name", "id"]
