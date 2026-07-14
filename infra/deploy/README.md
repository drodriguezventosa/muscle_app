# Deployment — free stack with CD on push to `main`

Zero-cost, no-credit-card stack (see ADR-0010). Continuous deployment is **native**:
both platforms auto-deploy on every push to `main` (ADR-0014) — no GitHub Actions
workflow or CI tokens needed.

| Component | Service | How it deploys |
|-----------|---------|----------------|
| Frontend (SPA) | **Vercel** (Hobby) | Vercel's native GitHub integration, on every push |
| Backend (API) | **Render** (free web service) | `render.yaml` Blueprint; Render rebuilds on every push (`autoDeploy`) |
| Database | **Neon** (Postgres + pgvector) | schema + catalog bootstrapped by the backend on boot |
| Chat LLM | **Groq** free API | `LLM_PROVIDER=groq` + `GROQ_API_KEY` (Gemini's free chat quota is too low) |
| Embeddings | **Gemini** free API | `EMBEDDING_PROVIDER=gemini` + `GEMINI_API_KEY` (no torch → fits Render's 512 MB) |

> Why not Hugging Face? HF now gates **Docker** Spaces behind the paid Pro plan,
> which breaks the no-card rule — so the backend lives on Render instead.

## One-time setup (you do this — accounts & secrets can't be automated)

### 1. Neon (database)
1. Create a free project at [neon.tech](https://neon.tech) (no card). Note host,
   database, user, password, port.
2. pgvector + the schema are created automatically by the backend on first boot.

### 2. API keys (both free, no card)
- **Gemini** (embeddings): create a key at [Google AI Studio](https://aistudio.google.com/apikey).
- **Groq** (chat LLM): create a key at [console.groq.com/keys](https://console.groq.com/keys).

### 3. Render (backend)
1. Sign up at [render.com](https://render.com) with GitHub (no card).
2. **New → Blueprint**, pick this repo. Render reads `render.yaml` and creates the
   `muscleapp-api` web service.
3. Fill the env vars marked "set in dashboard" (they are `sync: false` in the
   Blueprint, so nothing secret is committed):
   `POSTGRES_HOST/PORT/USER/PASSWORD/DB` (from Neon), `GEMINI_API_KEY`,
   `GROQ_API_KEY`, and `CORS_ORIGINS` (your Vercel URL — fill after step 4).
   The rest (`APP_ENV`, `DB_SSL=true`, `EMBEDDING_PROVIDER=gemini`,
   `LLM_PROVIDER=groq`) come from `render.yaml`.
4. Deploy → note the service URL, e.g. `https://muscleapp-api.onrender.com`.

### 4. Vercel (frontend)
1. Import the GitHub repo; set **Root Directory = `frontend`** (Vite auto-detected).
2. Add env var `VITE_API_BASE_URL = https://<your-render-service>.onrender.com/api/v1`.
3. Deploy → note the URL, and set it as `CORS_ORIGINS` on Render (step 3).

## After setup
Every push to `main`: Vercel redeploys the frontend and Render redeploys the backend
(which re-bootstraps the DB idempotently). No manual steps, no CI secrets.

## Checklist
- [ ] Neon project created; pgvector allowed (auto `CREATE EXTENSION`).
- [ ] Render Blueprint deployed; `DB_SSL=true`; `GEMINI_API_KEY` + `GROQ_API_KEY` set; `CORS_ORIGINS` = the Vercel origin.
- [ ] `VITE_API_BASE_URL` set in Vercel = the Render `/api/v1` URL.
- [ ] First deploy green; `/health` returns OK; explorer + chatbot work.
- [ ] Note: Render free sleeps on inactivity; the first request after idle is slow.
