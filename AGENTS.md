# Repository guidance

## Project layout

- This is the `bi` Django project, managed with `uv`. Read `pyproject.toml` and `uv.lock` for current dependency versions; the project currently requires Python 3.13+ and Django 5.2.
- Run commands from the repository root, alongside `manage.py`.
- `bi/settings.py` contains settings, `bi/urls.py` contains root routes, and `bi/asgi.py` and `bi/wsgi.py` expose application entry points.
- `apps/api/` is the dedicated DRF API app. Keep API routes, viewsets, serializers, and service logic under this package instead of the core app.
- Correct API structure:
  - `apps/api/urls.py` for router registration
  - `apps/api/viewset/database_viewset.py` for DRF viewset logic
  - `apps/api/schema.py` for drf-spectacular schema decorators
  - `apps/api/service/database_interface.py` for the abstract service contract
  - `apps/api/service/database_service.py` for configured backend services and their factory
  - `apps/api/serializers.py` for API payload serialization
- `apps/core/` remains the core app for model and non-API project logic. Its registered configuration is `apps.core.apps.CoreConfig`.
- Use `apps.core` consistently in imports when touching the core app, and use `apps.api` when touching API code. Although settings add `apps/` to `sys.path`, importing the same application under multiple names can create duplicate module identities.
- The Django database is PostgreSQL. Keep local database files and credentials out of commits; commit migration files.
- `README.md` documents local setup and development commands; update it when those instructions change.

## Local skills

For Django REST Framework API work, read and follow [the REST Framework skill](.agents/skills/django-rest-framework/SKILL.md).

Django REST Framework and drf-spectacular are installed and configured. The connection service uses Psycopg 3 (`psycopg`); `psycopg2-binary` is also currently declared. Read `pyproject.toml` and `uv.lock` before changing dependencies, and synchronize them with `uv add` when adding packages.

Inspect `.agents/skills/` for other relevant skills as the repository evolves. Only reference skill files that actually exist.

## Implementation conventions

- Inspect the affected code and current settings before making changes. The project has a connection-test API, Swagger documentation, and an unmanaged `DatabaseMetadata` placeholder model. Commented metadata queries and unused serializers do not imply active endpoints.
- Keep application behavior in `apps/` and project-wide configuration in `bi/`. Follow existing patterns and keep changes scoped to the request.
- Generate migrations for model changes and review their operations. Preserve applied migration history; use new migrations for subsequent schema changes.
- Name Django model classes in PascalCase, such as `DataBase`; do not use all-uppercase model names. Set explicit lowercase SQL table names through `Meta.db_table` (use snake_case for multiple words). Keep Python class names and SQL table names distinct, and create migrations for renames instead of rewriting applied history.
- Set explicit, human-readable `Meta.verbose_name` and `Meta.verbose_name_plural` for Django models. Generate a new migration when changing model options.
- Use Django authentication, permissions, validation, and CSRF protection appropriate to the feature. Keep secrets out of committed code and documentation.
- Settings currently target local development and load environment values from `.env` using `python-dotenv` when needed.
- Django’s own PostgreSQL configuration should use `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT` environment variables.
- Keep changes focused and reviewable. Use Django's existing tooling for validation when needed, but do not force automatic test creation for every change.

## Database API flow

The API is stateless: it does not save connection records or passwords. `DataBase` was removed by `core.0007`; retain the historical migrations, including the former encrypted-password migration. `apps/core/models.py` currently has no models. The unmanaged `apps/api/models.py` placeholder is not required by the active `GenericViewSet`.

- `apps/api/urls.py` registers `DatabaseViewSet` with `DefaultRouter`, prefix `database`, and explicit basename `database`. `bi/urls.py` includes `/api/` and owns `/schema/`, `/swagger/`, and `/admin/`.
- `DatabaseViewSet` uses `GenericViewSet`, allows POST and OPTIONS, and has no model CRUD. Keep routing `@action` decorators on methods and apply `@database_viewset_schema` at class level. Keep `extend_schema_view`/`extend_schema` definitions in `apps/api/schema.py`.
- All actions validate `request.data` using a serializer and `is_valid(raise_exception=True)`, select a configured service through the factory, call a service method, and return HTTP 200 when `success` is true or 400 otherwise.

