from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('kpi', '0007_alter_dataset_limit'),
    ]

    operations = [
        migrations.RenameModel(old_name='DataSet', new_name='Dashboard'),
        migrations.RenameModel(old_name='DataSetFilter', new_name='DashboardFilter'),
        migrations.RenameField(
            model_name='dashboardfilter', old_name='dataset', new_name='dashboard',
        ),
        migrations.AlterModelTable(name='dashboard', table='dashboard'),
        migrations.AlterModelTable(name='dashboardfilter', table='dashboard_filter'),
        migrations.AlterModelOptions(
            name='dashboard',
            options={'verbose_name': 'Dashboard', 'verbose_name_plural': 'Dashboards'},
        ),
        migrations.AlterModelOptions(
            name='dashboardfilter',
            options={
                'verbose_name': 'Dashboard filter',
                'verbose_name_plural': 'Dashboard filters',
                'ordering': ['position', 'pk'],
            },
        ),
    ]
