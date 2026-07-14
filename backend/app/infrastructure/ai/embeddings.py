"""Embedding adapters.

FakeEmbedding is deterministic and dependency-free (default, for dev/CI).
GeminiEmbedding uses Google's free embedding REST API — real semantic vectors
with no local model, so it fits memory-constrained free hosts (e.g. Render).
SentenceTransformerEmbedding gives real semantic vectors but needs the optional
`.[ai]` extra (torch), so it is imported lazily.
"""

import asyncio
import hashlib
import math

import httpx

from app.domain.ports.ai import EmbeddingPort

_TIMEOUT = httpx.Timeout(30.0)


def _normalize(values: list[float]) -> list[float]:
    """L2-normalize a vector (unit length) for stable cosine similarity."""
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


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
        return _normalize(values)

    async def embed(self, text: str) -> list[float]:
        return self._vector(text)

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]


class GeminiEmbedding(EmbeddingPort):
    """Real embeddings via Google's free-tier embedding REST API.

    Uses `outputDimensionality` (Matryoshka truncation) so the model returns
    vectors of `dim` (default 384), keeping the existing pgvector column size —
    no re-seed or schema change. Truncated vectors are not unit-length, so we
    L2-normalize them here for stable cosine similarity.

    `gemini-embedding-001` exposes only the single `embedContent` method (no
    synchronous batch), so `embed_many` embeds each text individually with
    bounded concurrency to respect free-tier rate limits.
    """

    _ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"
    _MAX_CONCURRENCY = 5

    def __init__(self, api_key: str, model: str, dim: int) -> None:
        self._api_key = api_key
        self._model = model if model.startswith("models/") else f"models/{model}"
        self._dim = dim

    async def _embed_one(self, client: httpx.AsyncClient, text: str) -> list[float]:
        url = f"{self._ENDPOINT}/{self._model.split('/', 1)[1]}:embedContent"
        payload = {
            "model": self._model,
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": self._dim,
        }
        response = await client.post(url, params={"key": self._api_key}, json=payload)
        response.raise_for_status()
        return _normalize([float(x) for x in response.json()["embedding"]["values"]])

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            return await self._embed_one(client, text)

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        semaphore = asyncio.Semaphore(self._MAX_CONCURRENCY)

        async def bounded(client: httpx.AsyncClient, text: str) -> list[float]:
            async with semaphore:
                return await self._embed_one(client, text)

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            return list(await asyncio.gather(*(bounded(client, text) for text in texts)))


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
