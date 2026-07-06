"""Unit tests for the default (dependency-free) AI adapters."""

import math

from app.infrastructure.ai.embeddings import FakeEmbedding
from app.infrastructure.ai.llm import StubLLM


async def test_fake_embedding_is_sized_deterministic_and_normalized() -> None:
    embedding = FakeEmbedding(384)
    first = await embedding.embed("chest at home")
    again = await embedding.embed("chest at home")
    other = await embedding.embed("legs at the gym")

    assert len(first) == 384
    assert first == again  # deterministic
    assert first != other  # different inputs differ
    assert math.isclose(math.sqrt(sum(x * x for x in first)), 1.0, abs_tol=1e-6)  # unit norm


async def test_embed_many_matches_single_embed() -> None:
    embedding = FakeEmbedding(16)
    batch = await embedding.embed_many(["a", "b"])
    assert batch[0] == await embedding.embed("a")
    assert len(batch) == 2


async def test_stub_llm_returns_non_empty_text() -> None:
    reply = await StubLLM().generate("system", "user")
    assert isinstance(reply, str)
    assert reply.strip()
