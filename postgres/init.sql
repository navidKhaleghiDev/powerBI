-- CREATE ROLE debezium
-- WITH REPLICATION LOGIN PASSWORD 'pass';
-- GRANT CONNECT ON DATABASE financial_db TO debezium;
-- GRANT USAGE ON SCHEMA public TO debezium;

-- CREATE TABLE public.orders (
--     id SERIAL PRIMARY KEY,
--     customer_name VARCHAR(100),
--     amount INTEGER,
--     product_name VARCHAR(150)
-- );

-- GRANT SELECT ON ALL TABLES
-- IN SCHEMA public TO debezium;

-- CREATE PUBLICATION dbz_publication
-- FOR TABLE public.orders;
