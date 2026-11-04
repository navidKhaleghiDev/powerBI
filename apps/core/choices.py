from django.db import models


class DatabaseType(models.TextChoices):
    POSTGRESQL = "postgresql", "PostgreSQL"
    MYSQL = "mysql", "MySQL"
    CLICKHOUSE = "clickhouse", "ClickHouse"
    MSSQL = "mssql", "Microsoft SQL Server"