| POST route | Request serializer | Service method | Success result |
| --- | --- | --- | --- |
| `/api/database/databases/` | `DatabaseConnectionQuerySerializer` | `connection_test()` | `success`, `message` |
| `/api/database/tables/` | `DatabaseConnectionQuerySerializer` | `get_tables()` | `success`, `database`, `tables` as `schema.table` strings |
| `/api/database/columns/` | `DatabaseColumnsQuerySerializer` | `get_columns(table)` | `success`, `database`, `table`, `columns` |

- Connection fields are required: `db_type`, `host`, `port`, `database`, `username`, and `password`. Host, database, and username have maximum length 255; port is 1–65535. Password is write-only, preserves whitespace, and allows an empty string.
- `DatabaseType` in `apps/core/choices.py` is the shared `TextChoices`: `postgresql`, `mysql`, `clickhouse`, and `mssql`. Only `postgresql` has an implementation. Do not confuse accepted serializer choices with implemented backends or use the obsolete `postgres` value.
- `DatabaseColumnsQuerySerializer` adds `table`, requiring nonempty schema and table parts. Copy validated data and remove `table` before passing constructor arguments to the factory; pass it separately to `get_columns`.
- `DatabaseServiceFactory.get_service(db_type, **connection_kwargs)` returns a new configured backend instance, or `None` when no implementation exists. Views handle `None` with HTTP 400 and an `error` message. Its current return annotation omits `None`; preserve runtime behavior when documenting or updating typing.
- `DatabaseService` is an ABC declaring instance methods `connection_test`, `get_tables`, and `get_columns`. `POSTGRES` implements it with constructor-supplied settings in `self.config`, translating `database` to `dbname` and `username` to `user`. Keep SQL in the service, validation in serializers, and HTTP responses in the viewset.
- Services use Psycopg 3, a 5-second connection timeout, and context-managed connections/cursors. `connection_test` executes `SELECT 1`. `get_tables` queries `pg_catalog.pg_tables`, excludes `pg_catalog` and `information_schema`, and sorts schema/table names; it does not return views or nested columns.
- `get_columns` splits the qualified name at the first dot and uses SQL parameters for schema/table filters on `information_schema.columns`, ordered by ordinal position. Columns contain `name`, `type`, `nullable`, `default`, `max_length`, `precision`, and `scale`. No visible matches returns a successful empty list.
- Driver failures produce `success: false`, generic messages, and empty metadata lists. Invalid requests produce DRF field errors; unsupported implementations produce an `error` object. These are distinct response shapes.
- Known schema drift: `DatabaseTablesResponseSerializer` and the table action description still describe nested columns/views, while runtime returns table-name strings. The interface's table docstring is also stale. Schema validation alone does not prove response accuracy; verify documented shapes against service results when touching these areas.
- Never log or return passwords, connection configuration, or raw driver errors. Keep credentials in POST bodies. Target credentials come from requests, independently of Django's environment-configured database. Preserve appropriate authentication, permissions, and session CSRF protection; no explicit permission policy is currently configured on this viewset.

## Python conventions

- Use snake_case for functions, methods, and variables; PascalCase for new classes and models; uppercase for constants. The existing backend class is named `POSTGRES`; do not rename it incidentally or confuse it with a model.
- Keep canonical `apps.api`/`apps.core` imports, explicit serializer fields, and backend interfaces aligned with implementations. Avoid broad exception handling that hides programming errors.
- Reuse shared choices rather than copying database type strings. Adding a backend requires an implementation, factory registration, matching request validation, schema updates, and meaningful checks.

## Commands and validation

Install the locked dependencies:

```bash
uv sync --locked
```

Run checks appropriate to the changes:

```bash
uv run python manage.py check
```

For schema or API documentation changes:

```bash
uv run python manage.py spectacular --file /tmp/bi-openapi.yaml --validate --fail-on-warn
```

For connection-flow changes, use mocked driver checks for credential forwarding, successful and failed connections, serializer validation, and resource cleanup. Report live database checks separately; mocked checks do not establish live connectivity.

For model changes:

```bash
uv run python manage.py makemigrations core
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py migrate --plan
```

Use the affected application's label when generating migrations for other apps. Apply migrations to the local development database when needed for the requested work.

If `uv` is unavailable or blocked by cache or network access, use `.venv/bin/python manage.py ...` for checks when the existing environment has the required dependencies. Report any validation that could not run and why. Documentation-only edits do not require running the Django test suite.

When finishing, summarize the changes, validation results, and any migration or setup steps the user needs to perform. Claim checks passed only when they were executed successfully.
