from django.db import models
from apps.core.choices import AnalyticDatabaseType, NoSqlDatabaseType, SqlDatabaseType

class SqlDatabase(models.Model):
    name = models.CharField(max_length=30, choices=SqlDatabaseType.choices, unique=True)

    class Meta:
        db_table = "sql_database"
        verbose_name = "SQL database"
        verbose_name_plural = "SQL databases"

    def __str__(self):
        return self.name

class AnalyticDatabase(models.Model):
    name = models.CharField(max_length=30, choices=AnalyticDatabaseType.choices, unique=True)

    class Meta:
        db_table = "analytic_database"
        verbose_name = "Analytic database"
        verbose_name_plural = "Analytic databases"

    def __str__(self):
        return self.name


class NoSqlDatabase(models.Model):
    name = models.CharField(max_length=30, choices=NoSqlDatabaseType.choices, unique=True)

    class Meta:
        db_table = "no_sql_database"
        verbose_name = "NoSQL database"
        verbose_name_plural = "NoSQL databases"

    def __str__(self):
        return self.name
