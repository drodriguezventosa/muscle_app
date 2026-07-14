"""Build the configured cache adapter from settings (composition root helper)."""

from app.core.config import Settings
from app.domain.ports.cache import CachePort
from app.infrastructure.cache.memory import InMemoryCache


def build_cache(settings: Settings) -> CachePort:
    # Fall back to the in-memory cache if Redis is selected but no URL is set,
    # so a missing REDIS_URL never breaks the app.
    if settings.cache_provider == "redis" and settings.redis_url:
        from app.infrastructure.cache.redis_cache import RedisCache

        return RedisCache(settings.redis_url)
    return InMemoryCache()
