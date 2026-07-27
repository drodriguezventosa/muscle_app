# 18. Surviving embedding-model retirement (gemini-embedding-2 + graceful degradation)

- Status: accepted (context corrected — see the update below)
- Date: 2026-07-27

> **Update (2026-07-27, same day): the root cause below was wrong.** The logging
> added by this ADR revealed the real error from the deployed service:
> `400 FAILED_PRECONDITION — "User location is not supported for the API use"`.
> Both `gemini-embedding-001` and `gemini-embedding-2` answer fine from a
> residential IP with the same key, so the model was never the problem: Google's
> **free tier rejects datacenter egress IPs**. See
> [ADR-0019](0019-embeddings-provider-jina.md) for the actual fix. Everything this
> ADR decided still stands (the graceful degradation is what kept the app up, and
> `001` does have an announced shutdown), but it did not restore semantic search.

## Context

The deployed assistant started returning **HTTP 500** on both chats (exercises and
meals) around mid-July 2026, with no backend change since #36 — so the trigger was
external. Google's deprecation schedule lists **`gemini-embedding-001` shutdown on
2026-07-14** (replacement: `gemini-embedding-2`), which matches the timing.

Two defects turned that upstream retirement into a full outage:

1. **No graceful degradation in the embedding adapter.** `GeminiLLM`/`GroqLLM`
   already caught HTTP errors and returned a fallback text, but
   `GeminiEmbedding._embed_one` called `raise_for_status()` unguarded, so any
   provider error (retired model, 429 quota, bad key) propagated out of the use
   case and surfaced as a 500. Embeddings are the *first* step of both RAG flows,
   so the whole assistant died — while DB-only endpoints kept working.
2. **A pinned model with no migration path.** Embedding models are retired
   roughly yearly, and vectors from different models are not comparable, so a
   model swap also requires re-embedding the stored catalog.

## Decision

- **Migrate to `gemini-embedding-2`.** It keeps the same `:embedContent` REST
  method and supports flexible output dimensionality (128–3072), so the existing
  `vector(384)` column and pgvector queries are unchanged — no schema migration.
- **Never let an embedding outage fail a request.** The adapter now logs the real
  status/body and raises the domain-level `EmbeddingUnavailableError`; both RAG
  use cases catch it and fall back to a **structured, non-vector retrieval**
  (`ExerciseRepository.list_catalog`, `FoodRepository.list_all`). The LLM still
  narrates real catalog items, so the assistant degrades from "semantic" to
  "structured" instead of breaking.
- **One-shot rebuild switch.** `EMBEDDING_REBUILD=true` clears the stored vectors
  at boot so the backfill recomputes them with the current model — the only way
  to re-embed on a shell-less free host. It is off by default (a rebuild costs one
  API call per catalog row).
- **Incremental backfill.** Vectors are committed in batches of 20, so a
  rate-limited run keeps its progress and the next boot only retries the rows
  still missing a vector.

## Consequences

- The assistant stays available through provider outages, quota exhaustion and
  future model retirements; only ranking quality degrades. Failures are now
  visible in logs (`embedding_request_failed` with the upstream status) instead of
  being an opaque 500.
- Migrating embedding models is a documented two-step operation (deploy with
  `EMBEDDING_REBUILD=true`, then turn it off) rather than a code archaeology task.
- The fallback is deliberately simple (catalog order + the existing structured
  filters) because both catalogs are small; it is not a replacement for semantic
  search, just a safety net.
- Reinforces the port/adapter boundary (ADR-0002/0004): the swap touched one
  adapter, one config default and the two use cases — no domain or API changes.
