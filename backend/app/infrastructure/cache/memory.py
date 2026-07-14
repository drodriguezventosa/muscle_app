"""In-process cache adapter (default, zero-setup).

Shared across requests within a single worker process. Enough for a single-
instance deploy; for multi-instance or persistence use the Redis adapter.
"""

import time

from app.domain.ports.cache import CachePort


class InMemoryCache(CachePort):
    def __init__(self) -> None:
        # key -> (expires_at_monotonic, value)
        self._store: dict[str, tuple[float, str]] = {}

    async def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._store[key] = (time.monotonic() + ttl_seconds, value)
