"""Async SQLAlchemy engine and session factory.

The engine is created lazily from settings so importing this module has no side
effects (important for tests that use their own database URL).
"""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    """Return a cached async engine built from application settings."""
    settings = get_settings()
    # Managed Postgres (Neon, etc.) needs TLS; asyncpg enables it via connect_args.
    connect_args = {"ssl": True} if settings.db_ssl else {}
    return create_async_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return a cached session factory bound to the engine."""
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a database session per request."""
    factory = get_session_factory()
    async with factory() as session:
        yield session
