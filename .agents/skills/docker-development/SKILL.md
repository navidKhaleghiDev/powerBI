---
name: docker-development
description: Maintain this project's Django Dockerfiles and Compose stack, including development reload, separate application and CDC databases, container networking and volumes.
---

# Django Docker development

Read `AGENTS.md`, both Dockerfiles, `.dockerignore`, `docker-compose.yaml`,
`.env.example`, dependency manifests and relevant settings before editing.

## Service boundaries

- Compose `web` builds `Dockerfile.dev` and mounts source at `/app`. Dependencies
  live at `/opt/venv` so the mount does not hide them. Compose already selects
  development mode directly; do not assume a separate override file exists.
- `Dockerfile` is a multi-stage Gunicorn runtime excluding development packages.
  Both images run as UID 10001; check volume ownership for uploads/static files.
- `db` is application PostgreSQL with `django_pg_data`. Compose maps
  `DJANGO_POSTGRES_DB`, `DJANGO_POSTGRES_USER` and `DJANGO_POSTGRES_PASSWORD`
  to matching `POSTGRES_*` variables in both `db` and `web`. Django uses `db:5432`.
- `postgres` is the CDC source: database `crm-db`, volume `pg_data`, host port
  5433, logical replication settings and `postgres/init.sql`. Keep its storage
  independent; Django migrations belong on `db`.
- PostgreSQL initialization only runs for empty storage. Environment changes
  do not rename existing databases or rotate passwords. Preserve named volumes
  during ordinary updates; do not use `down -v` as routine cleanup.

## Networking and builds

Containers use `connect:8083`, `debezium-ui:8080`, `clickhouse:8123` and
`postgres:5432` for CDC. Kafka's internal listener is `kafka:29092`; ClickHouse
resolves its configured Kafka brokers. Container localhost is the container
itself. The application `db` has no published host port.

Add dependencies with `uv add` and preserve `uv.lock`. Rebuild after dependency
changes; recreate containers after environment changes. Keep secrets, dumps and
archives out of image contexts through `.dockerignore`.

## Validation and documentation

Run `docker compose config --quiet` after configuration changes. Build affected
images for Dockerfile/dependency changes and run Django checks inside them.
`docker compose run --rm web python manage.py check` can start dependencies;
report this separately from static validation. Apply migrations explicitly when
needed, never during image builds. Readiness does not prove migrations or CDC
consumption succeeded. Follow AGENTS.md's no-tests policy unless requested.

Keep README commands and environment names current. Current settings remain for
development; Gunicorn alone does not provide production settings or static serving.
