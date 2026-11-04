from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_alter_database_db_type"),
    ]

    operations = [
        # An intermediate name avoids a case-only model-state key collision.
        migrations.RenameModel(old_name="DATABASE", new_name="DatabaseConnectionRename"),
        migrations.RenameModel(old_name="DatabaseConnectionRename", new_name="DataBase"),
    ]
