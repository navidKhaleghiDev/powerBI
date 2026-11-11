from django.core.management.base import BaseCommand

from apps.core.choices import DatabaseCategory, DatabaseType
from apps.core.models import DatabaseCatalog


class Command(BaseCommand):
    help = "Create the initial PostgreSQL and ClickHouse database types. Safe to run repeatedly."
    requires_migrations_checks = True

    def handle(self, *args, **options):
        database_types = (
            (DatabaseType.POSTGRESQL, DatabaseCategory.SQL),
            (DatabaseType.CLICKHOUSE, DatabaseCategory.ANALYTIC),
        )
        for db_type, category in database_types:
            _, created = DatabaseCatalog.objects.get_or_create(
                db_type=db_type, category=category
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {db_type.label} database type."))
            else:
                self.stdout.write(f"{db_type.label} database type already exists.")
