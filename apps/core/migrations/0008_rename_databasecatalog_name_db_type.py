from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_databasecatalog_delete_analyticdatabase_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="databasecatalog", name="unique_database_category_name",
        ),
        migrations.RenameField(
            model_name="databasecatalog", old_name="name", new_name="db_type",
        ),
        migrations.AddConstraint(
            model_name="databasecatalog",
            constraint=models.UniqueConstraint(
                fields=("category", "db_type"), name="unique_database_category_db_type",
            ),
        ),
    ]
