from django.core.management.base import BaseCommand

from apps.core.choices import SqlDatabaseType
from apps.core.models import SqlDatabase


class Command(BaseCommand):
    help = "Create the initial PostgreSQL database type entry. Safe to run repeatedly."
    requires_migrations_checks = True

    def handle(self, *args, **options):
        _, created = SqlDatabase.objects.get_or_create(name=SqlDatabaseType.POSTGRESQL)
        if created:
            self.stdout.write(self.style.SUCCESS("Created PostgreSQL database type."))
        else:
            self.stdout.write("PostgreSQL database type already exists.")
