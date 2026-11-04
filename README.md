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
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/ to view the development server, or http://127.0.0.1:8000/admin/ to sign in with your superuser account.

The API routes are available under `/api/` and the main database metadata endpoints are registered through the API router.

Open http://127.0.0.1:8000/api/swagger/ for interactive Swagger documentation.
The OpenAPI schema is available at `/api/schema/`. Database documentation covers
listing databases and inspecting columns with the `database` query parameter.

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
