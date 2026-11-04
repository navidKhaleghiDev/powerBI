---
name: django-rest-framework
description: Develop and review this project's DRF database connection and metadata APIs, service interfaces and factories, serializers, and drf-spectacular schemas.
---

# Django REST Framework

## Discovery and scope

Read `AGENTS.md`, installed/locked dependencies, settings, and the affected router, viewset, serializers, schema, service interface, and backend together. The repository's endpoint table and detailed conventions are in `AGENTS.md`; use active code to verify them.

The current API is stateless. Connection credentials are not persisted. `DataBase` and its CRUD endpoints were removed; keep migration history through `core.0007` intact and do not restore persistence unless requested. The unmanaged API placeholder and older serializers do not imply active model endpoints.

## Implement the existing flow

`POST request.data → serializer validation → factory → configured service → result dict → HTTP response`

- Keep `GenericViewSet` actions in `apps/api/viewset/`, routers in `apps/api/urls.py`, payloads in `apps/api/serializers.py`, SQL and connection logic in `apps/api/service/`, and shared `DatabaseType` choices in `apps/core/choices.py`. Use canonical package imports.
- Preserve routing `@action` decorators on methods. Define Swagger annotations with `extend_schema_view` in `apps/api/schema.py`, applied through `@database_viewset_schema`. Project-wide `/schema/` and `/swagger/` routes belong in `bi/urls.py`.
- Use `DatabaseConnectionQuerySerializer` for `/api/database/databases/` and `/api/database/tables/`. Use its subclass `DatabaseColumnsQuerySerializer` for `/api/database/columns/`.
- Validate `request.data` with `is_valid(raise_exception=True)`. For columns, copy validated data and pop `table` before factory invocation; send the qualified table separately to `get_columns(table)`.
- The ABC `DatabaseService` declares `connection_test`, `get_tables`, and `get_columns`. The factory creates a new configured implementation or returns `None`; views must return HTTP 400 for unsupported implementations. Do not assume its current annotation fully describes its nullable result.
- Serializer choices include `postgresql`, `mysql`, `clickhouse`, and `mssql`, but only `postgresql` maps to `POSTGRES`. When adding a backend, align the implementation, abstract contract, factory, validation, schema, and checks.
- The configured service owns credentials and SQL. Use Psycopg 3 context managers and the existing 5-second connection timeout. Parameterize SQL values; preserve stable schema/table and ordinal column ordering.

## Match runtime response shapes

The connection test returns `success` and `message`. Table listing returns `success`, `database`, and a list of `schema.table` strings from `pg_tables`; it does not include views or nested columns. Column listing returns `success`, `database`, `table`, and column objects with `name`, `type`, `nullable`, `default`, `max_length`, `precision`, and `scale`.

Views map service success to HTTP 200 and service failure to 400. Driver failures return generic messages and empty lists. Validation failures use DRF field errors; unsupported backends return an `error` object. Document these shapes deliberately.

Known drift: the table response serializer and Swagger description still describe the previous nested-column/view format, and the interface table docstring is stale. Treat actual service output as evidence, not stale descriptions. Correct those definitions when the task includes that area; do not expand documentation-only work into runtime changes.

## Security and validation

- Send passwords in POST bodies, keep them write-only, preserve whitespace and allowed empty strings, and never return/log credentials or raw driver errors. Target request credentials are independent of Django's `POSTGRES_*` environment settings.
- Preserve appropriate authentication, permissions, and CSRF protection. Current viewset permissions are not explicitly configured; do not claim it enforces authentication.
- For Python changes, check syntax and run `uv run python manage.py check`. For schema changes, run `uv run python manage.py spectacular --file /tmp/bi-openapi.yaml --validate --fail-on-warn`.
- Use `.venv/bin/python` when uv cannot run, as described in `AGENTS.md`. For model changes, follow its migration commands and preserve applied history.
- For service/API changes, mock the driver to check credential forwarding, parameterized queries, result mapping, empty lists, failures, cleanup, and serializer rejection as relevant. Verify schema shapes separately from schema validity. Distinguish live connectivity from mocked checks.
- Documentation-only updates need no Django test suite. Report changed files, executed validation, and unresolved findings accurately.
