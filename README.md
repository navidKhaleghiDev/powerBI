# BI

A Django project with a `core` application, Django admin, and a local SQLite database. The project is currently an initial scaffold with no custom models or application routes.

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/) for dependency management

Dependencies are declared in `pyproject.toml` and locked in `uv.lock`. The project uses Django 5.2.

## Local setup

Run these commands from the project root:

```bash
uv sync --locked
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/ to view the development server, or http://127.0.0.1:8000/admin/ to sign in with your superuser account. The admin is currently the only configured application route.

SQLite data is stored in `db.sqlite3`, which is excluded from version control. No environment file is required for the current local settings.

## Project structure

```text
bi/
├── apps/
│   └── core/          # Application models, views, admin, and migrations
├── bi/
│   ├── settings.py    # Django configuration
│   ├── urls.py        # Root URL configuration
│   ├── asgi.py        # ASGI entry point
│   └── wsgi.py        # WSGI entry point
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
