from django.db import models


class DatabaseMetadata(models.Model):
    """Lightweight model used to satisfy DRF ModelViewSet requirements without persisting metadata."""

    class Meta:
        managed = False
        app_label = "api"
