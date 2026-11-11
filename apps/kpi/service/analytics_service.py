"""Compile logical, approved metric queries; never accept browser SQL."""

from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import clickhouse_connect
import jdatetime
from clickhouse_connect.driver.exceptions import Error
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from utils.consumers import quote_identifier as q


class AnalyticsUnavailable(APIException):
    status_code = 503
    default_detail = (
        "The analytics source is unavailable. Check the dataset mapping and ClickHouse connection."
    )


class AnalyticsService:
    @staticmethod
    def client(manage=False):
        return clickhouse_connect.get_client(
            host=settings.CONSUMER_HOST,
            port=settings.CONSUMER_PORT,
            username=settings.CONSUMER_USER if manage else settings.ANALYTICS_USER,
            password=settings.CONSUMER_PASSWORD if manage else settings.ANALYTICS_PASSWORD,
            database=settings.CONSUMER_DATABASE,
            connect_timeout=5,
            send_receive_timeout=30,
        )

    @staticmethod
    def qualified(table):
        return f"{q(settings.CONSUMER_DATABASE)}.{q(table)}"

    def sources(self):
        try:
            with self.client() as client:
                rows = client.query(
                    "SELECT t.name, t.engine, c.name, c.type FROM system.tables t "
                    "INNER JOIN system.columns c ON t.database = c.database AND t.name = c.table "
                    "WHERE t.database = {database:String} AND t.is_temporary = 0 "
                    "AND (endsWith(t.engine, 'MergeTree') OR t.engine = 'View') ORDER BY t.name, c.position",
                    parameters={"database": settings.CONSUMER_DATABASE},
                    settings={"readonly": 1, "max_execution_time": 20},
                ).result_rows
        except Error as exc:
            raise AnalyticsUnavailable() from exc
        tables = {}
        for table, engine, column, kind in rows:
            tables.setdefault(table, {"name": table, "engine": engine, "columns": []})[
                "columns"
            ].append({"name": column, "type": kind})
        return list(tables.values())

    def validate_source(self, dataset):
        sources = {source["name"]: source for source in self.sources()}
        for name in [dataset.source_table, dataset.history_table]:
            if not name:
                continue
            source = sources.get(name)
            if not source:
                raise ValidationError(
                    {
                        "source_table": "Select a business view or MergeTree table from the configured database."
                    }
                )
            columns = {c["name"]: c["type"] for c in source["columns"]}
            required = {dataset.primary_key, *(v["column"] for v in dataset.mapping.values())}
            required.update(c for c in [dataset.version_column, dataset.deleted_column] if c)
            if name == dataset.history_table:
                required.add(dataset.recorded_at_column)
                if source["engine"] != "MergeTree":
                    raise ValidationError(
                        {
                            "history_table": "Historical queries require an append-only MergeTree table that retains every version."
                        }
                    )
                if not columns.get(dataset.recorded_at_column, "").startswith("DateTime"):
                    raise ValidationError(
                        {"recorded_at_column": "Use a non-nullable DateTime/DateTime64 timestamp."}
                    )
            if required - set(columns):
                raise ValidationError(
                    {"mapping": "Some mapped or identity columns do not exist in the source."}
                )
            if columns[dataset.primary_key].startswith("Nullable"):
                raise ValidationError({"primary_key": "The business key must not be nullable."})
            if dataset.version_column and not columns[dataset.version_column].startswith(
                ("UInt", "Int", "DateTime")
            ):
                raise ValidationError(
                    {"version_column": "Use a non-nullable integer or timestamp source version."}
                )
            if source["engine"] not in ["MergeTree", "View", "ReplacingMergeTree"]:
                raise ValidationError(
                    {
                        "source_table": "Unsupported business table engine. Publish a validated business view instead."
                    }
                )
            if source["engine"] == "ReplacingMergeTree" and not dataset.version_column:
                raise ValidationError(
                    {"version_column": "A version column is required for this source."}
                )
            for field in dataset.mapping.values():
                kind = columns[field["column"]].removeprefix("Nullable(").removesuffix(")")
                if field["type"] == "number" and not kind.startswith(
                    ("Int", "UInt", "Decimal", "Float")
                ):
                    raise ValidationError(
                        {"mapping": "A numeric mapping must reference a numeric source column."}
                    )
                if field["type"] == "date" and not kind.startswith("Date"):
                    raise ValidationError(
                        {"mapping": "A date mapping must reference Date/DateTime source data."}
                    )

    @staticmethod
    def _live(column):
        return f"lowerUTF8(toString({column})) NOT IN ('1', 'true', 'd')"

    def base(self, dataset, options, params):
        historical = options["mode"] == "historical"
        table = dataset.history_table if historical else dataset.source_table
        columns = list(
            dict.fromkeys(
                [
                    dataset.primary_key,
                    *(v["column"] for v in dataset.mapping.values()),
                    *([dataset.deleted_column] if dataset.deleted_column else []),
                ]
            )
        )
        source = self.qualified(table)
        where = ""
        if historical:
            cutoff = options["known_at"]
            if not dataset.history_table or not dataset.history_start:
                raise ValidationError(
                    {"known_at": "This dataset does not retain historical versions."}
                )
            if cutoff < dataset.history_start or cutoff > timezone.now():
                raise ValidationError(
                    {"known_at": "The cutoff is outside the retained history period."}
                )
            params["known_at"] = cutoff.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            where = f" WHERE {q(dataset.recorded_at_column)} <= {{known_at:DateTime64(6, 'UTC')}}"
        if dataset.version_column:
            # A tuple keeps nullable field values together and does not skip null updates.
            values = ", ".join(q(c) for c in columns)
            ordering = q(dataset.version_column)
            if historical:
                ordering = f"tuple({ordering}, {q(dataset.recorded_at_column)})"
            select = ", ".join(
                f"tupleElement(_row, {i + 1}) AS {q(c)}" for i, c in enumerate(columns)
            )
            resolved = f"SELECT {select} FROM (SELECT argMax(tuple({values}), {ordering}) AS _row FROM {source}{where} GROUP BY {q(dataset.primary_key)})"
        else:
            resolved = f"SELECT {', '.join(q(c) for c in columns)} FROM {source}{where}"
        # Deletion, date and business predicates must run AFTER version resolution.
        live = f" WHERE {self._live(q(dataset.deleted_column))}" if dataset.deleted_column else ""
        mapped = ", ".join(
            f"{q(value['column'])} AS {q(key)}" for key, value in dataset.mapping.items()
        )
        return f"SELECT {mapped}, toString({q(dataset.primary_key)}) AS _record_id FROM ({resolved}){live}"

    @staticmethod
    def encode(value):
        import math

        if isinstance(value, Decimal) or isinstance(value, int) and abs(value) > 2**53 - 1:
            return str(value)
        if isinstance(value, float):
            return value if math.isfinite(value) else None
        return value

    @staticmethod
    def period_expression(grain, options, params):
        start, end = options["date_from"], options["date_to"]
        conditions, labels = [], []
        cursor = start
        while cursor < end:
            converted = (
                jdatetime.date.fromgregorian(date=cursor)
                if options["calendar"] == "persian"
                else cursor
            )
            key = converted.strftime(
                "%Y-%m-%d" if grain == "day" else "%Y-%m" if grain == "month" else "%Y"
            )
            next_date = cursor + timedelta(days=1)
            while next_date < end:
                following = (
                    jdatetime.date.fromgregorian(date=next_date)
                    if options["calendar"] == "persian"
                    else next_date
                )
                if (
                    following.strftime(
                        "%Y-%m-%d" if grain == "day" else "%Y-%m" if grain == "month" else "%Y"
                    )
                    != key
                ):
                    break
                next_date += timedelta(days=1)
            index = len(labels)
            params[f"edge_{index}"] = next_date
            params[f"label_{index}"] = key
            conditions.extend(
                [f"_business_date < {{edge_{index}:Date}}", f"{{label_{index}:String}}"]
            )
            labels.append(key)
            cursor = next_date
        # multiIf requires a default. Period predicates ensure no unmatched date.
        return "multiIf(" + ", ".join([*conditions, "''"]) + ")"

    def execute(self, dataset, metric, options, details=False):
        groups = options["group_by"]
        if any(g not in metric.dimensions for g in groups):
            raise ValidationError(
                {"group_by": "This KPI does not support the selected dimensions."}
            )
        for key in options["filters"]:
            if (
                key not in dataset.mapping
                or dataset.mapping[key]["type"] != "string"
                or key not in metric.dimensions
            ):
                raise ValidationError(
                    {"filters": "Filter fields must be permitted categorical dimensions."}
                )
        params = {
            "date_from": options["date_from"],
            "date_to": options["date_to"],
            "tz": dataset.timezone,
        }
        base = self.base(dataset, options, params)
        predicates = ["_business_date >= {date_from:Date}", "_business_date < {date_to:Date}"]
        for index, (key, values) in enumerate(
            [*metric.filters.items(), *options["filters"].items()]
        ):
            params[f"filter_{index}"] = values
            predicates.append(f"toString({q(key)}) IN {{filter_{index}:Array(String)}}")
        if details and options.get("cursor"):
            params["cursor"] = options["cursor"]
            predicates.append("_record_id > {cursor:String}")
        selections = []
        for group in groups:
            expression = (
                self.period_expression(group, options, params)
                if group in {"day", "month", "year"}
                else q(group)
            )
            selections.append(f"{expression} AS {q(group)}")
        measure = "*" if metric.aggregation == "count" else q(metric.field)
        selections.append(f"{metric.aggregation}({measure}) AS _value")
        business = f"SELECT *, toDate({q('date')}, {{tz:String}}) AS _business_date FROM ({base})"
        if details:
            selections = [q(key) for key in dataset.mapping] + ["_record_id"]
        sql = f"SELECT {', '.join(selections)} FROM ({business}) WHERE {' AND '.join(predicates)}"
        if details:
            sql += " ORDER BY _record_id"
        elif groups:
            keys = ", ".join(q(group) for group in groups)
            sql += f" GROUP BY {keys} ORDER BY {keys}"
        # Fetch one extra result to report truncation; never silently claim a full total.
        sql += f" LIMIT {options['limit'] + 1}"
        try:
            with self.client() as client:
                rows = client.query(
                    sql,
                    parameters=params,
                    settings={
                        "readonly": 1,
                        "max_execution_time": 20,
                        "max_rows_to_read": 10_000_000,
                        "max_memory_usage": 536_870_912,
                        "max_result_rows": options["limit"] + 1,
                        "result_overflow_mode": "throw",
                    },
                ).result_rows
        except Error as exc:
            raise AnalyticsUnavailable() from exc
        metric_id = f"{dataset.slug}.{metric.key}"
        fields = [*groups, metric_id]
        columns = [
            {
                "key": group,
                "type": "date"
                if group in {"day", "month", "year"}
                else dataset.mapping[group]["type"],
            }
            for group in groups
        ]
        columns.append(
            {
                "key": metric_id,
                "type": "number",
                "unit": "" if metric.aggregation == "count" else dataset.unit,
            }
        )
        if details:
            fields = [*dataset.mapping, "_record_id"]
            columns = [
                {"key": key, "type": field["type"]} for key, field in dataset.mapping.items()
            ]
        return {
            "columns": columns,
            "rows": [dict(zip(fields, map(self.encode, row))) for row in rows[: options["limit"]]],
            "meta": {
                "dataset": dataset.slug,
                "revision": dataset.revision,
                "metric": metric.key,
                "queried_at": timezone.now().isoformat(),
                "mode": options["mode"],
                "known_at": options.get("known_at"),
                "calendar": options["calendar"],
                "timezone": dataset.timezone,
                "truncated": len(rows) > options["limit"],
                "source_freshness": None,
                "next_cursor": str(rows[options["limit"] - 1][-1])
                if details and len(rows) > options["limit"]
                else None,
            },
        }

    def preview(self, dataset):
        self.validate_source(dataset)
        metric = dataset.metrics.first()
        # Execute a bounded recent aggregate preview, with no records or source secrets exposed.
        today = timezone.localdate(timezone=ZoneInfo(dataset.timezone))
        return self.execute(
            dataset,
            metric,
            {
                "mode": "latest",
                "date_from": today - timedelta(days=30),
                "date_to": today + timedelta(days=1),
                "calendar": "gregorian",
                "filters": {},
                "group_by": [],
                "limit": 10,
            },
        )

    def enable_history(self, dataset):
        """Capture future insert versions plus a baseline, without changing the CDC source."""
        if dataset.history_table:
            raise ValidationError("History is already configured.")
        if not dataset.version_column:
            raise ValidationError(
                {"version_column": "History capture requires an ordered source version."}
            )
        self.validate_source(dataset)
        source = next(s for s in self.sources() if s["name"] == dataset.source_table)
        if source["engine"] not in ["MergeTree", "ReplacingMergeTree"]:
            raise ValidationError(
                "Automatic history capture requires a MergeTree source table, not a view."
            )
        if "__analytics_recorded_at" in {c["name"] for c in source["columns"]}:
            raise ValidationError("The source contains the reserved history timestamp column.")
        # New revision identifiers avoid changing or overwriting any existing table.
        history_name = f"analytics_{dataset.pk}_history"
        view_name = f"analytics_{dataset.pk}_history_mv"
        history = self.qualified(history_name)
        view = self.qualified(view_name)
        origin = self.qualified(dataset.source_table)
        columns = ", ".join(q(c["name"]) for c in source["columns"])
        try:
            with self.client(manage=True) as client:
                client.command(
                    f"CREATE TABLE IF NOT EXISTS {history} AS {origin} ENGINE = MergeTree ORDER BY {q(dataset.primary_key)}"
                )
                client.command(
                    f"ALTER TABLE {history} ADD COLUMN IF NOT EXISTS __analytics_recorded_at DateTime64(6, 'UTC') DEFAULT now64(6, 'UTC')"
                )
                # Install capture before seeding: version resolution makes any overlap harmless.
                client.command(
                    f"CREATE MATERIALIZED VIEW IF NOT EXISTS {view} TO {history} AS SELECT {columns}, now64(6, 'UTC') AS __analytics_recorded_at FROM {origin}"
                )
                client.command(
                    f"INSERT INTO {history} ({columns}, __analytics_recorded_at) SELECT {columns}, now64(6, 'UTC') FROM {origin}",
                    settings={"max_execution_time": 20, "max_memory_usage": 536_870_912},
                )
        except Error as exc:
            # DDL is nontransactional. A retry reuses the objects and resolves overlapping versions.
            raise AnalyticsUnavailable(
                "History provisioning failed. Existing data was preserved; retry or inspect the generated history objects."
            ) from exc
        dataset.history_table = history_name
        dataset.recorded_at_column = "__analytics_recorded_at"
        # Only cutoffs after the complete baseline are supported, never invented past snapshots.
        dataset.history_start = timezone.now()
        dataset.save(update_fields=["history_table", "recorded_at_column", "history_start"])
