"""Fixtures for integration tests that require a real PostgreSQL + pgvector.

Tests are skipped unless TEST_DATABASE_URL is set (e.g. in CI, where a Postgres
service is available). Locally: `docker compose up db` and export the URL.
"""

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.infrastructure.ai.embeddings import FakeEmbedding
from app.infrastructure.persistence.database import get_session
from app.infrastructure.persistence.embeddings_backfill import backfill_embeddings
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.seed import seed
from app.main import create_app

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest_asyncio.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """Provide an engine against a freshly-created schema, torn down after.

    Skips the test when no test database is configured (e.g. local runs without
    Docker); CI sets TEST_DATABASE_URL via a Postgres service.
    """
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set; skipping DB integration tests")
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """A database session bound to the test engine."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as db_session:
        yield db_session


@pytest_asyncio.fixture
async def api_client(db_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    """An HTTP client for the app, wired to the seeded test database."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as db_session:
        await seed(db_session)
        # Backfill embeddings so the RAG search returns results in tests.
        await backfill_embeddings(db_session, FakeEmbedding(384))

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        async with factory() as db_session:
            yield db_session

    app = create_app(Settings(app_env="test", cors_origins=["http://testserver"]))
    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()
