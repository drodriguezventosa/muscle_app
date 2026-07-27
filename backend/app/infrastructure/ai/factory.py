"""Build the configured AI adapters from settings (composition root helpers)."""

from app.core.config import Settings
from app.domain.ports.ai import EmbeddingPort, LLMPort
from app.domain.ports.vision import VisionPort
from app.infrastructure.ai.embeddings import (
    FakeEmbedding,
    GeminiEmbedding,
    JinaEmbedding,
    SentenceTransformerEmbedding,
)
from app.infrastructure.ai.llm import GeminiLLM, GroqLLM, OllamaLLM, StubLLM
from app.infrastructure.ai.vision import GeminiVision, StubVision


def build_embedding(settings: Settings) -> EmbeddingPort:
    if settings.embedding_provider == "sentence_transformers":
        return SentenceTransformerEmbedding(settings.embedding_model)
    if settings.embedding_provider == "jina":
        return JinaEmbedding(settings.jina_api_key, settings.jina_model, settings.embedding_dim)
    if settings.embedding_provider == "gemini":
        return GeminiEmbedding(
            settings.gemini_api_key, settings.gemini_embedding_model, settings.embedding_dim
        )
    return FakeEmbedding(settings.embedding_dim)


def build_vision(settings: Settings) -> VisionPort:
    if settings.vision_provider == "gemini":
        return GeminiVision(settings.gemini_api_key, settings.vision_model)
    return StubVision()


def build_llm(settings: Settings) -> LLMPort:
    if settings.llm_provider == "ollama":
        return OllamaLLM(settings.ollama_base_url, settings.llm_model)
    if settings.llm_provider == "gemini":
        return GeminiLLM(settings.gemini_api_key, settings.gemini_model)
    if settings.llm_provider == "groq":
        return GroqLLM(settings.groq_api_key, settings.groq_model)
    return StubLLM()
