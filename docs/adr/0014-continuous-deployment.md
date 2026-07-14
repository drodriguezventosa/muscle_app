# 14. Continuous deployment on merge to main

- Status: accepted
- Date: 2026-07-14

## Context

We want the free-tier demo (ADR-0010) to redeploy automatically, without manual
steps per release, and in a way that reads well for the thesis (CI/CD maturity).

Superseded backend host: Hugging Face Spaces was the original backend target, but
HF now gates the **Docker** SDK behind a paid Pro plan, which breaks the
no-card / 0 € constraint (ADR-0010). We moved the backend to **Render** (free web
service, no card). This also simplifies CD: Render, like Vercel, auto-deploys
natively from GitHub, so the custom GitHub Actions deploy workflow is removed.

## Decision

Deploy on every push to `main`, both via **native GitHub auto-deploy** (no custom
workflow):
- **Frontend**: Vercel's native GitHub integration (auto-deploy on push, plus PR
  previews).
- **Backend**: Render, configured by the committed `render.yaml` Blueprint. Render
  watches `main` and rebuilds on every push (`autoDeploy: true`).
- **Database**: the Render start command runs `python -m app.bootstrap` before
  uvicorn — idempotent (create extension + `create_all` + seed + embedding
  backfill) rather than a separate migration job, so managed-Postgres TLS is
  handled in one place (the async engine, `DB_SSL`).

Secrets live in each platform's own store (Render env vars marked `sync: false`,
Vercel env); nothing secret is committed and no CI tokens are needed.

## Consequences

- One push → frontend, backend and DB are all updated; deploy config (`render.yaml`,
  `vercel.json`) is visible in the repo.
- The boot bootstrap is idempotent, so redeploys and restarts are safe.
- Render's free instance sleeps on inactivity (first request ~cold start); accepted
  for a demo (ADR-0010).
- Embeddings use the Gemini API (`EMBEDDING_PROVIDER=gemini`) instead of local
  sentence-transformers, since torch does not fit the 512 MB free instance.
- Initial schema is created from the models (not Alembic) at deploy time to avoid
  configuring the sync Alembic connection for TLS; Alembic remains the source for
  schema evolution and local/CI databases.
