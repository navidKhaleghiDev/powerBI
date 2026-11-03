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

## API Development

- Use existing Django REST Framework patterns.
- Implement serializers with explicit writable fields.
- Validate request data using serializers.
- Use ViewSets or generic views according to project conventions.
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

## Testing

- Follow the existing project's test framework.
- Test successful API requests.
- Test invalid request data.
- Test unauthenticated requests.
- Test unauthorized access.
- Test object-level permissions.
- Test pagination and filtering.
- Add regression tests for identified bugs.

## Validation

Use the project's existing environment and tooling.

Run relevant checks:

- uv run python manage.py check
- uv run python manage.py test

Do not claim tests passed unless they were actually executed.

## Completion

Report:

1. Bugs or security issues discovered.
2. Files changed.
3. Tests added.
4. Validation results.
5. Remaining risks.
