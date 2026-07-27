# 19. Embeddings on Jina AI (Google's free tier blocks datacenter IPs)

- Status: accepted
- Date: 2026-07-27

## Context

After [ADR-0018](0018-embedding-model-migration.md) added logging to the embedding
adapter, the deployed service reported the real failure:

```
status=400  FAILED_PRECONDITION
"User location is not supported for the API use."
```

Measured with the same API key, minutes apart:

| Caller | Result |
|---|---|
| Developer laptop (residential IP, Spain) | `gemini-embedding-2` → 200, 384 dims; `gemini-embedding-001` → 200 |
| Render web service (`frankfurt`, datacenter IP) | 400 `FAILED_PRECONDITION` |

So the key, the project and both models are fine: Google's **free** tier refuses
requests from cloud egress IPs. Two consequences follow:

- Moving the service to a US region would very likely **not** help (the gate is on
  the datacenter IP, not the country), and would cost a service recreation plus a
  new URL to propagate to Vercel and UptimeRobot.
- Enabling billing on the Google project would work, but breaks the project's
  €0 / no-credit-card constraint (ADR-0010).

The exercise/meal chats stayed up meanwhile thanks to ADR-0018's structured
fallback, but with no semantic ranking — the RAG core of the thesis.

## Decision

Move embeddings to **Jina AI** (`jina-embeddings-v3` by default, configurable via
`JINA_MODEL`), a free tier that requires no credit card and accepts cloud IPs.

- `JinaEmbedding` posts to `https://api.jina.ai/v1/embeddings` with a Bearer key,
  requesting `dimensions: EMBEDDING_DIM` (Matryoshka truncation) and
  `task: text-matching` — the same task for catalog rows and queries, so cosine
  distance stays meaningful between them. Vectors are L2-normalized as before.
- **384 dimensions are preserved**, so the `vector(384)` column, the pgvector
  queries and the Alembic history are untouched: switching provider is a config
  change plus one adapter, exactly what the ports/adapters boundary promised
  (ADR-0002/0004).
- Gemini stays available as a provider for local development.
- Because vectors of different models are not comparable, deploying this needs one
  boot with `EMBEDDING_REBUILD=true` (ADR-0018) to recompute the catalog.

Also fixed while diagnosing: `REDIS_URL` was configured as `redis://` against
Upstash, which requires TLS. The connection had been failing since it was set up,
and `RedisCache` swallowed every error, so the cache looked enabled while doing
nothing. The adapter now **logs the first failure** (with a `rediss://` hint) and
the URL scheme is documented in `.env.example` and `render.yaml`.

## Consequences

- Semantic search works from the deployed host again, still at €0 and with no
  credit card, and without recreating the service or changing its URL.
- One more provider to keep an eye on: its free tier is token-based, so heavy use
  could exhaust it. The graceful degradation from ADR-0018 covers that case, and
  query embeddings are cached (ADR-0015) — now that Redis actually works.
- Lesson recorded: **swallowing errors without logging** hid two separate faults
  (a broken cache for weeks, and a provider outage behind an opaque 500). Adapters
  degrade quietly, but never silently.
