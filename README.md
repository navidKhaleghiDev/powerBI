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
settings accept all hosts with `ALLOWED_HOSTS = ["*"]`.

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
