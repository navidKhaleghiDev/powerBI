---
name: django-rest-framework
description: Develop, review, debug, secure, and optimize Django REST Framework APIs, serializers, viewsets, authentication, permissions, pagination, and filtering.
---

# Django REST Framework Skill

## Project Discovery

Before modifying code:

1. Read AGENTS.md if available.
2. Inspect pyproject.toml to determine installed versions.
3. Inspect Django settings in the bi/ directory.
4. Find existing APIs, serializers, views, and URL routes in apps/.
5. Follow existing project conventions.
6. For this repository, keep DRF API work under `apps/api/` with the package layout:
   - `apps/api/urls.py`
   - `apps/api/viewset/database_viewset.py`
   - `apps/api/service/database_service.py`
   - `apps/api/serializers.py`

## API Development

- Use existing Django REST Framework patterns.
- Implement serializers with explicit writable fields.
- Validate request data using serializers.
- Use `ModelViewSet` or `ReadOnlyModelViewSet` when the endpoint is read-only and follows the project’s metadata API pattern.
- Keep database logic in `apps/api/service/` and keep API response logic in `apps/api/viewset/`.
- Apply pagination for large collections.
- Use appropriate HTTP status codes.
- Preserve backwards compatibility when possible.

## Security

- Enforce authentication and permissions.
- Filter querysets by user or tenant when required.
- Prevent unauthorized object access.
- Validate foreign-key ownership.
- Never expose sensitive model fields.
- Preserve CSRF protection for session authentication.

## Database Optimization

- Use select_related() for ForeignKey relationships.
- Use prefetch_related() for reverse and many-to-many relationships.
- Avoid N+1 queries.
- Avoid unnecessary database queries in serializers.


## Validation

Use the project's existing environment and tooling when validation is needed.

Run relevant checks as appropriate, such as:

- uv run python manage.py check

Do not claim validation passed unless it was actually executed.

## Completion

Report:

1. Bugs or security issues discovered.
2. Files changed.
3. Validation results.
4. Remaining risks.
