---
name: django-rest-framework
description: Develop and review this project's Django REST Framework APIs, request serializers, configured database services, and drf-spectacular documentation.
---

# Django REST Framework

## Discover the implementation

Read `AGENTS.md`, `pyproject.toml`, relevant lockfile entries, and `bi/settings.py`. Inspect the affected viewset, serializers, interface, backend service, schema annotations, and router together. Follow active code; commented metadata queries and unused serializers do not imply implemented endpoints.

## Project flow

`POST body → DatabaseConnectionQuerySerializer → DatabaseServiceFactory.get_service → configured POSTGRES instance → connection_test() → Response`

- Keep service-oriented actions on `GenericViewSet`; use model viewsets when the requested behavior needs model CRUD.
- Keep routers in `apps/api/urls.py`, views in `apps/api/viewset/`, serializers in `apps/api/serializers.py`, and backend logic in `apps/api/service/`. Use canonical `apps.api` and `apps.core` imports.
- Keep routing `@action` decorators in the viewset. Put Swagger annotations in `apps/api/schema.py`, applying the exported `extend_schema_view` decorator to the viewset.
- Keep `/schema/` and `/swagger/` in `bi/urls.py`; API router paths live under `/api/`.

## Connection request and service contract

`POST /api/database/databases/` currently accepts required `db_type`, `host`, `port`, `database`, `username`, and `password` fields. `db_type` is currently limited to `postgres`; port is 1–65535. Password is write-only, preserves whitespace, and allows an empty string.

Validate `request.data` using `is_valid(raise_exception=True)` before forwarding validated keyword arguments to the factory. Send credentials in POST bodies rather than URL parameters.

`DatabaseService` in `apps/api/service/database_interface.py` defines the abstract `connection_test(self) -> dict` contract. The factory selects and instantiates the backend with constructor-supplied settings. `POSTGRES` maps `database` to `dbname` and `username` to `user` in `self.config`.

The service uses Psycopg 3 (`psycopg`), a 5-second connection timeout, context-managed connection/cursor cleanup, and `SELECT 1`. It returns `success` and `message`; the view maps success to HTTP 200 and failure to HTTP 400. Serializer validation failures use DRF's field-error shape; distinguish them from connection failures when refining schema responses.

Keep interface, factory, constructor, serializer, view, and schema aligned when changing the flow. For a new backend, update the implementation, factory mapping, and serializer choices. Define unsupported-backend handling explicitly; API serializer choices currently prevent unsupported factory selections. An unchecked mapping lookup is not a preferred error-handling convention.

Django's own database uses `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT` from the environment. The tested database uses request credentials; preserve this separation.

## Validation and security

- Keep passwords, connection configuration, and raw driver exceptions out of responses, logs, and committed examples.
- Preserve appropriate authentication, permissions, and session CSRF protection when changing endpoints.
- Run `uv run python manage.py check` for API changes. For schema changes, also run `uv run python manage.py spectacular --file /tmp/bi-openapi.yaml --validate --fail-on-warn`.
- If uv is blocked, use `.venv/bin/python manage.py ...` as described in `AGENTS.md`.
- For connection-flow changes, use mocked driver checks for credential forwarding, success/failure results, cleanup, validation, and allowed methods as relevant. Report live connectivity checks separately; do not assume a live database is available.
- Documentation-only edits need no Django test suite. Report changed files, executed validation, and unresolved issues or setup steps.
