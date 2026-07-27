"""Unit tests for the in-memory cache adapter."""

from app.infrastructure.cache.memory import InMemoryCache


async def test_set_get_roundtrip() -> None:
    cache = InMemoryCache()
    assert await cache.get("k") is None
    await cache.set("k", "v", 60)
    assert await cache.get("k") == "v"


async def test_expired_entry_returns_none() -> None:
    cache = InMemoryCache()
    await cache.set("k", "v", 0)  # ttl 0 → already expired on read
    assert await cache.get("k") is None


async def test_redis_cache_degrades_to_a_miss_and_warns_once() -> None:
    # A misconfigured URL (Upstash needs rediss://) must not break requests, but
    # it must be visible in the logs — it silently hid a broken cache in prod.
    from app.infrastructure.cache.redis_cache import RedisCache

    cache = RedisCache.__new__(RedisCache)  # skip __init__ (no redis server here)

    class _Boom:
        async def get(self, key: str) -> str:
            raise ConnectionError("Connection closed by server.")

        async def set(self, key: str, value: str, ex: int) -> None:
            raise ConnectionError("Connection closed by server.")

    cache._client = _Boom()  # type: ignore[attr-defined]
    cache._needs_tls_hint = True  # type: ignore[attr-defined]
    cache._warned = False  # type: ignore[attr-defined]

    assert await cache.get("k") is None  # degrades to a miss
    await cache.set("k", "v", 60)  # does not raise
    assert cache._warned is True  # type: ignore[attr-defined]
