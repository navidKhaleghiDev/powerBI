# BI

A Django project with a `core` application, a DRF API app, and PostgreSQL-backed configuration via environment variables.

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/) for dependency management
- PostgreSQL running locally or remote and accessible by the configured credentials

Dependencies are declared in `pyproject.toml` and locked in `uv.lock`. The project uses Django 5.2 and Django REST Framework.

## Local setup

1. Copy the sample environment file:

```bash
cp .env.example .env
```

2. Update `.env` with your local PostgreSQL values.

3. Run these commands from the project root:

```bash
uv sync --locked
uv run python manage.py migrate
uv run python manage.py init_databases
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

`init_databases` creates only the PostgreSQL entry in the `DatabaseCatalog` catalog with category `sql`.
It is safe to run again; existing entries are preserved.

For testing from another device, run `uv run python manage.py runserver 0.0.0.0:8000`.
The VS Code launch configuration also listens on all interfaces. Local development
settings accept all hosts with `ALLOWED_HOSTS = ["*"]` and allow browser requests
from all origins with `CORS_ALLOW_ALL_ORIGINS = True` using `django-cors-headers`.

Open http://127.0.0.1:8000/ to view the development server, or http://127.0.0.1:8000/admin/ to sign in with your superuser account.

The API routes are available under `/api/` and the main database metadata endpoints are registered through the API router.

Open http://127.0.0.1:8000/swagger/ for interactive Swagger documentation.
The OpenAPI schema is available at `/schema/`. Database documentation covers
testing connections using credentials supplied in a POST request body.

`POST /api/database/databases/` tests a connection using a JSON body:

```json
{
  "db_type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "bi",
  "username": "postgres",
  "password": "your-password"
}
```

Returns `success` and `message`, with HTTP 200 on success or 400 on failure.

Connection tests do not save connection records or passwords.

`POST /api/database/columns/` accepts the connection body plus `table`, for
example `"table": "public.orders"`. It returns `success`, `database`, `table`,
and `columns` with each column's name, type, nullable flag, default, maximum
length, precision, and scale. Invalid table names or database failures return
HTTP 400.

Each column also includes `consumer_type`, a suggested ClickHouse destination type; `type`
keeps the original PostgreSQL type. Common mappings include `smallint` → `Int16`,
`integer` → `Int32`, `bigint` → `Int64`, `real` → `Float32`,
`double precision` → `Float64`, `boolean` → `Bool`, text/JSON → `String`,
`uuid` → `UUID`, and `date` → `Date32`. Timestamps use
`DateTime64(datetime_precision)`, with UTC for timestamps with time zone.
Constrained `numeric` columns use `Decimal(precision, scale)` when precision is
1–76 and scale is between 0 and precision. Nullable columns use `Nullable(T)`.
Arrays, user-defined types, unconstrained or unsupported numeric definitions,
and other unmapped types return `consumer_type: null` for manual mapping.
These suggestions do not transform CDC payloads or guarantee that all source
values fit destination date/time ranges.

`POST /api/database/tables/` accepts the same connection body and returns
`success`, `database`, and `tables`. Each table contains `schema_name`,
`table_name`, and a `columns` list with names, data types, lengths, and numeric
precision/scale. Results include accessible user tables and views, exclude
system schemas, and preserve column order. Failed metadata queries return
HTTP 400 with `success: false`, an empty table list, and a generic message.

## Environment variables

The project reads PostgreSQL settings from environment variables defined in `.env`:

```env
POSTGRES_DB=bi
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## Project structure

```text
bi/
├── apps/
│   ├── api/           # DRF API app, routers, viewsets, serializers, services
│   └── core/          # Application models, views, admin, and migrations
├── bi/
│   ├── settings.py    # Django configuration
│   ├── urls.py        # Root URL configuration
│   ├── asgi.py        # ASGI entry point
│   └── wsgi.py        # WSGI entry point
├── .env.example       # Sample environment configuration
├── manage.py          # Django management commands
├── pyproject.toml     # Python version and dependencies
└── uv.lock            # Locked dependency versions
```

## Development commands

Check project configuration:

```bash
uv run python manage.py check
```

After changing models, create and apply migrations:

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

Run tests:

```bash
uv run python manage.py test
```

## Deployment

The current settings are configured for local development. Before deploying, configure a private production `SECRET_KEY`, set `DEBUG = False`, populate `ALLOWED_HOSTS`, and configure production database and static file handling.

