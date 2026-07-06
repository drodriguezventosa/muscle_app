---
name: backend-dev
description: Conventions for the FastAPI hexagonal backend — how to add entities, ports, use cases, adapters and routers without breaking the layer boundaries. Use when editing anything under backend/app.
---

# Backend development (hexagonal / ports & adapters)

## Layer boundaries (do not violate)

- `app/domain/` — pure entities, value objects and **ports** (abstract interfaces). No FastAPI, no SQLAlchemy, no I/O.
- `app/application/` — use cases orchestrating domain + ports. Depends **only** on `domain`.
- `app/infrastructure/` — concrete adapters implementing ports (SQLAlchemy repos, LLM, embeddings, payments).
- `app/api/` — thin FastAPI routers + Pydantic schemas; wire adapters via dependency injection.

Dependency rule: dependencies point **inwards**. `domain` imports nothing from the outer layers.

## Recipe: add a feature (e.g. list exercises)

1. **Entity** in `app/domain/entities/` (a frozen dataclass or Pydantic model with no framework deps).
2. **Port** in `app/domain/ports/` — an `abc.ABC` describing what the use case needs (e.g. `ExerciseRepository`).
3. **Use case** in `app/application/use_cases/` — a class/function that receives the port(s) and returns domain objects/DTOs.
4. **Adapter** in `app/infrastructure/` — implement the port (SQLAlchemy repo, LLM client, ...).
5. **Schema** in `app/api/v1/schemas/` — Pydantic request/response models (never expose ORM models directly).
6. **Router** in `app/api/v1/routers/` — call the use case, map to schema. Register it in `app/api/v1/router.py`.
7. **Tests**: unit-test the use case with a fake port; integration-test the router.

## Rules

- All code and comments in **English**.
- Validate every input with Pydantic. Never build SQL by string concatenation.
- No business logic in `api/`; no DB/HTTP calls in `domain/`.
- Config comes from `app/core/config.py` (`get_settings()`), never `os.environ` scattered around.
- Keep the medical disclaimer present in any recommendation response.

## Commands

```bash
ruff check . && ruff format --check . && mypy app && bandit -r app
pytest
```
