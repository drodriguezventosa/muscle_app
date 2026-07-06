---
name: docker-infra
description: How to use Docker Compose, add services and work with dev/prod profiles for MuscleApp. Use when changing docker-compose files, Dockerfiles or deployment config.
---

# Docker & infra

## Compose layout

- `docker-compose.yml` — base services: `db` (pgvector), `backend`, `frontend`, on the `muscle_net` network.
- `docker-compose.override.yml` — dev tweaks (hot-reload, exposed ports, source volumes), merged automatically.
- Services talk to each other by **service name** (e.g. backend reaches Postgres at `db:5432`).

## Common commands

```bash
docker compose up --build              # start the full dev stack
docker compose --profile llm up        # also start Ollama (local LLM)
docker compose down -v                 # stop and drop volumes
docker compose logs -f backend         # tail a service
```

## Dockerfiles

- Multi-stage: builder → slim runtime. Backend runs as a **non-root** user.
- Frontend Dockerfile has stages: `base` → `dev` (Vite server) → `builder` → `runtime` (nginx static).
- The override uses `target: dev` for the frontend so hot-reload works.

## Adding a service

1. Add it under `services:` in `docker-compose.yml` on `muscle_net`.
2. Add a healthcheck and `depends_on` conditions where needed.
3. Put dev-only overrides (ports, volumes) in `docker-compose.override.yml`.

## Deploy (prepared, not executed)

`infra/deploy/` holds notes/config for Cloud Run (backend), Neon (Postgres+pgvector) and Vercel (frontend). Keep images small and scale-to-zero friendly. All code and comments in English.
