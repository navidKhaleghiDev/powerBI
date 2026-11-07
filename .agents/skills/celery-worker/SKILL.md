---
name: celery-worker
description: Configure and maintain Celery background tasks in this project's apps/worker app, including Django integration and worker troubleshooting.
---

# Celery worker

## Repository context

Read `AGENTS.md`, `pyproject.toml`, `uv.lock`, `bi/settings.py`, `bi/__init__.py`, and affected worker code before changing behavior.

`apps/worker/` is dedicated to Celery tasks and registered as `apps.worker.apps.WorkerConfig`. When this skill was added, it was a scaffold: Celery was not declared as a dependency, and no Celery application, broker configuration, or tasks existed. Verify current files before assuming setup is complete.

## Implementation boundaries

- Put task entry points in `apps/worker/tasks.py`, using canonical `apps.worker` imports. Keep HTTP validation and responses in `apps/api/`; reuse services without importing viewsets.
- When integration is requested, keep project-wide Celery setup in `bi/celery.py`, initialization in `bi/__init__.py`, and settings in `bi/settings.py`. Do not start workers from Django app initialization.
- Add dependencies with `uv add` and synchronize the lockfile. Configure broker and optional result-backend URLs through environment variables. Do not assume a broker has been selected or commit its credentials.
- Keep arguments serializable. Avoid passing connections, requests, or passwords through the broker. Moving the stateless database API into tasks requires an explicit credential-handling design.
- Dispatch tasks consuming newly written records after the transaction commits. Make retried side effects safe to repeat and bound retries to appropriate transient failures.
- Django uses `Asia/Tehran`; account for it in Celery scheduling. Add schedulers and result storage only when needed by the requested feature.

## Validation

Run Django's system check for integration changes and focused checks for task outcomes, retries, and transaction behavior as relevant. Eager execution and mocks do not establish live broker connectivity or worker execution; report those separately.

Update `README.md` when setup changes, using actual environment variable names and verified worker commands. Do not claim the worker is runnable before dependencies, application initialization, task discovery, and broker configuration are ready. Documentation-only changes need no Django tests.

## Test policy

Do not create, add, or modify automated tests unless the user explicitly requests them. Do not run test suites unless explicitly requested. Existing tests must remain untouched unless their modification or removal is requested. Use syntax checks, Django system checks, schema validation, or configuration validation as appropriate instead.
