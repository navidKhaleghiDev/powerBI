"""OpenAPI annotations for API viewsets."""

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view

from apps.api.serializers import DataTypeQuerySerializer, DataTypeResponseSerializer
from apps.api.serializers import KPIQuerySerializer, KPIResponseSerializer
from apps.api.serializers import KPIAvailableTablesResponseSerializer
from apps.api.serializers import (
    DashboardCreateSerializer, DashboardResponseSerializer, DashboardQueryFailureSerializer,
    KPIChartQuerySerializer,
)


KPI_JOIN_EXAMPLE = {
    'table_name': 'factor_current',
    'dimension': 'source.currency_unit',
    'measure': 'joined.amount_numeric',
    'aggregation': 'sum',
    'join_table_name': 'factor_item_current',
    'join_type': 'INNER',
    'join_left_column': 'id',
    'join_right_column': 'invoice_id',
    'limit': 100,
}

kpi_viewset_schema = extend_schema_view(
    chart_query=extend_schema(
        tags=['KPIs'],
        summary='Execute a saved chart with its filters',
        description=(
            'Loads a chart belonging to the authenticated admin, validates its saved '
            'query and filters, and returns chart axes. Optional limit overrides the '
            'saved limit for this request only. Unknown or other-owner charts return 404.'
        ),
        request=KPIChartQuerySerializer,
        responses={200: KPIResponseSerializer, 400: {'description': 'Invalid configuration or query failure.'},
                   404: {'description': 'Chart not found.'}},
        examples=[OpenApiExample('Saved chart', request_only=True, value={'chart_id': 1}),
                  OpenApiExample('Override group limit', request_only=True, value={'chart_id': 1, 'limit': 50})],
        filters=False,
    ),
    available_tables=extend_schema(
        tags=['KPIs'],
        summary='List available KPI tables and columns',
        description=(
            'Lists tables in the configured ClickHouse database with their engine and '
            'column names and types. Includes MergeTree engines, View and Distributed; '
            'excludes temporary tables and names ending in _raw, _kafka or _mv. '
            'Requires an authenticated admin. Empty results return an empty tables list.'
        ),
        request=None,
        examples=[OpenApiExample(
            'Available tables', response_only=True, status_codes=['200'], value={
                'success': True, 'tables': [{
                    'name': 'factor_item_current', 'engine': 'ReplacingMergeTree',
                    'columns': [{'name': 'invoice_id', 'type': 'Nullable(Int64)'}],
                }],
            },
        )],
        responses={200: KPIAvailableTablesResponseSerializer, 400: KPIAvailableTablesResponseSerializer},
        filters=False,
    ),
    query=extend_schema(
        tags=['KPIs'],
        summary='Query ClickHouse for chart axes',
        description=(
            'Requires an authenticated admin. Send a JSON body. Use the request example '
            'selector below for complete payloads. Discover tables and column types with '
            '`GET /api/kpis/available-tables/`.\n\n'
            '### Fields and aggregation\n\n'
            '- `table_name`: main table, optionally database-qualified.\n'
            '- `dimension`: column used for GROUP BY and the x axis.\n'
            '- `measure`: column to aggregate for the y axis. Omit or send an empty '
            'string for `count(*)`. Other aggregations need a column.\n'
            '- `aggregation`: `sum`, `avg`, `min`, `max`, `count`, or `uniqExact` '
            '(distinct count). `sum` and `avg` require numeric columns.\n'
            '- `limit`: number of groups, 1–1000, default 100.\n\n'
            '### Joining two tables\n\n'
            'Set `join_table_name` and all three required join fields: `join_type`, '
            '`join_left_column`, `join_right_column`. Only `INNER` and `LEFT` are supported. '
            '`INNER` keeps matching rows; `LEFT` keeps all main-table rows. '
            'The join condition is `source.<join_left_column> = joined.<join_right_column>`. '
            'Join column fields are plain column names without aliases.\n\n'
            'In `dimension`, `measure`, and filter `column`, use `source.column` for '
            'the main table or `joined.column` for the joined table. A plain column '
            'name defaults to the main table. `dimension_table` and `measure_table` '
            'are not supported fields. Only one equality join is supported.\n\n'
            '### WHERE filters\n\n'
            '`filters` is an optional list of up to 50 conditions, combined with **AND** '
            'before GROUP BY. Each condition contains `column`, `operator`, and, '
            'except for null checks, `value`. Values are bound as query parameters.\n\n'
            '| Operator | Meaning | Value |\n'
            '| --- | --- | --- |\n'
            '| `eq`, `ne` | Equal, not equal | String, number, or boolean |\n'
            '| `gt`, `gte`, `lt`, `lte` | Greater/less than, optionally equal | Scalar |\n'
            '| `in`, `not_in` | Included/excluded values | Nonempty list, maximum 1000 scalars |\n'
            '| `like` | SQL pattern match | String; `%` matches any sequence, `_` one character |\n'
            '| `is_null`, `is_not_null` | NULL checks | Omit `value` entirely |\n\n'
            'Use null operators instead of `value: null`. OR groups, raw SQL, and HAVING '
            'are not supported. Filters on joined columns after a LEFT JOIN can exclude '
            'unmatched main rows. Multiple matching joined rows contribute separately '
            'to the aggregate.\n\n'
            '### Response\n\n'
            '`x` contains dimensions; `y` contains aggregate values at matching indexes, '
            'ordered by dimension. Empty results return empty axes. Large integers and '
            'decimals may be JSON strings. HTTP 400 returns field validation errors or '
            '`success: false` with empty axes and a generic execution message. '
            'The query does not automatically deduplicate ReplacingMergeTree versions '
            'or exclude rows marked `is_deleted`; add explicit filters as needed.'
        ),
        request=KPIQuerySerializer,
        responses={200: KPIResponseSerializer, 400: {
            'description': 'Field validation errors or success=false with empty axes and a generic message.'
        }},
        examples=[
            OpenApiExample('Query with filters', request_only=True, value={
                **KPI_JOIN_EXAMPLE,
                'filters': [
                    {'column': 'source.status', 'operator': 'eq', 'value': 'convert_to_receipt'},
                    {'column': 'joined.quantity', 'operator': 'gte', 'value': 1},
                    {'column': 'joined.amount_numeric', 'operator': 'is_not_null'},
                ],
            }),
            OpenApiExample('Single table — sum', request_only=True, value={
                'table_name': 'factor_item_current', 'dimension': 'invoice_id',
                'measure': 'amount_numeric', 'aggregation': 'sum', 'limit': 100,
            }),
            OpenApiExample('Count invoices by status', request_only=True, value={
                'table_name': 'factor_current', 'dimension': 'status',
                'aggregation': 'count', 'limit': 100,
            }),
            OpenApiExample('Distinct invoices by currency', request_only=True, value={
                'table_name': 'factor_current', 'dimension': 'currency_unit',
                'measure': 'id', 'aggregation': 'uniqExact', 'limit': 100,
            }),
            OpenApiExample('INNER JOIN — item amounts by currency', request_only=True,
                           value=KPI_JOIN_EXAMPLE),
            OpenApiExample('LEFT JOIN — keep all invoices', request_only=True,
                           value={**KPI_JOIN_EXAMPLE, 'join_type': 'LEFT'}),
            OpenApiExample('Join with equality and numeric filters', request_only=True, value={
                **KPI_JOIN_EXAMPLE, 'filters': [
                    {'column': 'source.status', 'operator': 'eq', 'value': 'convert_to_receipt'},
                    {'column': 'joined.quantity', 'operator': 'gt', 'value': 0},
                ],
            }),
            OpenApiExample('IN, LIKE and NULL filters', request_only=True, value={
                **KPI_JOIN_EXAMPLE, 'filters': [
                    {'column': 'source.status', 'operator': 'in', 'value': ['convert_to_receipt']},
                    {'column': 'source.currency_unit', 'operator': 'like', 'value': '%'},
                    {'column': 'joined.amount_numeric', 'operator': 'is_not_null'},
                ],
            }),
            OpenApiExample('Numeric range', request_only=True, value={
                'table_name': 'factor_item_current', 'dimension': 'invoice_id',
                'measure': 'amount_numeric', 'aggregation': 'avg',
                'filters': [
                    {'column': 'quantity', 'operator': 'gte', 'value': 1},
                    {'column': 'quantity', 'operator': 'lte', 'value': 100},
                ], 'limit': 100,
            }),
            OpenApiExample('Chart axes', response_only=True, status_codes=['200'], value={
                'success': True, 'x': ['Germany', 'US'], 'y': [350, 1200],
            }),
        ],
        filters=False,
    ),
)


