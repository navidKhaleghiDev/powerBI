
CREATE DATABASE IF NOT EXISTS financial_analytics;

-- -- ==========================================
-- -- 1. Raw CDC Events
-- -- ==========================================

-- CREATE TABLE IF NOT EXISTS financial_analytics.orders_raw
-- (
--     record_id Int32,
--     client_name Nullable(String),
--     total_amount Nullable(Int32),
--     item_name Nullable(String),
--     __deleted String DEFAULT 'false',
--     __op String DEFAULT '',
--     __lsn UInt64 DEFAULT 0
-- )
-- ENGINE = MergeTree()
-- ORDER BY record_id;


-- -- ==========================================
-- -- 2. Current State
-- -- ==========================================

-- CREATE TABLE IF NOT EXISTS financial_analytics.orders_current
-- (
--     record_id Int32,
--     client_name Nullable(String),
--     total_amount Nullable(Int32),
--     item_name Nullable(String),
--     version UInt64,
--     is_deleted UInt8
-- )
-- ENGINE = ReplacingMergeTree(version)
-- ORDER BY record_id;


-- -- ==========================================
-- -- 3. Raw -> Current
-- -- ==========================================

-- CREATE MATERIALIZED VIEW IF NOT EXISTS
-- financial_analytics.orders_current_mv
-- TO financial_analytics.orders_current
-- AS
-- SELECT
--     record_id,
--     client_name,
--     total_amount,
--     item_name,
--     __lsn AS version,
--     if(
--         __deleted = 'true' OR __op = 'd',
--         1,
--         0
--     ) AS is_deleted
-- FROM financial_analytics.orders_raw
-- WHERE record_id > 0;


-- -- ==========================================
-- -- 4. Kafka Source
-- -- ==========================================

-- CREATE TABLE IF NOT EXISTS financial_analytics.orders_kafka
-- (
--     id Int32,
--     customer_name Nullable(String),
--     amount Nullable(Int32),
--     product_name Nullable(String),
--     __deleted String,
--     __op String,
--     __lsn UInt64
-- )
-- ENGINE = Kafka
-- SETTINGS
--     kafka_broker_list = 'kafka:29092',
--     kafka_topic_list = 'bi.public.orders',
--     kafka_group_name = 'clickhouse-orders',
--     kafka_format = 'JSONEachRow',
--     input_format_skip_unknown_fields = 1,
--     kafka_num_consumers = 1;


-- -- ==========================================
-- -- 5. Kafka -> Raw
-- -- ==========================================

-- CREATE MATERIALIZED VIEW IF NOT EXISTS
-- financial_analytics.orders_mv
-- TO financial_analytics.orders_raw
-- AS
-- SELECT
--     id AS record_id,
--     customer_name AS client_name,
--     amount AS total_amount,
--     product_name AS item_name,
--     if(
--         __deleted = 'true' OR __op = 'd',
--         'true',
--         'false'
--     ) AS __deleted,
--     __op,
--     __lsn
-- FROM financial_analytics.orders_kafka;
