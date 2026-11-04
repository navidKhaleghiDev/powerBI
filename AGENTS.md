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
- Name Django model classes in PascalCase, such as `DataBase`; do not use all-uppercase model names. Set explicit lowercase SQL table names through `Meta.db_table` (use snake_case for multiple words). `DataBase` maps to the SQL table `database`. Keep Python class names and SQL table names distinct, and create migrations for renames instead of rewriting applied history.
- Set explicit, human-readable `Meta.verbose_name` and `Meta.verbose_name_plural` for Django models. For `DataBase`, use `"Database"` and `"Databases"`. Generate a new migration when changing model options.
- Use Django authentication, permissions, validation, and CSRF protection appropriate to the feature. Keep secrets out of committed code and documentation.
- Settings currently target local development and load environment values from `.env` using `python-dotenv` when needed.
- Django’s own PostgreSQL configuration should use `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT` environment variables.
- Keep changes focused and reviewable. Use Django's existing tooling for validation when needed, but do not force automatic test creation for every change.

## Database API flow

- `apps/api/urls.py` registers `DatabaseViewSet` with `DefaultRouter` under `database`; `bi/urls.py` includes it under `/api/` and owns `/schema/` and `/swagger/`.
- The active action is `POST /api/database/databases/` (`connection_test`) on `GenericViewSet`. Keep `@action` routing decorators in the viewset; keep Swagger annotations in `apps/api/schema.py`, applied with `@database_viewset_schema`.
- Validate `request.data` with `DatabaseConnectionQuerySerializer` and `is_valid(raise_exception=True)`. Current body fields are `db_type`, `host`, `port`, `database`, `username`, and `password`. The backend choice is currently `postgres`; port is 1–65535. Password is write-only, preserves whitespace, and permits an empty string.
- Pass validated values to `DatabaseServiceFactory.get_service(**query.validated_data)`. The factory selects the backend and constructs it with connection settings. Keep backend selection out of the view and SQL out of serializers.
- `POSTGRES` implements `DatabaseService`, stores constructor-supplied credentials in `self.config`, and maps `database`/`username` to Psycopg’s `dbname`/`user`. These target credentials come from the request, independently of Django’s environment-configured database.
- `connection_test(self)` uses `psycopg.connect`, a 5-second connection timeout, context-managed connection/cursor cleanup, and `SELECT 1`. It returns `success` and `message`; the view maps success to HTTP 200 and failure to HTTP 400. Validation errors use DRF’s field-error response.
- Keep interface, factory, constructor, serializers, view, and schema aligned when changing this flow. For a new backend, add its implementation and factory mapping and update serializer choices. Define unsupported-backend handling explicitly; the current serializer rejects unsupported API choices before factory invocation.
- Do not expose passwords, connection configuration, or raw driver errors in responses or logs. Keep request credentials in POST bodies and preserve session authentication’s CSRF protection.

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
