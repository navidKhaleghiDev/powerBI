from django.db import models

from apps.core.choices import DatabaseType


class DataBase(models.Model):
    db_type = models.CharField(max_length=32, choices=DatabaseType.choices)
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()
    database = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "database"
        verbose_name = "Database"
        verbose_name_plural = "Databases"
        constraints = [
            models.UniqueConstraint(
                fields=["db_type", "host", "port", "database", "username"],
                name="unique_database_connection",
            ),
        ]

    def __str__(self):
        return f"{self.db_type}://{self.host}:{self.port}/{self.database} ({self.username})"
