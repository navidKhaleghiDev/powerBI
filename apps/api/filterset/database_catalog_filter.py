from django_filters import rest_framework as filters

from apps.core.models import DatabaseCatalog


class DatabaseCatalogFilter(filters.FilterSet):
    class Meta:
        model = DatabaseCatalog
        fields = ("category", "name")
