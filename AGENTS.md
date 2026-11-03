# Repository guidance

## Project layout

- This is the `bi` Django project, managed with `uv`. Read `pyproject.toml` and `uv.lock` for current dependency versions; the project currently requires Python 3.13+ and Django 5.2.
- Run commands from the repository root, alongside `manage.py`.
- `bi/settings.py` contains settings, `bi/urls.py` contains root routes, and `bi/asgi.py` and `bi/wsgi.py` expose application entry points.
- `apps/core/` contains the core application: models, views, admin registration, and migrations. Its registered configuration is `apps.core.apps.CoreConfig`.
- Use `apps.core` consistently in imports. Although settings add `apps/` to `sys.path`, importing the same application as both `core` and `apps.core` can create duplicate module identities.
- SQLite data lives in the ignored `db.sqlite3` file. Commit migration files, not local databases.
- `README.md` documents local setup and development commands; update it when those instructions change.

## Local skills

For Django REST Framework API work, read and follow [the REST Framework skill](.agents/skills/django-rest-framework/SKILL.md).

REST Framework is not currently installed or configured. The presence of a skill does not mean its dependencies or application features exist. Add and configure it when the requested API work requires it, keeping `pyproject.toml` and `uv.lock` synchronized with `uv add`.

Inspect `.agents/skills/` for other relevant skills as the repository evolves. Only reference skill files that actually exist.

## Implementation conventions

- Inspect the affected code and current settings before making changes. The project starts as a scaffold with no custom models and only the `/admin/` route; verify the current state rather than assuming features exist.
- Keep application behavior in `apps/` and project-wide configuration in `bi/`. Follow existing patterns and keep changes scoped to the request.
- Generate migrations for model changes and review their operations. Preserve applied migration history; use new migrations for subsequent schema changes.
- Use Django authentication, permissions, validation, and CSRF protection appropriate to the feature. Keep secrets out of committed code and documentation.
- Settings currently target local development and do not load `.env` files. Implement environment loading explicitly if a requested configuration depends on it.
- Add focused tests for changed behavior, including relevant validation and access-control failures. Use Django's existing test runner unless the project adopts another framework.

## Commands and validation

Install the locked dependencies:

```bash
uv sync --locked
```

Run checks appropriate to the changes:

```bash
uv run python manage.py check
uv run python manage.py test
```

For model changes:

```bash
uv run python manage.py makemigrations core
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py migrate --plan
```

Use the affected application's label when generating migrations for other apps. Apply migrations to the local development database when needed for the requested work.

If `uv` is unavailable or blocked by cache or network access, use `.venv/bin/python manage.py ...` for checks when the existing environment has the required dependencies. Report any validation that could not run and why. Documentation-only edits do not require running the Django test suite.

When finishing, summarize the changes, validation results, and any migration or setup steps the user needs to perform. Claim checks passed only when they were executed successfully.
