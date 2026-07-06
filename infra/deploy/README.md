# Deployment (prepared, not yet executed)

Target free-tier stack for the thesis demo. Nothing here is deployed until the app is
ready; this documents the intended path and keeps config close at hand.

## Topology

| Component | Service | Notes |
|-----------|---------|-------|
| Frontend (static SPA) | **Vercel** | build `frontend`, output `dist/`; free tier |
| Backend (FastAPI) | **Google Cloud Run** | container from `backend/Dockerfile`, scales to zero |
| Database (Postgres + pgvector) | **Neon** | free tier supports `pgvector` |
| LLM | **Gemini free tier** | set `LLM_PROVIDER=gemini` + `GEMINI_API_KEY` |

## Configuration

- Backend reads all config from environment variables (see `.env.example`). On Cloud Run,
  set them as service env vars / secrets — never bake secrets into the image.
- Set `APP_ENV=production`, `LOG_JSON=true`, and a strict `CORS_ORIGINS` (the Vercel URL).
- Run Alembic migrations against Neon before the first release (`alembic upgrade head`).

## Checklist before going live

- [ ] Secrets stored in the platform secret manager (not in git).
- [ ] `CORS_ORIGINS` restricted to the real frontend origin.
- [ ] HTTPS enforced (Cloud Run + Vercel do this by default).
- [ ] Trivy image scan clean for HIGH/CRITICAL.
- [ ] Health/readiness probes wired to `/health` and `/ready`.
