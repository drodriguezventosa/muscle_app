---
title: MuscleApp API
emoji: 💪
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8000
pinned: false
---

# MuscleApp API (Hugging Face Space)

Backend of [MuscleApp](https://github.com/) — FastAPI, hexagonal architecture.
This Space is **deployed automatically** by the project's GitHub Actions workflow
on every merge to `main`; do not edit it by hand.

Configure these as **Space secrets/variables** (Settings → Variables and secrets):

| Name | Value |
|------|-------|
| `APP_ENV` | `production` |
| `POSTGRES_HOST` / `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | from your Neon database |
| `DB_SSL` | `true` |
| `EMBEDDING_PROVIDER` | `sentence_transformers` |
| `LLM_PROVIDER` | `gemini` |
| `GEMINI_API_KEY` | your free Google AI Studio key |
| `CORS_ORIGINS` | your Vercel URL, e.g. `https://muscleapp.vercel.app` |

The container bootstraps the schema + catalog on first boot, then serves the API.
