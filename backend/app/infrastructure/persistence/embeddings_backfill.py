"""Compute and store embeddings for exercises that don't have one yet.

Run as a script (`python -m app.infrastructure.persistence.embeddings_backfill`)
after seeding. Uses the configured embedding provider (fake by default).
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.ports.ai import EmbeddingPort
from app.infrastructure.ai.factory import build_embedding
from app.infrastructure.persistence.database import get_session_factory
from app.infrastructure.persistence.models.exercise import ExerciseModel


async def backfill_embeddings(session: AsyncSession, embedding: EmbeddingPort) -> int:
    """Embed exercises missing a vector. Returns how many were updated."""
    result = await session.scalars(select(ExerciseModel).where(ExerciseModel.embedding.is_(None)))
    models = list(result)
    if not models:
        return 0

    # Embed both languages so semantic search works regardless of query locale.
    texts = [
        " ".join(filter(None, [model.name, model.name_en, model.description, model.description_en]))
        for model in models
    ]
    vectors = await embedding.embed_many(texts)
    for model, vector in zip(models, vectors, strict=True):
        model.embedding = vector
    await session.commit()
    return len(models)


async def _main() -> None:
    settings = get_settings()
    embedding = build_embedding(settings)
    factory = get_session_factory()
    async with factory() as session:
        count = await backfill_embeddings(session, embedding)
    print(f"Backfilled embeddings for {count} exercises.")


if __name__ == "__main__":
    asyncio.run(_main())
