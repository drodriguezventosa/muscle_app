"""Embedding adapters.

FakeEmbedding is deterministic and dependency-free (default, for dev/CI).
SentenceTransformerEmbedding gives real semantic vectors but needs the optional
`.[ai]` extra (torch), so it is imported lazily.
"""

import asyncio
import hashlib
import math

from app.domain.ports.ai import EmbeddingPort


class FakeEmbedding(EmbeddingPort):
    """Deterministic, normalized pseudo-embedding derived from a text hash.

    Not semantic, but stable and free — enough to exercise pgvector search and
    the full RAG flow without downloading a model.
    """

    def __init__(self, dim: int) -> None:
        self._dim = dim

    def _vector(self, text: str) -> list[float]:
        values: list[float] = []
        counter = 0
        while len(values) < self._dim:
            digest = hashlib.sha256(f"{text}:{counter}".encode()).digest()
            for byte in digest:
                values.append((byte / 255.0) * 2 - 1)  # map to [-1, 1]
                if len(values) >= self._dim:
                    break
            counter += 1
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    async def embed(self, text: str) -> list[float]:
        return self._vector(text)

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]


class SentenceTransformerEmbedding(EmbeddingPort):
    """Real embeddings via sentence-transformers (requires the `.[ai]` extra)."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    async def embed(self, text: str) -> list[float]:
        vector = await asyncio.to_thread(self._model.encode, text)
        return [float(x) for x in vector]

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        matrix = await asyncio.to_thread(self._model.encode, texts)
        return [[float(x) for x in row] for row in matrix]
