#!/usr/bin/env sh
# First-boot bootstrap for the Space: ensure the schema + catalog exist on the
# managed database, then serve the API. All steps are idempotent, so it is safe
# to run on every container start.
set -eu

python - <<'PY'
import asyncio

from sqlalchemy import text

from app.core.config import get_settings
from app.infrastructure.ai.factory import build_embedding
from app.infrastructure.persistence.database import get_engine, get_session_factory
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.seed import seed
from app.infrastructure.persistence.embeddings_backfill import backfill_embeddings


async def main() -> None:
    async with get_engine().begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)  # create missing tables only
    async with get_session_factory()() as session:
        await seed(session)  # skips if already seeded
        await backfill_embeddings(session, build_embedding(get_settings()))  # fills nulls only


asyncio.run(main())
PY

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
