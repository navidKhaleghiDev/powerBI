from django.contrib import admin

from apps.core.models import DatabaseCatalog


@admin.register(DatabaseCatalog)
class DatabaseCatalogAdmin(admin.ModelAdmin):
    list_display = ("id", "db_type", "category")
    list_filter = ("category",)
    search_fields = ("db_type",)
    ordering = ("category", "db_type")
    fields = ("db_type", "category", "image")
