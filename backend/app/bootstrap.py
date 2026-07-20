"""First-boot bootstrap for managed deploys (e.g. Render).

Ensures the schema + catalog exist on the managed database, then exits so the
process manager can start the API server. Every step is idempotent, so it is
safe to run on each deploy/restart.

Run with `python -m app.bootstrap`; the deploy start command then execs uvicorn.
"""

import asyncio

from sqlalchemy import text

from app.core.config import get_settings
from app.infrastructure.ai.factory import build_embedding
from app.infrastructure.persistence.database import get_engine, get_session_factory
from app.infrastructure.persistence.embeddings_backfill import (
    backfill_embeddings,
    backfill_food_embeddings,
)
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.seed import seed


async def bootstrap() -> None:
    async with get_engine().begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)  # create missing tables only
    async with get_session_factory()() as session:
        await seed(session)  # skips if already seeded
        # Fills null vectors only, using the configured embedding provider.
        # Non-fatal: an embedding-provider hiccup must not stop the API from
        # serving (the explorer + filters work without vectors; semantic search
        # degrades until the next successful backfill).
        try:
            embedding = build_embedding(get_settings())
            count = await backfill_embeddings(session, embedding)
            food_count = await backfill_food_embeddings(session, embedding)
            print(f"Backfilled embeddings for {count} exercises and {food_count} foods.")
        except Exception as exc:  # noqa: BLE001 - log and keep serving
            print(f"WARNING: embedding backfill skipped ({exc!r}); serving without vectors.")


if __name__ == "__main__":
    asyncio.run(bootstrap())
