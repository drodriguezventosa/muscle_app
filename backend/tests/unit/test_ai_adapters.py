"""Unit tests for the default (dependency-free) AI adapters."""

import math

import httpx
import pytest

from app.infrastructure.ai.embeddings import FakeEmbedding, GeminiEmbedding
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


async def test_gemini_embedding_single_normalizes_and_hits_embedcontent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_post(self: httpx.AsyncClient, url: str, **kwargs: object) -> httpx.Response:
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        return httpx.Response(
            200, json={"embedding": {"values": [3.0, 4.0]}}, request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    vector = await GeminiEmbedding("k", "text-embedding-004", dim=2).embed("chest at home")

    assert str(captured["url"]).endswith("models/text-embedding-004:embedContent")
    assert captured["json"] == {  # type: ignore[comparison-overlap]
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": "chest at home"}]},
        "outputDimensionality": 2,
    }
    assert vector == [0.6, 0.8]  # L2-normalized (3,4) -> (0.6,0.8)


async def test_gemini_embedding_many_embeds_each_via_embedcontent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # gemini-embedding-001 has no synchronous batch method, so embed_many must
    # call embedContent once per text and preserve input order.
    raw = {"a": [1.0, 0.0], "b": [0.0, 2.0]}

    async def fake_post(self: httpx.AsyncClient, url: str, **kwargs: object) -> httpx.Response:
        assert url.endswith(":embedContent")
        json_body = kwargs["json"]
        text = json_body["content"]["parts"][0]["text"]  # type: ignore[index]
        return httpx.Response(
            200, json={"embedding": {"values": raw[text]}}, request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    vectors = await GeminiEmbedding("k", "gemini-embedding-001", dim=2).embed_many(["a", "b"])

    assert vectors == [[1.0, 0.0], [0.0, 1.0]]  # each L2-normalized, order preserved
