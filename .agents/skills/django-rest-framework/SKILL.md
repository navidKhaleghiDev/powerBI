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

- Keep `GenericViewSet` actions in `apps/api/viewset/`, KPI routing in `apps/api/urls.py` and existing database/Connect/consumer routing in `apps/core/urls.py`. Existing database/Connect payloads are in `apps/core/serializers.py`, KPI/consumer payloads in `apps/api/serializers.py`. Keep SQL and connections in owning-app services (`apps/core/service/` or `apps/kpi/service/`), and shared `DatabaseType` choices in `apps/core/choices.py`. Use canonical package imports.
- Preserve routing `@action` decorators on methods. Define Swagger annotations with `extend_schema_view` in the existing schema module (`apps/core/schema.py` for database actions and `apps/api/schema.py` for KPIs), applied through `@database_viewset_schema`. Project-wide `/schema/` and `/swagger/` routes belong in `bi/urls.py`.
- Use `DatabaseConnectionQuerySerializer` for `/api/database/connection-test/` and `/api/database/tables/`. Use its subclass `DatabaseColumnsQuerySerializer` for `/api/database/columns/`.
- Validate `request.data` with `is_valid(raise_exception=True)`. For columns, copy validated data and pop `table` before factory invocation; send the qualified table separately to `get_columns(table)`.
- The ABC `DatabaseService` declares `connection_test`, `get_tables`, and `get_columns`. The factory creates a new configured implementation or returns `None`; views must return HTTP 400 for unsupported implementations. Do not assume its current annotation fully describes its nullable result.
- Serializer choices include `postgresql`, `mysql`, `clickhouse`, and `mssql`, but only `postgresql` maps to `POSTGRES`. When adding a backend, align the implementation, abstract contract, factory, validation, schema, and checks.
- The configured service owns credentials and SQL. Use Psycopg 3 context managers and the existing 5-second connection timeout. Parameterize SQL values; preserve stable schema/table and ordinal column ordering.

Celery task entry points belong in `apps/worker/`. When adding asynchronous execution, also read [the Celery worker skill](../celery-worker/SKILL.md). Preserve the synchronous API contract unless the requested feature changes it.

## Match runtime response shapes

The connection test returns `success` and `message`. Table listing returns `success`, `database`, and a list of `schema.table` strings from `pg_tables`; it does not include views or nested columns. Column listing returns `success`, `database`, `table`, and column objects with `name`, `type`, `consumer_type`, `nullable`, `default`, `max_length`, `precision`, and `scale`.

Views map service success to HTTP 200 and service failure to 400. Driver failures return generic messages and empty lists. Validation failures use DRF field errors; unsupported backends return an `error` object. Document these shapes deliberately.

Known drift: the table response serializer and Swagger description still describe the previous nested-column/view format. Treat actual service output as evidence, not stale descriptions. Correct those definitions when the task includes that area; do not expand documentation-only work into runtime changes.

## Security and validation

- Do not create, add, or modify automated tests unless the user explicitly requests them. Do not run test suites unless explicitly requested. Existing tests must remain untouched unless their modification or removal is requested. Use syntax checks, Django system checks, schema validation, or configuration validation as appropriate instead.

- Send passwords in POST bodies, keep them write-only, preserve whitespace and allowed empty strings, and never return/log credentials or raw driver errors. Target request credentials are independent of Django's `POSTGRES_*` environment settings.
- Preserve appropriate authentication, permissions, and CSRF protection. `DatabaseViewSet` and `KPIViewSet` require `IsAuthenticated` and `IsAdminUser`; verify each affected viewset.
- For Python changes, check syntax and run `uv run python manage.py check`. For schema changes, run `uv run python manage.py spectacular --file /tmp/bi-openapi.yaml --validate --fail-on-warn`.
- Use `.venv/bin/python` when uv cannot run, as described in `AGENTS.md`. For model changes, follow its migration commands and preserve applied history.
- For service/API changes, inspect credential forwarding, parameterized queries, result mapping, empty lists, failures, cleanup, and serializer validation. Verify schema shapes separately from schema validity. Do not introduce mocked tests unless explicitly requested.
- Documentation-only updates need no Django test suite. Report changed files, executed validation, and unresolved findings accurately.

## Container execution

Compose `web` builds `Dockerfile.dev` and connects to application PostgreSQL
`db`. The independent `postgres` service is the CDC source. Django migrations
belong on `db`; request-supplied source credentials are separate. See the
[Docker skill](../docker-development/SKILL.md) for image and networking changes.
