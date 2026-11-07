from django.contrib import admin

from apps.core.models import DatabaseCatalog


@admin.register(DatabaseCatalog)
class DatabaseCatalogAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category")
    list_filter = ("category",)
    search_fields = ("name",)
    ordering = ("category", "name")
    fields = ("name", "category", "image")
