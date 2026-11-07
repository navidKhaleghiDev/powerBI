from django.db import models
from utils.uploads import database_image_upload_to
from utils.images import create_thumbnail
from apps.core.choices import DatabaseCategory, DatabaseType

class DatabaseImageModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:
            self.image = create_thumbnail(self.image)

        return super().save(*args, **kwargs)


class DatabaseCatalog(DatabaseImageModel):
    db_type = models.CharField(max_length=30, choices=DatabaseType.choices, null=True)
    category = models.CharField(max_length=10, choices=DatabaseCategory.choices)
    image = models.ImageField(upload_to=database_image_upload_to, blank=True, null=True)

    class Meta:
        db_table = "database_catalog"
        verbose_name = "Database catalog entry"
        verbose_name_plural = "Database catalog entries"
        constraints = [
            models.UniqueConstraint(fields=("category", "db_type"), name="unique_database_category_db_type"),
        ]

    def __str__(self):
        return self.db_type or ""
