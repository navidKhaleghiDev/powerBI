from django.db import models
from apps.kpi.choices import Aggregation, JoinType


class DataSet(models.Model):
    title = models.CharField(max_length=100)
    table_name = models.CharField(max_length=255)
    dimension = models.CharField(max_length=100)
    join_table_name = models.CharField(max_length=255, blank=True, null=True)
    measure = models.CharField(
        max_length=100,
        blank=True,
    )
    join_type = models.CharField(max_length=10, choices=JoinType.choices, null=True, blank=True)
    join_left_column = models.CharField(max_length=100, blank=True, null=True)
    join_right_column = models.CharField(max_length=100, blank=True, null=True)
    aggregation = models.CharField(max_length=20, choices=Aggregation.choices)

    class Meta:
        db_table = "data_set"
        verbose_name = "Data set"
        verbose_name_plural = "Data sets"

    def __str__(self):
        return self.title


class AnalyticsDataset(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    grain = models.CharField(max_length=255)
    source_table = models.CharField(max_length=100)
    mapping = models.JSONField(default=dict)
    primary_key = models.CharField(max_length=100)
    version_column = models.CharField(max_length=100, blank=True)
    deleted_column = models.CharField(max_length=100, blank=True)
    history_table = models.CharField(max_length=100, blank=True)
    recorded_at_column = models.CharField(max_length=100, blank=True)
    history_start = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=64, default="Asia/Tehran")
    unit = models.CharField(max_length=24, default="IRR")
    status = models.CharField(
        max_length=16, choices=[("draft", "Draft"), ("published", "Published")], default="draft"
    )
    revision = models.PositiveIntegerField(default=1)
    approved_by = models.ForeignKey(
        "users.CustomUser", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_dataset"
        verbose_name = "Analytics dataset"
        verbose_name_plural = "Analytics datasets"
        ordering = ["title"]


class AnalyticsMetric(models.Model):
    dataset = models.ForeignKey(AnalyticsDataset, on_delete=models.CASCADE, related_name="metrics")
    key = models.SlugField()
    title = models.CharField(max_length=160)
    description = models.TextField()
    aggregation = models.CharField(
        max_length=16,
        choices=[
            ("sum", "Sum"),
            ("count", "Count"),
            ("avg", "Average"),
            ("min", "Minimum"),
            ("max", "Maximum"),
        ],
        default="sum",
    )
    field = models.SlugField(default="amount", blank=True)
    filters = models.JSONField(default=dict, blank=True)
    dimensions = models.JSONField(default=list)

    class Meta:
        db_table = "analytics_metric"
        verbose_name = "Analytics metric"
        verbose_name_plural = "Analytics metrics"
        constraints = [
            models.UniqueConstraint(fields=["dataset", "key"], name="analytics_metric_dataset_key")
        ]


class AnalyticsDashboard(models.Model):
    owner = models.OneToOneField(
        "users.CustomUser", on_delete=models.CASCADE, related_name="analytics_dashboard"
    )
    sheets = models.JSONField(default=list)
    revision = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_dashboard"
        verbose_name = "Analytics dashboard"
        verbose_name_plural = "Analytics dashboards"
