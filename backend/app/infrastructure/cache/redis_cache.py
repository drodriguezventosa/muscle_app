"""Redis cache adapter (e.g. Upstash free tier over TLS).

All operations are wrapped so a Redis outage or misconfiguration degrades to a
cache miss — it must never break a request. `redis` is imported lazily so the
in-memory default works even if the package isn't installed.

Failures are logged once per process: swallowing them silently hid a
misconfigured URL in production for weeks (Upstash needs `rediss://`, not
`redis://`), so the cache looked enabled while every operation failed.
"""

from typing import Any, cast

import structlog

from app.domain.ports.cache import CachePort

_logger = structlog.get_logger(__name__)


class RedisCache(CachePort):
    def __init__(self, url: str) -> None:
        import redis.asyncio as redis

        self._client: Any = redis.from_url(url, decode_responses=True)
        # Managed Redis providers (Upstash and friends) require TLS; a plain
        # `redis://` URL fails on connect, which used to be invisible.
        self._needs_tls_hint = url.startswith("redis://")
        self._warned = False

    def _warn_once(self, exc: Exception) -> None:
        if self._warned:
            return
        self._warned = True
        _logger.warning(
            "cache_unavailable",
            error=repr(exc),
            hint=(
                "URL uses redis:// — managed providers such as Upstash require rediss:// (TLS)"
                if self._needs_tls_hint
                else "serving without cache"
            ),
        )

    async def get(self, key: str) -> str | None:
        try:
            return cast("str | None", await self._client.get(key))
        except Exception as exc:  # noqa: BLE001 - cache errors must not reach the request
            self._warn_once(exc)
            return None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        # Best-effort write; a cache failure must never break the request.
        try:
            await self._client.set(key, value, ex=ttl_seconds)
        except Exception as exc:  # noqa: BLE001 - cache errors must not reach the request
            self._warn_once(exc)
