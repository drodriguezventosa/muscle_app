"""First-boot bootstrap for managed deploys (e.g. Render).

Ensures the schema + catalog exist on the managed database, then exits so the
process manager can start the API server. Every step is idempotent, so it is
safe to run on each deploy/restart.

Run with `python -m app.bootstrap`; the deploy start command then execs uvicorn.
"""

import asyncio
import logging

from sqlalchemy import Connection, inspect, text
from sqlalchemy.schema import CreateColumn

from app.core.config import get_settings
from app.infrastructure.ai.factory import build_embedding
from app.infrastructure.persistence.database import get_engine, get_session_factory
from app.infrastructure.persistence.embeddings_backfill import (
    backfill_embeddings,
    backfill_food_embeddings,
)
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.seed import seed

logger = logging.getLogger(__name__)


def _add_missing_columns(connection: Connection) -> None:
    """Add columns the models declare but the deployed tables do not have.

    `create_all` creates missing *tables* and never touches existing ones, so a
    new column on an old table reached production silently missing — every query
    selecting it failed with a 500 while unrelated endpoints kept working. This
    reconciles the gap on boot, in the same spirit as the rest of the bootstrap.

    Alembic remains the source of truth (and the only path that can rewrite
    data); a column that cannot be added safely is reported rather than forced,
    because filling a NOT NULL column on a populated table is a migration, not
    a startup step.
    """
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue  # create_all just made it, with every column
        present = {column["name"] for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in present:
                continue
            if not column.nullable and column.server_default is None:
                logger.warning(
                    "schema_column_missing table=%s column=%s "
                    "needs a migration (not nullable and no server default)",
                    table.name,
                    column.name,
                )
                continue
            definition = CreateColumn(column).compile(dialect=connection.dialect)
            connection.execute(
                text(f'ALTER TABLE "{table.name}" ADD COLUMN IF NOT EXISTS {definition}')
            )
            logger.info("schema_column_added table=%s column=%s", table.name, column.name)


async def bootstrap() -> None:
    async with get_engine().begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)  # create missing tables only
        await conn.run_sync(_add_missing_columns)  # ...and columns they gained since
    async with get_session_factory()() as session:
        await seed(session)  # skips if already seeded
        # Fills null vectors only, using the configured embedding provider.
        # Non-fatal: an embedding-provider hiccup must not stop the API from
        # serving (the explorer + filters work without vectors; semantic search
        # degrades until the next successful backfill).
        try:
            settings = get_settings()
            if settings.embedding_rebuild:
                # Vectors from a different embedding model are not comparable, so
                # drop them and let the backfill below recompute every row.
                await session.execute(text("UPDATE exercises SET embedding = NULL"))
                await session.execute(text("UPDATE foods SET embedding = NULL"))
                await session.commit()
                print("EMBEDDING_REBUILD set: cleared stored vectors, recomputing.")
            embedding = build_embedding(settings)
            count = await backfill_embeddings(session, embedding)
            food_count = await backfill_food_embeddings(session, embedding)
            print(f"Backfilled embeddings for {count} exercises and {food_count} foods.")
        except Exception as exc:  # noqa: BLE001 - log and keep serving
            print(f"WARNING: embedding backfill skipped ({exc!r}); serving without vectors.")


if __name__ == "__main__":
    asyncio.run(bootstrap())
