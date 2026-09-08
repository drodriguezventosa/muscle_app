"""Fixtures for integration tests that require a real PostgreSQL + pgvector.

Tests are skipped unless TEST_DATABASE_URL is set (e.g. in CI, where a Postgres
service is available). Locally: `docker compose up db` and export the URL.
"""

import os
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
import time_machine
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.core.rate_limit import limiter
from app.infrastructure.ai.embeddings import FakeEmbedding
from app.infrastructure.persistence.database import get_session
from app.infrastructure.persistence.embeddings_backfill import backfill_embeddings
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.seed import DEMO_YEAR, seed
from app.main import create_app

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
# Weeks of demo history and plan the tests seed: enough for a past week, the
# current one and one ahead, which is what the assertions look at.
SEED_WEEKS = 3
# The day every integration test runs on. The demo data is anchored to DEMO_YEAR
# and follows training blocks with a deload every ninth week, so the calendar
# decides what the seeded history looks like: the suite failed during a deload
# week (the strength series dipped) and would find no history at all once the
# demo year is over. A Wednesday in the middle of a block keeps the seeded
# window free of deloads and makes the data the same on every run.
FROZEN_NOW = datetime(DEMO_YEAR, 6, 10, 12, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _frozen_calendar() -> Iterator[None]:
    """Run each test on FROZEN_NOW, with the clock ticking from there.

    Ticking (rather than a stopped clock) keeps token lifetimes and rate-limit
    windows behaving as they do in production.
    """
    with time_machine.travel(FROZEN_NOW, tick=True):
        yield


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Start every test with a fresh limiter.

    The limiter is a module-level singleton keyed by client address, and every
    test shares the same one, so without this a test that signs in would spend
    the login budget of the tests that run after it.
    """
    limiter.reset()


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
        # A short window of demo data: the same shapes as production, without
        # re-writing a year of history for every test.
        await seed(db_session, weeks=SEED_WEEKS)
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
