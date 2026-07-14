# Deployment — free stack with CD on merge to `main`

Zero-cost, no-credit-card stack (see ADR-0010). Continuous deployment: **merge to
`main` → everything redeploys** (ADR-0014).

| Component | Service | How it deploys |
|-----------|---------|----------------|
| Frontend (SPA) | **Vercel** (Hobby) | Vercel's native GitHub integration, on every push |
| Backend (API) | **Hugging Face Space** (Docker) | `.github/workflows/deploy.yml` pushes `backend/` + `infra/hf-space/` to the Space, which rebuilds |
| Database | **Neon** (Postgres + pgvector) | schema + catalog bootstrapped by the Space on first boot |
| LLM | **Gemini** free API | `LLM_PROVIDER=gemini` + `GEMINI_API_KEY` on the Space |

## One-time setup (you do this — accounts & secrets can't be automated)

### 1. Neon (database)
1. Create a free project at neon.tech (no card). Note host, database, user, password.
2. pgvector + the schema are created automatically by the Space on first boot.

### 2. Gemini key
Create a free API key at Google AI Studio (aistudio.google.com — no card).

### 3. Hugging Face Space (backend)
1. Create a **Docker** Space (huggingface.co/new-space). Its id is `your-user/muscleapp-api`.
2. In the Space → Settings → *Variables and secrets*, add (see `infra/hf-space/README.md`):
   `APP_ENV=production`, `POSTGRES_HOST/USER/PASSWORD/DB` (from Neon), `DB_SSL=true`,
   `EMBEDDING_PROVIDER=sentence_transformers`, `LLM_PROVIDER=gemini`, `GEMINI_API_KEY`,
   and `CORS_ORIGINS` (your Vercel URL — fill in after step 4).

### 4. Vercel (frontend)
1. Import the GitHub repo; set **Root Directory = `frontend`** (Vite auto-detected).
2. Add env var `VITE_API_BASE_URL = https://<your-space>.hf.space/api/v1`.
3. Deploy → note the URL, and set it as `CORS_ORIGINS` on the Space (step 3).

### 5. GitHub (enables backend CD)
Add in the repo (Settings → Secrets and variables → Actions), or via `gh`:
```bash
gh secret set HF_TOKEN            # a Hugging Face write token (huggingface.co/settings/tokens)
gh variable set HF_SPACE --body "your-user/muscleapp-api"
```
> Set the secret **value** yourself (it must not pass through anyone else). Until
> `HF_SPACE` exists, the deploy job is skipped — no failing runs.

## After setup
Every merge to `main`: Vercel redeploys the frontend, and the workflow pushes the
backend to the Space (which rebuilds and re-bootstraps the DB, idempotently).

## Checklist
- [ ] Neon project created; pgvector allowed (auto `CREATE EXTENSION`).
- [ ] Space secrets set; `DB_SSL=true`; `CORS_ORIGINS` = the Vercel origin.
- [ ] `HF_TOKEN` secret + `HF_SPACE` variable in GitHub.
- [ ] `VITE_API_BASE_URL` set in Vercel = the Space `/api/v1` URL.
- [ ] First deploy green; `/health` returns OK; explorer + chatbot work.
