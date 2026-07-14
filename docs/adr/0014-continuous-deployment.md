# 14. Continuous deployment on merge to main

- Status: accepted
- Date: 2026-07-14

## Context

We want the free-tier demo (ADR-0010) to redeploy automatically, without manual
steps per release, and in a way that reads well for the thesis (CI/CD maturity).

## Decision

Deploy on every merge to `main`:
- **Frontend**: Vercel's native GitHub integration (auto-deploy on push, plus PR
  previews) — no workflow needed.
- **Backend**: a `deploy.yml` GitHub Actions job assembles `backend/` +
  `infra/hf-space/` and force-pushes it to the Hugging Face Space git repo, which
  rebuilds the Docker image. Guarded by an `HF_SPACE` repo variable so it is a no-op
  until configured.
- **Database**: the Space container bootstraps idempotently on boot (create extension
  + `create_all` + seed + embedding backfill) rather than a separate migration job,
  so managed-Postgres TLS is handled in one place (the async engine, `DB_SSL`).

Secrets live in each platform's own store (Space vars, Vercel env) and in GitHub
(`HF_TOKEN`); nothing secret is committed.

## Consequences

- One merge → frontend, backend and DB are all updated; the pipeline is visible in
  the repo.
- The container bootstrap is idempotent, so redeploys and restarts are safe.
- Initial schema is created from the models (not Alembic) at deploy time to avoid
  configuring the sync Alembic connection for TLS; Alembic remains the source for
  schema evolution and local/CI databases.
