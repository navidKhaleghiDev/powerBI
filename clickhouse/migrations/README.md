# Invoice-item join migration

`001_factor_item_invoice_id.sql` updates the existing `financial_analytics`
pipeline from `crm.public.finance_invoiceitem` into `factor_item_current`.
The source column is `invoice_id` (not `invoice_ide`). Debezium's `crm`
connector already captures this table without a column filter.

The SQL preserves raw/current data and reuses the existing Kafka consumer group.
It briefly stops the item reader while recreating its schema and updating the
materialized views. Run with the configured ClickHouse user:

```bash
docker compose exec -T clickhouse sh -c 'clickhouse-client --user "$CLICKHOUSE_USER" --password "$CLICKHOUSE_PASSWORD" --multiquery' < clickhouse/migrations/001_factor_item_invoice_id.sql
```

For future consumer provisioning, include this column in the item mapping:

```json
{"source": "invoice_id", "target": "invoice_id", "type": "Nullable(Int64)"}
```

Existing rows require a separate source-backed backfill of `id` to `invoice_id`
in both `factor_item_raw` and `factor_item_current`. Adding the column alone
leaves these historical references NULL. The local migration was applied and
all 66 current items were backfilled on 2026-11-14.

The KPI join is `factor_current.id = factor_item_current.invoice_id`.
