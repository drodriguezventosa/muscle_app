"""Port for a simple key/value cache with per-entry TTL.

Concrete adapters (in-memory, Redis) live in `app.infrastructure.cache`. The
application layer depends only on this. Implementations must be best-effort: a
cache failure should degrade to a miss, never raise into the request path.
"""

from abc import ABC, abstractmethod


class CachePort(ABC):
    """String key/value cache with expiry."""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Return the cached value for `key`, or None if missing/expired/unavailable."""

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Store `value` under `key` for `ttl_seconds`. Best-effort; never raises."""
