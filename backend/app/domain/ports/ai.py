"""Ports for AI capabilities: text embeddings and LLM text generation.

Concrete adapters (fake/sentence-transformers, stub/Ollama/Gemini) live in
`app.infrastructure.ai`. The domain and application layers depend only on these.
"""

from abc import ABC, abstractmethod


class EmbeddingUnavailableError(RuntimeError):
    """The embedding provider could not be reached (outage, quota, bad key).

    Adapters raise this instead of leaking transport errors, so use cases can
    degrade gracefully (e.g. retrieve without semantic ranking) rather than
    letting the request fail.
    """


class EmbeddingPort(ABC):
    """Turns text into fixed-size vectors for semantic search."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return the embedding vector for a single text."""

    @abstractmethod
    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for several texts (order preserved)."""


class LLMPort(ABC):
    """Generates a natural-language answer from a system + user prompt."""

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Return the model's reply. The user prompt is untrusted data."""