Database types are defined by `DatabaseType` in `apps/core/choices.py`: `postgresql`,
`mysql`, `clickhouse`, and `mssql`. Only PostgreSQL currently has a service
implementation. Migration `core.0002` converts stored `postgres` values to `postgresql`.

Database types share the `DatabaseCatalog` model, categorized as `sql`, `analytic`,
or `nosql`. The existing catalog list APIs filter by category and include it in
each result. Migration `core.0007` copies names and image paths from the former
three tables; catalog IDs may change during consolidation.

The public catalog endpoint is `GET /api/database-types/`. It replaces the three
category-specific catalog URLs. Use `?category=sql`, `?category=analytic`, or
`?category=nosql` to filter the category, `?db_type=postgresql` for an exact database type,
`?search=post` for database type search, `?ordering=-db_type` for sorting, and `?page=2`
for pagination. Ordering supports `db_type`, `category`, and `id`.

## Kafka UI

### PostgreSQL test source

Start the test source with `docker compose up -d postgres`.
It creates `financial_db` with local test credentials `postgres` / `postgres`
and enables logical replication with four WAL senders and replication slots.
Connect from the host at `localhost:5433`; Kafka Connect uses `postgres:5432`
on the shared `bi-net` network.

Add test tables and seed data to `postgres/init.sql` before the first startup.
The script runs only when the `pg_data` volume is first initialized; changes to
the script do not automatically run against an existing database.

### pgAdmin

Run `docker compose up -d pgadmin`, then open http://localhost:5050.
The local development login is hardcoded in Compose: email `admin@example.com`,
password `admin`.
The web port is bound to localhost, and pgAdmin settings persist in the
`pgadmin_data` volume. The login variables initialize the account on first startup;
change an existing account's password through pgAdmin.

Use **Register > Server** to add the Compose PostgreSQL instance with host
`postgres`, port `5432`, maintenance database `financial_db`, and the local test
credentials documented above. Give the server any display name.

### Kafka management UI

Start Kafka, Kafka Connect, and Kafka UI with `docker compose up -d kafka-ui`.
Open http://localhost:8081 to inspect topics, partitions, messages, consumer groups,
and connectors in the `bi` cluster. Kafka UI uses `kafka:29092` and
`http://connect:8083` on `bi-net`; its web port is bound to all network interfaces.
The existing Debezium UI remains available on port 8080.

### ClickHouse

Start ClickHouse with `docker compose up -d clickhouse`.
The `financial_analytics` database is created automatically and stored in the
`clickhouse_data` volume. HTTP is available at `http://localhost:8123`, and the
native protocol at `localhost:9002`. Other containers use `clickhouse:8123` or
`clickhouse:9000` on `bi-net`; ClickHouse can reach Kafka at `kafka:29092`.

Local test credentials are hardcoded in Compose: user `bi`, password `clickhouse`.
The service mounts `clickhouse/init.sql` to initialize the raw events table,
current state table, Kafka source, and materialized views. Starting ClickHouse
also starts Kafka. The consumer reads `bi.public.orders`, matching the connector's
`topic.prefix: bi`, with unwrapped JSON records containing `__deleted`, `__op`,
and `__lsn`.

For the Compose PostgreSQL source, configure the connector with
`database.hostname: postgres` and `database.port: 5432`. The supplied external
host and port `5433` apply only when connecting through that host's published port.
Keep the connector password in your local configuration.

To apply the SQL manually to an existing running ClickHouse instance:

```bash
docker compose exec -T clickhouse sh -c 'clickhouse-client --user "$CLICKHOUSE_USER" --password "$CLICKHOUSE_PASSWORD" --multiquery' < clickhouse/init.sql
```

The SQL uses `IF NOT EXISTS`, so it does not update existing table definitions.
If `orders_kafka` already uses the old topic, change it explicitly:

```sql
ALTER TABLE financial_analytics.orders_kafka
MODIFY SETTING kafka_topic_list = 'bi.public.orders';
```

Query the latest non-deleted orders with:

```sql
SELECT * FROM financial_analytics.orders_current FINAL WHERE is_deleted = 0;
```

### Provision consumer pipelines through the API

