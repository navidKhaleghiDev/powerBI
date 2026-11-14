-- Existing Debezium topic: crm.public.finance_invoiceitem; source key: invoice_id.
-- Stop ingestion while updating the projections. Data tables and Kafka offsets remain.
DROP VIEW IF EXISTS financial_analytics.factor_item_mv;

ALTER TABLE financial_analytics.factor_item_raw ADD COLUMN IF NOT EXISTS invoice_id Nullable(Int64);
ALTER TABLE financial_analytics.factor_item_current ADD COLUMN IF NOT EXISTS invoice_id Nullable(Int64);
-- Kafka storage does not support ADD COLUMN. Recreate its reader with the same
-- consumer group so Kafka retains its committed offsets.
DROP TABLE IF EXISTS financial_analytics.factor_item_kafka;
CREATE TABLE financial_analytics.factor_item_kafka
(
    id Int64,
    created_at DateTime64(6, 'UTC'),
    amount_numeric Nullable(Decimal(15, 2)),
    quantity Int64,
    invoice_id Nullable(Int64),
    __deleted String,
    __op String,
    __lsn UInt64
)
ENGINE = Kafka SETTINGS
    kafka_broker_list = 'kafka:29092',
    kafka_topic_list = 'crm.public.finance_invoiceitem',
    kafka_security_protocol = 'plaintext',
    kafka_group_name = 'clickhouse-financial_analytics-factor_item-crm.public.finance_invoiceitem',
    kafka_format = 'JSONEachRow',
    date_time_input_format = 'best_effort',
    input_format_skip_unknown_fields = 1,
    kafka_num_consumers = 1;

ALTER TABLE financial_analytics.factor_item_current_mv MODIFY QUERY
SELECT id, created_at, amount_numeric, quantity, invoice_id, __lsn AS version,
       if(__deleted = 'true' OR __op = 'd', 1, 0) AS is_deleted
FROM financial_analytics.factor_item_raw;

CREATE MATERIALIZED VIEW financial_analytics.factor_item_mv
TO financial_analytics.factor_item_raw AS
SELECT id, created_at, amount_numeric, quantity, invoice_id,
       if(__deleted = 'true' OR __op = 'd', 'true', 'false') AS __deleted,
       __op, __lsn
FROM financial_analytics.factor_item_kafka;

-- Existing rows need a separate backfill from source id -> invoice_id mappings.
-- NULL deliberately marks historical rows whose invoice reference is not known.
