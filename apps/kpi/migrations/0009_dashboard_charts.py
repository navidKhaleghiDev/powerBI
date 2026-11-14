import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_dashboards(apps, schema_editor):
    Dashboard = apps.get_model('kpi', 'Dashboard')
    KPIChart = apps.get_model('kpi', 'KPIChart')
    database = schema_editor.connection.alias
    for chart in KPIChart.objects.using(database).all().iterator():
        dashboard = Dashboard.objects.using(database).create(title=chart.title)
        KPIChart.objects.using(database).filter(pk=chart.pk).update(dashboard_id=dashboard.pk)


class Migration(migrations.Migration):
    dependencies = [
        ('kpi', '0008_rename_dataset_dashboard'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Keep existing query rows and filter relationships while changing names.
        migrations.RenameModel(old_name='Dashboard', new_name='KPIChart'),
        migrations.AlterModelTable(name='kpichart', table='kpi_chart'),
        migrations.AlterModelOptions(name='kpichart', options={
            'verbose_name': 'KPI chart', 'verbose_name_plural': 'KPI charts',
            'ordering': ['position', 'pk'],
        }),
        migrations.RenameModel(old_name='DashboardFilter', new_name='KPIChartFilter'),
        migrations.RenameField(model_name='kpichartfilter', old_name='dashboard', new_name='chart'),
        migrations.AlterModelTable(name='kpichartfilter', table='kpi_chart_filter'),
        migrations.AlterModelOptions(name='kpichartfilter', options={
            'verbose_name': 'KPI chart filter', 'verbose_name_plural': 'KPI chart filters',
            'ordering': ['position', 'pk'],
        }),
        migrations.CreateModel(
            name='Dashboard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                            related_name='dashboards', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'dashboard', 'verbose_name': 'Dashboard', 'verbose_name_plural': 'Dashboards'},
        ),
        migrations.AddField(
            model_name='kpichart', name='chart_type',
            field=models.CharField(choices=[('bar', 'Bar'), ('line', 'Line'), ('pie', 'Pie'), ('table', 'Table'), ('number', 'Number')],
                                   default='bar', max_length=10),
        ),
        migrations.AddField(model_name='kpichart', name='position', field=models.PositiveIntegerField(default=0)),
        migrations.AddField(
            model_name='kpichart', name='dashboard',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='charts', to='kpi.dashboard'),
        ),
        migrations.RunPython(create_dashboards, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='kpichart', name='dashboard',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='charts', to='kpi.dashboard'),
        ),
    ]