For the supplied Compose stack, run Django on the host with `CONSUMER_HOST=localhost`,
`CONSUMER_PORT=8123`, `CONSUMER_USER=bi`, `CONSUMER_PASSWORD=clickhouse`, and
`CONSUMER_DATABASE=financial_analytics`. If Django runs on `bi-net`, use
`CONSUMER_HOST=clickhouse`. ClickHouse uses `CLICKHOUSE_KAFKA_BROKERS=kafka:29092`
to reach Kafka over PLAINTEXT, without SASL credentials. These broker addresses
are resolved by ClickHouse, not Django.

`ConsumerServiceFactory` selects the destination implementation using `db_type`,
which defaults to `clickhouse`. Only ClickHouse consumers are implemented;
other recognized database types return HTTP 400 without provisioning objects.
Services return a result body and HTTP status, following the Connect service pattern.

Send `POST /api/consumer/pipelines/` with a staff user's JWT access token
in the `Authorization: Bearer <token>` header:

```json
{
  "warehouse_name": "financial_analytics",
  "table.include.list": "public.orders",
  "topic.prefix": "bi",
  "tables": [
    {
      "source_table": "public.orders",
      "target_table": "sales",
      "columns": [
        {"source": "id", "target": "record_id", "type": "Int32"},
        {"source": "customer_name", "target": "client_name", "type": "Nullable(String)"},
        {"source": "amount", "target": "total_amount", "type": "Nullable(Int32)"},
        {"source": "product_name", "target": "item_name", "type": "Nullable(String)"}
      ],
      "order_by": ["record_id"]
    }
  ]
}
```

The client supplies `warehouse_name` in the request body. It selects the existing
destination database; the API does not create it. Responses identify it as
`database`. Django connects using `CONSUMER_HOST`,
`CONSUMER_PORT`, `CONSUMER_USER`, and `CONSUMER_PASSWORD` from `.env`;
`CLICKHOUSE_KAFKA_BROKERS` must be reachable from ClickHouse.
No PostgreSQL connection is made and no Kafka Connect connector is created.

For each client-supplied target table name, the API creates `<name>_raw`,
`<name>_current`, `<name>_kafka`, `<name>_current_mv`, and `<name>_mv`.
Send `table.include.list` as comma-separated literal schema-qualified names and
`topic.prefix` as a string. Each source consumes `<topic.prefix>.<schema>.<table>`.
For example, `public.orders` and `bi` produce `bi.public.orders`.
Each entry in `tables` supplies `source_table` (schema-qualified), `target_table`,
column mappings, and `order_by`. Source tables must match the include list exactly.
Source tables and target tables must each be unique; regex include patterns are
rejected. Different schemas may contain the same source table name when mapped
to distinct target tables.
Each Kafka source uses one consumer and a separate group per database, table,
and generated topic.

Each column specifies `source`, `target`, and `type`. Kafka tables use source
names. Raw and current tables use target names; the Kafka-to-raw view applies
the aliases. For example, `customer_name` becomes `client_name` in `sales_raw`
and `sales_current`. Supply ClickHouse types:
integer and floating-point types, String, Bool, UUID, Date, Date32, DateTime,
DateTime64(precision), Decimal(precision, scale), or Nullable wrappers.
Other type expressions are rejected. Table and column names must be simple
SQL identifiers. `order_by` must list unique, non-nullable target column names from the
same table; use the source row's stable unique key, including all parts of a
composite key, so updates and deletes replace the correct row.

Debezium fields `__deleted`, `__op`, and `__lsn` are added automatically;
current tables also add `version` and `is_deleted`. These names are reserved.
The Kafka messages must contain the supplied columns and unwrapped CDC metadata.
SQL is generated directly from validated input; no SQL template file is read.

Success returns HTTP 200 with `success`, `database`, and `tables` (completed
target table names). Existing objects are preserved with `IF NOT EXISTS`; repeating
a request does not change their definitions or topics. Driver failures return
HTTP 400 with a generic message and completed table names. DDL is not
transactional: a failed table may have partially created objects. This endpoint
does not verify Kafka connectivity or that events have been consumed.

Connector configuration uses the Debezium UI proxy for cluster `1`:
`GET /api/connect/{source}/config/` calls
`DEBEZIUM_UI_URL/api/connectors/1/{source}/config`.
Set `DEBEZIUM_UI_URL=http://localhost:8080` in `.env`, or replace `localhost`
with the Debezium UI server IP when it runs on another machine.
