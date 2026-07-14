# 15. Performance & resilience on free tiers: keep-alive + caching

- Status: accepted
- Date: 2026-07-15

## Context

The €0 stack (ADR-0010) has two free-tier costs that hurt perceived performance:

1. **Cold starts.** Render's free web service spins down after ~15 min of
   inactivity; the next request then waits ~50 s while the container boots. For a
   demo that is opened sporadically (a tribunal, a recruiter), the first click is
   almost always slow.
2. **Repeated external work while awake.** Every chatbot query embeds its text via
   the Gemini API, and the muscle/exercise catalog is re-fetched from Neon on every
   page load — even though it changes rarely. This adds latency and spends free-tier
   quota on work we already did moments ago.

We want to mitigate both **without adding paid services** and without coupling the
domain to any specific cache technology.

## Decision

Three complementary, independent measures:

1. **Keep-alive cron** (`.github/workflows/keep-alive.yml`): ping `/health` every
   ~10 min so Render never idles into a cold start. A single free instance running
   ~24/7 stays within Render's monthly instance-hours, so it remains €0. This is the
   only real fix for the cold start — a cache cannot help, because while the backend
   sleeps the very process that would read the cache is down.

2. **Catalog caching** at the edges of the data path: `Cache-Control:
   public, max-age=300, stale-while-revalidate=86400` on the catalog endpoints, plus
   a localStorage stale-while-revalidate in the explorer store (paint cached data
   instantly, then revalidate). This makes the explorer instant on repeat loads and
   keeps it usable if the backend is briefly cold.

3. **`CachePort`** (domain) with `InMemoryCache` (default, zero-setup) and
   `RedisCache` (Upstash free tier) adapters. Used to cache the **query embedding**
   so repeated questions skip the Gemini call. Selected by `CACHE_PROVIDER`; falls
   back to in-memory when Redis is selected without a `REDIS_URL`. Cache operations
   are best-effort — a cache failure degrades to a miss, never breaking a request.

## Consequences

- The demo is fast on the first click (keep-alive) and instant for the explorer on
  repeat visits (catalog cache), at no cost.
- Caching lives behind a port, so swapping in-memory ↔ Redis is a config change; the
  use cases and domain are untouched (consistent with ADR-0002).
- With a single Render instance, the in-memory cache already works; Redis (Upstash)
  only adds value across restarts/instances, so it is optional.
- Trade-offs accepted: GitHub scheduled runs can be delayed under load (a stricter
  cadence would need an external monitor like UptimeRobot); cached catalog data can
  be up to `max-age` stale (fine for a rarely-changing catalog); the embedding cache
  is keyed by query text, so a change of embedding model needs a key-version bump.
- Adds a `redis` dependency (light, pure-Python client), imported lazily so the
  in-memory default works even if it were absent.