DASHBOARD_CREATE_EXAMPLE = {
    'title': 'Invoice analytics',
    'description': 'Item totals by invoice',
    'charts': [{
        'title': 'Amounts by invoice', 'chart_type': 'bar',
        'x_label': 'Invoice', 'y_label': 'Total amount', 'position': 0,
        'table_name': 'factor_item_current', 'dimension': 'invoice_id',
        'measure': 'amount_numeric', 'aggregation': 'sum',
        'filters': [
            {'column': 'quantity', 'operator': 'gte', 'value': 1},
            {'column': 'amount_numeric', 'operator': 'gt', 'value': 100},
        ],
        'limit': 100,
    }],
}

kpi_dashboard_schema = extend_schema_view(
    create_dashboard=extend_schema(
        tags=['Dashboards'], summary='Create a dashboard with charts and filters',
        description=(
            'Requires an authenticated admin. Saves a dashboard, 1–50 charts, and each '
            'chart’s filter rows atomically. Owner is the authenticated user. Each chart '
            'uses the same query fields and validation as POST /api/kpis/query/. '
            'Executes every submitted chart query in ClickHouse before saving any objects. '
            'If any query fails, returns HTTP 400 with a zero-based chart_index and saves '
            'nothing. Empty query results count as success. After successful execution, '
            'saves all objects in one database transaction. Use /api/kpis/chart-query/ with a returned '
            'chart ID to execute it. Chart types: bar, line, pie, table, number. '
            'Positions control chart ordering; filters retain request order. '
            'Axis labels are optional. Null-check filters omit value in requests.'
        ),
        request=DashboardCreateSerializer,
        responses={201: DashboardResponseSerializer, 400: OpenApiResponse(
            response=DashboardQueryFailureSerializer,
            description=(
                "ClickHouse failure with a zero-based chart_index; nothing is saved. "
                "Invalid input instead returns DRF field validation errors."
            ),
        )},
        examples=[
            OpenApiExample('Dashboard with filtered chart', request_only=True, value=DASHBOARD_CREATE_EXAMPLE),
            OpenApiExample('Dashboard with join chart', request_only=True, value={
                'title': 'Invoice currencies',
                'charts': [{**KPI_JOIN_EXAMPLE, 'title': 'Amounts by currency',
                            'chart_type': 'bar', 'filters': [
                                {'column': 'joined.quantity', 'operator': 'gte', 'value': 1},
                            ]}],
            }),
        ],
    ),
    dashboards=extend_schema(
        tags=['Dashboards'], summary='List your dashboards with charts and filters',
        description='Requires an authenticated admin. Returns only dashboards owned by the current user.',
        responses={200: DashboardResponseSerializer(many=True)}, filters=False,
    ),
    dashboard=extend_schema(
        tags=['Dashboards'], summary='Retrieve your dashboard with charts and filters',
        parameters=[OpenApiParameter('dashboard_id', int, OpenApiParameter.PATH)],
        description='Requires an authenticated admin. Unknown or other-owner dashboards return 404.',
        responses={200: DashboardResponseSerializer, 404: {'description': 'Dashboard not found.'}},
        filters=False,
    ),
)


data_type_viewset_schema = extend_schema_view(
    list=extend_schema(
        tags=["Database types"],
        summary="List data types for a database backend",
        description=(
            "Returns database type entries in declaration order. Each entry contains a "
            "lowercase identifier in `name` and the backend type string in `value`. "
            "Results are not paginated. Authentication is not required."
        ),
        parameters=[DataTypeQuerySerializer],
        responses={
            200: DataTypeResponseSerializer(many=True),
            400: {
                "type": "object",
                "properties": {
                    "db_type": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        filters=False,
    ),
)
