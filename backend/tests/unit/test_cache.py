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
