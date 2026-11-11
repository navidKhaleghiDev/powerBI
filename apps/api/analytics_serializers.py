import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db import transaction
from rest_framework import serializers

from apps.kpi.models import AnalyticsDataset, AnalyticsMetric

IDENTIFIER = r"\A[A-Za-z_][A-Za-z0-9_]*\Z"
TIME_DIMENSIONS = {"day", "month", "year"}


class MappingFieldSerializer(serializers.Serializer):
    column = serializers.RegexField(IDENTIFIER, max_length=100)
    type = serializers.ChoiceField(choices=["number", "date", "string"])


class MetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsMetric
        fields = ["key", "title", "description", "aggregation", "field", "filters", "dimensions"]
        extra_kwargs = {"key": {"validators": []}}
        validators = []


class DatasetSerializer(serializers.ModelSerializer):
    mapping = serializers.DictField(child=MappingFieldSerializer(), allow_empty=False)
    metrics = MetricSerializer(many=True, allow_empty=False)

    class Meta:
        model = AnalyticsDataset
        fields = [
            "id",
            "slug",
            "title",
            "description",
            "grain",
            "source_table",
            "mapping",
            "primary_key",
            "version_column",
            "deleted_column",
            "history_table",
            "recorded_at_column",
            "history_start",
            "timezone",
            "unit",
            "status",
            "revision",
            "published_at",
            "metrics",
        ]
        read_only_fields = ["status", "revision", "published_at"]

    def validate(self, attrs):
        config = {
            field: getattr(self.instance, field)
            for field in self.Meta.fields
            if self.instance and hasattr(self.instance, field) and field not in {"metrics"}
        }
        config.update(attrs)
        for name in [
            "source_table",
            "primary_key",
            "version_column",
            "deleted_column",
            "history_table",
            "recorded_at_column",
        ]:
            value = config.get(name, "")
            if value and not re.fullmatch(IDENTIFIER, value):
                raise serializers.ValidationError(
                    {name: "Use a simple column/table name in the configured analytics database."}
                )
        mapping = config["mapping"]
        if len(mapping) > 30:
            raise serializers.ValidationError(
                {"mapping": "At most 30 mapped fields are supported."}
            )
        for key in mapping:
            if not re.fullmatch(IDENTIFIER, key) or key in TIME_DIMENSIONS or key.startswith("_"):
                raise serializers.ValidationError(
                    {
                        "mapping": "Logical field names must be identifiers and cannot be day/month/year or start with underscore."
                    }
                )
        if mapping.get("date", {}).get("type") != "date":
            raise serializers.ValidationError(
                {"mapping": "Map a date field named date for the business period."}
            )
        try:
            ZoneInfo(config.get("timezone", "Asia/Tehran"))
        except ZoneInfoNotFoundError:
            raise serializers.ValidationError({"timezone": "Unknown IANA timezone."})
        history = [
            bool(config.get(name))
            for name in ["history_table", "recorded_at_column", "history_start"]
        ]
        if any(history) and (not all(history) or not config.get("version_column")):
            raise serializers.ValidationError(
                {
                    "history_table": "History requires an append-only table, recorded timestamp, earliest reliable cutoff and version column."
                }
            )
        metrics = attrs.get("metrics", [])
        if len(metrics) > 30 or len({m["key"] for m in metrics}) != len(metrics):
            raise serializers.ValidationError({"metrics": "Use at most 30 uniquely named metrics."})
        for metric in metrics:
            field = metric.get("field", "amount")
            if (
                metric.get("aggregation", "sum") != "count"
                and mapping.get(field, {}).get("type") != "number"
            ):
                raise serializers.ValidationError(
                    {"metrics": "Numeric aggregations require a mapped numeric field."}
                )
            dimensions = metric.get("dimensions", [])
            if not isinstance(dimensions, list) or any(
                not isinstance(d, str) or d not in TIME_DIMENSIONS | set(mapping)
                for d in dimensions
            ):
                raise serializers.ValidationError({"metrics": "Unknown dimension."})
            filters = metric.get("filters", {})
            if not isinstance(filters, dict) or any(
                k not in mapping
                or mapping[k]["type"] != "string"
                or not isinstance(v, list)
                or not v
                or len(v) > 50
                or any(not isinstance(x, str) or len(x) > 255 for x in v)
                for k, v in filters.items()
            ):
                raise serializers.ValidationError(
                    {
                        "metrics": "Fixed filters must contain mapped string fields and nonempty string lists."
                    }
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        metrics = validated_data.pop("metrics")
        dataset = AnalyticsDataset.objects.create(**validated_data)
        AnalyticsMetric.objects.bulk_create(
            [AnalyticsMetric(dataset=dataset, **metric) for metric in metrics]
        )
        return dataset

    @transaction.atomic
    def update(self, instance, validated_data):
        metrics = validated_data.pop("metrics")
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.revision += 1
        instance.save()
        instance.metrics.all().delete()
        AnalyticsMetric.objects.bulk_create(
            [AnalyticsMetric(dataset=instance, **metric) for metric in metrics]
        )
        return instance


class AnalyticsQuerySerializer(serializers.Serializer):
    dataset = serializers.SlugField()
    metric = serializers.SlugField()
    group_by = serializers.ListField(
        child=serializers.CharField(max_length=100), max_length=2, default=list
    )
    date_from = serializers.DateField()
    date_to = serializers.DateField(help_text="Exclusive end date.")
    calendar = serializers.ChoiceField(choices=["persian", "gregorian"], default="persian")
    mode = serializers.ChoiceField(choices=["latest", "historical"], default="latest")
    known_at = serializers.DateTimeField(required=False)
    filters = serializers.DictField(
        child=serializers.ListField(
            child=serializers.CharField(max_length=255), min_length=1, max_length=50
        ),
        default=dict,
    )
    limit = serializers.IntegerField(default=1000, min_value=1, max_value=1000)

    def validate(self, attrs):
        if not 0 < (attrs["date_to"] - attrs["date_from"]).days <= 3660:
            raise serializers.ValidationError(
                "Choose a positive business period of at most ten years."
            )
        if attrs["date_from"].year < 1970 or attrs["date_to"].year > 2100:
            raise serializers.ValidationError("Supported business dates are between 1970 and 2100.")
        if attrs["mode"] == "historical" and "known_at" not in attrs:
            raise serializers.ValidationError(
                {"known_at": "Historical mode requires a knowledge cutoff."}
            )
        if attrs["mode"] == "latest" and "known_at" in attrs:
            raise serializers.ValidationError(
                {"known_at": "Only historical mode accepts a knowledge cutoff."}
            )
        if len(attrs["filters"]) > 10:
            raise serializers.ValidationError({"filters": "Use at most ten filters."})
        groups = attrs["group_by"]
        if len(set(groups)) != len(groups) or len(set(groups) & TIME_DIMENSIONS) > 1:
            raise serializers.ValidationError(
                {"group_by": "Use distinct dimensions and at most one time grain."}
            )
        return attrs


class AnalyticsDetailsSerializer(AnalyticsQuerySerializer):
    cursor = serializers.CharField(max_length=255, required=False)
    limit = serializers.IntegerField(default=50, min_value=1, max_value=100)


class DashboardSerializer(serializers.Serializer):
    revision = serializers.IntegerField(min_value=0)
    sheets = serializers.JSONField()

    def validate_sheets(self, value):
        if not isinstance(value, list) or len(value) > 20:
            raise serializers.ValidationError("Use at most 20 sheets.")
        import json

        if len(json.dumps(value)) > 200_000:
            raise serializers.ValidationError("Dashboard exceeds the size limit.")
        ids = set()
        for sheet in value:
            if (
                not isinstance(sheet, dict)
                or not isinstance(sheet.get("id"), str)
                or sheet["id"] in ids
                or not isinstance(sheet.get("name"), str)
                or not isinstance(sheet.get("widgets"), list)
                or len(sheet["widgets"]) > 50
            ):
                raise serializers.ValidationError("Invalid sheet definition.")
            ids.add(sheet["id"])
            widget_ids = set()
            for widget in sheet["widgets"]:
                if (
                    not isinstance(widget, dict)
                    or not isinstance(widget.get("id"), str)
                    or widget["id"] in widget_ids
                    or not isinstance(widget.get("title"), str)
                    or widget.get("visual")
                    not in [
                        "bar",
                        "horizontalBar",
                        "line",
                        "pie",
                        "radar",
                        "heatmap",
                        "table",
                        "card",
                    ]
                    or widget.get("size") not in ["small", "medium", "wide"]
                ):
                    raise serializers.ValidationError("Invalid widget definition.")
                widget_ids.add(widget["id"])
                query = widget.get("query")
                if query is not None and (
                    not isinstance(query, dict)
                    or not isinstance(query.get("measures"), list)
                    or len(query["measures"]) != 1
                    or not isinstance(query["measures"][0], str)
                    or not isinstance(query.get("dimensions", []), list)
                    or any(not isinstance(d, str) for d in query.get("dimensions", []))
                ):
                    raise serializers.ValidationError("Invalid widget query.")
        return value


class AnalyticsResultSerializer(serializers.Serializer):
    columns = serializers.ListField(child=serializers.DictField())
    rows = serializers.ListField(child=serializers.DictField())
    meta = serializers.DictField()


class PublishedMappingSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["number", "date", "string"])


class PublishedDatasetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    slug = serializers.SlugField()
    title = serializers.CharField()
    description = serializers.CharField()
    grain = serializers.CharField()
    revision = serializers.IntegerField()
    unit = serializers.CharField()
    timezone = serializers.CharField()
    history_start = serializers.DateTimeField(allow_null=True)
    supports_history = serializers.BooleanField()
    mapping = serializers.DictField(child=PublishedMappingSerializer())
    metrics = MetricSerializer(many=True)


class AnalyticsMetadataSerializer(serializers.Serializer):
    can_manage = serializers.BooleanField()
    datasets = PublishedDatasetSerializer(many=True)
    templates = MetricSerializer(many=True)


class AnalyticsSourcesSerializer(serializers.Serializer):
    tables = serializers.ListField(child=serializers.DictField())
