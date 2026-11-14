from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from apps.kpi.choices import Aggregation, ChartType, FilterOperator, JoinType


class Dashboard(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='dashboards', null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboard'
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'

    def __str__(self):
        return self.title


class KPIChart(models.Model):
    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name='charts',
    )
    title = models.CharField(max_length=100)
    chart_type = models.CharField(max_length=10, choices=ChartType.choices, default=ChartType.BAR)
    x_label = models.CharField(max_length=100, blank=True, default='')
    y_label = models.CharField(max_length=100, blank=True, default='')
    position = models.PositiveIntegerField(default=0)
    table_name = models.CharField(max_length=255)
    dimension = models.CharField(max_length=100)
    join_table_name = models.CharField(max_length=255,
        blank=True,
        null=True
    )
    measure = models.CharField(max_length=100, blank=True,)
    join_type = models.CharField(max_length=10, 
                                 choices=JoinType.choices,
                                 null=True, 
                                 blank=True)
    join_left_column = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    join_right_column = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    aggregation = models.CharField(max_length=20, choices=Aggregation.choices)
    limit = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        help_text='Maximum number of result groups (1-1000).',
    )

    class Meta:
        db_table = 'kpi_chart'
        verbose_name = 'KPI chart'
        verbose_name_plural = 'KPI charts'
        ordering = ['position', 'pk']

    def __str__(self):
        return self.title


class KPIChartFilter(models.Model):
    chart = models.ForeignKey(
        KPIChart, on_delete=models.CASCADE, related_name='filters',
    )
    column = models.CharField(max_length=100)
    operator = models.CharField(max_length=11, choices=FilterOperator.choices)
    value = models.JSONField(blank=True, null=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'kpi_chart_filter'
        verbose_name = 'KPI chart filter'
        verbose_name_plural = 'KPI chart filters'
        ordering = ['position', 'pk']

    def __str__(self):
        return f'{self.column} {self.operator}'
