# Governed ClickHouse analytics

The React dashboard uses `/api/analytics/`, not the legacy admin-only `/api/kpis/query/` or the independent Cube card. No synthetic amounts are substituted when analytics is unavailable.

## Setup

After pulling the changes, rebuild the Django image to install the locked `jdatetime` dependency, then run migrations explicitly against the application PostgreSQL database:

```bash
docker compose build web
docker compose run --rm web python manage.py migrate
docker compose up -d web
```

`ANALYTICS_USER` and `ANALYTICS_PASSWORD` optionally configure a separate ClickHouse read-only principal. Otherwise the existing `CONSUMER_*` credentials are used with query-level `readonly=1`. Provisioning history always uses `CONSUMER_*`, which needs CREATE TABLE, CREATE VIEW, ALTER and INSERT privileges in `CONSUMER_DATABASE`. When supplying distinct reader credentials, grant access to newly created history tables as well. No database credentials reach the browser. Inject environment values into the web container through deployment configuration; a Compose service does not automatically forward arbitrary host variables.

## Dataset lifecycle

1. Sign in as staff and open **Dashboard → Datasets & mappings**.
2. Create a draft dataset with its business meaning, grain, unit and timezone. Choose a business source table/view in the configured ClickHouse database. Mapping creates a logical business table; it does not copy or mutate the source.
3. Map logical `date` to the approved business date. Map `amount` for the starter sum templates. Other fields are explicit, typed mappings. Define a stable, non-null business key and source version for CDC data. For composite keys, prepare a reviewed source view with a collision-free key; the initial UI accepts one key column.
4. Select starter templates or define a custom sum/count/avg/min/max KPI. Add mapped categorical fields and fixed inclusion values when only approved statuses/document types should qualify. Fixed KPI filters and interactive filters are intersected, never overridden. Complex transforms, joins, currency conversions and recognition policy belong in reviewed business views/marts, not browser SQL.
5. Preview an aggregate for the last 30 days. A zero/empty preview is not financial reconciliation. Review source definitions and reconcile an appropriate period before approval.
6. Optionally start history capture, or supply a pre-existing append-only history table with the same mapped columns/key/version, a non-null recorded timestamp and a trustworthy earliest cutoff.
7. **Approve & publish** makes the dataset visible to all authenticated application users. This release uses a shared approved catalog; it is not tenant-isolated or a per-dataset group-permission system. Only staff can create, change drafts, preview, publish, withdraw or provision history. Withdrawing blocks new data requests. Already delivered browser data cannot be revoked.
8. Published definitions and history-enabled mappings are immutable. Use **New version** to create a new stable dataset identifier. Saved widgets continue to reference their original identifier; withdrawn KPIs show an unavailable state. Ordinary drafts can be edited with revision conflict checks.

A mapping is not proof of financial meaning. `created_at`, invoice totals or receipts must not be labeled recognized income unless the business owner confirms that definition. Formal/informal and cash/credit classifications require real source data. Units and tax treatment must be confirmed; the IRR default is editable, not an inferred property of the source.

The current source inspection found `crm_bi_current` and `crm_bi_raw`, including `id`, `created_at`, `amount`, `document_type`, `status` and CDC metadata. No financial mappings are auto-published from these names.

## Query semantics

`POST /api/analytics/query/`:

```json
{
  "dataset": "approved-income-v1",
  "metric": "income",
  "group_by": ["month"],
  "date_from": "2026-01-01",
  "date_to": "2026-07-01",
  "calendar": "persian",
  "mode": "latest",
  "filters": {"incomeType": ["formal"]},
  "limit": 1000
}
```

