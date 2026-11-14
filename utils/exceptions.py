"""Custom exceptions shared by application services and API views."""


class KPIUnavailable(RuntimeError):
    """ClickHouse could not provide KPI source metadata."""


class ChartQueryFailed(RuntimeError):
    """A submitted chart query failed before its dashboard could be saved."""

    def __init__(self, chart_index):
        self.chart_index = chart_index
        super().__init__('Unable to execute the chart query in ClickHouse. No objects were saved.')
