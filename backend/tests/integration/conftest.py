"""Fixtures for integration tests that require a real PostgreSQL + pgvector.

Tests are skipped unless TEST_DATABASE_URL is set (e.g. in CI, where a Postgres
service is available). Locally: `docker compose up db` and export the URL.
"""

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.models import Base

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """Provide a session against a freshly-created schema, torn down after.

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

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db_session:
        yield db_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
