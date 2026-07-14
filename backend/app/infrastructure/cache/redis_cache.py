"""Redis cache adapter (e.g. Upstash free tier over TLS).

All operations are wrapped so a Redis outage or misconfiguration degrades to a
cache miss — it must never break a request. `redis` is imported lazily so the
in-memory default works even if the package isn't installed.
"""

import contextlib
from typing import Any, cast

from app.domain.ports.cache import CachePort


class RedisCache(CachePort):
    def __init__(self, url: str) -> None:
        import redis.asyncio as redis

        self._client: Any = redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        try:
            return cast("str | None", await self._client.get(key))
        except Exception:  # noqa: BLE001 - cache errors must not reach the request
            return None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        # Best-effort write; a cache failure must never break the request.
        with contextlib.suppress(Exception):
            await self._client.set(key, value, ex=ttl_seconds)
