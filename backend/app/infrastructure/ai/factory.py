"""Build the configured AI adapters from settings (composition root helpers)."""

from app.core.config import Settings
from app.domain.ports.ai import EmbeddingPort, LLMPort
from app.infrastructure.ai.embeddings import FakeEmbedding, SentenceTransformerEmbedding
from app.infrastructure.ai.llm import GeminiLLM, OllamaLLM, StubLLM


def build_embedding(settings: Settings) -> EmbeddingPort:
    if settings.embedding_provider == "sentence_transformers":
        return SentenceTransformerEmbedding(settings.embedding_model)
    return FakeEmbedding(settings.embedding_dim)


def build_llm(settings: Settings) -> LLMPort:
    if settings.llm_provider == "ollama":
        return OllamaLLM(settings.ollama_base_url, settings.llm_model)
    if settings.llm_provider == "gemini":
        return GeminiLLM(settings.gemini_api_key, settings.gemini_model)
    return StubLLM()