- Dates are Gregorian API dates; `date_to` is exclusive. Source timestamps are converted into the dataset's business timezone. Reporting groups use genuine Persian or Gregorian day/month/year boundaries computed by the server. Supported dates: 1970–2100; each request covers at most 3,660 days.
- An empty `group_by` returns a scalar aggregate row for cards. Up to two compatible grouping fields are supported by the API; the initial widget editor exposes one grouping field.
- `latest` resolves the greatest source version per business key using `argMax(tuple(...), version)`. Tuple aggregation preserves null-valued updates. Only after that resolution are deletion, date, fixed KPI and interactive filters applied. Source versions must be strictly ordered for each key; indistinguishable conflicting versions cannot be resolved reliably. Unversioned sources must already contain one row per business key.
- `historical` additionally requires `known_at`, an offset-aware timestamp within retained history, and selects only versions recorded by that cutoff before resolving state. The historical meaning is **recorded by the analytics platform**, not committed in the upstream database. Retroactive financial restatements use latest mode; reporting with older KPI formulas requires selecting the appropriate dataset version.
- Numeric decimals and integers exceeding JavaScript's safe integer range are returned as strings. Cards, tables and CSV preserve the exact text. Chart conversion is approximate and rejects magnitudes outside the safe range.
- Grouped responses are ordered by grouping fields. An extra row detects truncation; `meta.truncated` signals that the result is incomplete. Missing periods are not automatically zero-filled. Empty sums/counts follow ClickHouse aggregate semantics; unknown nullable amounts remain nullable.
- `queried_at` is execution time. `source_freshness` is null because CDC watermark monitoring is not implemented. Do not label it last source update time.
- Value filters use typed ClickHouse parameters. SQL identifiers come only from validated administrator mappings. Queries have time, memory, read-row and output limits. Driver details and credentials are not returned.

`POST /api/analytics/details/` accepts the same period/mode/filter/KPI fields, plus `cursor` and `limit` (default 50, max 100). It returns only mapped fields and an internal `_record_id` for stable pagination, applying the KPI's fixed rules. `meta.next_cursor` is the next page cursor. Results use lexical business-key order. Latest-state pages are separate queries and can change while browsing; use historical mode for a stable retained cutoff. An aggregate table is not a transaction-detail table.

## History capture

`POST /api/analytics/datasets/{id}/enable-history/` is staff-only and restricted to an unpublished draft over a versioned MergeTree/ ReplacingMergeTree source. It creates:

- `analytics_{id}_history`: append-only MergeTree retaining source fields and `__analytics_recorded_at`.
- `analytics_{id}_history_mv`: an insert-triggered materialized view from the source to history.

Capture is installed before seeding existing source rows. Version resolution handles overlap between capture and baseline. `history_start` is set after seeding completes, so earlier historical states are rejected. Existing source tables are never altered. The history table must retain all versions for the advertised period; do not attach TTL/cleanup that invalidates the declared coverage. Withdrawing a dataset does not stop capture or delete history.

This requires CDC changes to arrive as inserted versions, including delete flags. ClickHouse source mutations, partition replacement and direct deletes are not captured by an insert-triggered materialized view. Do not use automatic capture for mutable-in-place pipelines. DDL is nontransactional: failures can leave partial objects; retry reuses them and re-seeds safely through version resolution. Source schema changes require review; history mappings do not evolve automatically. Large baselines may exceed the synchronous 20-second limit and should be provisioned by an operator before setting history coverage.

Sources: [ClickHouse update/version guidance](https://github.com/ClickHouse/clickhouse-docs/blob/main/docs/managing-data/updating-data/overview.mdx), [typed query parameters](https://github.com/ClickHouse/clickhouse-docs/blob/main/docs/guides/developer/stored-procedures-and-prepared-statements.md), [materialized view insert semantics](https://github.com/ClickHouse/ClickHouse/blob/master/docs/get-started/quickstarts/create-your-first-materialized-view.mdx).

## Endpoints

| Method | Endpoint | Access |
| --- | --- | --- |
| GET | `/api/analytics/metadata/` | Signed-in users; published logical metadata only |
| GET | `/api/analytics/sources/` | Staff; configured database table/column catalog |
| GET, POST | `/api/analytics/datasets/` | Staff; list or create drafts |
| PUT | `/api/analytics/datasets/{id}/` | Staff; edit ordinary drafts with revision |
| POST | `/api/analytics/datasets/{id}/preview/` | Staff; source validation and bounded aggregate |
| POST | `/api/analytics/datasets/{id}/publish/` | Staff; validate, approve and publish |
| POST | `/api/analytics/datasets/{id}/unpublish/` | Staff; withdraw and increment revision |
| POST | `/api/analytics/datasets/{id}/enable-history/` | Staff; provision history for a draft |
| POST | `/api/analytics/query/` | Signed-in users; published KPI results |
| POST | `/api/analytics/details/` | Signed-in users; mapped detail records |
| GET, PUT | `/api/analytics/dashboard/` | Signed-in users; their own dashboard only |

Dashboard saves use an optimistic revision. A stale save returns 409 instead of overwriting another session. Sheets, widgets and their logical queries are stored in application PostgreSQL. Date filters are session state. The frontend clears query caches on authentication changes and uses TanStack Query for requests, cancellation, refresh and deduplication.
