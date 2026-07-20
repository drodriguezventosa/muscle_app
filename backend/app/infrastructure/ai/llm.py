"""LLM adapters.

StubLLM needs no external service (zero-setup default). OllamaLLM (local),
GeminiLLM and GroqLLM call out over HTTP and are selected via configuration.

The hosted adapters degrade gracefully: on any HTTP error (notably free-tier
429s) they log and return a helpful fallback message, so the chat endpoint keeps
returning the retrieved exercises instead of a 500. The LLM only narrates the
recommendation — the real work (embeddings + pgvector retrieval) happens upstream.
"""

from typing import Any

import httpx
import structlog

from app.domain.ports.ai import LLMPort

_TIMEOUT = httpx.Timeout(30.0)
_logger = structlog.get_logger(__name__)

# Returned when the provider is unreachable or rate-limited, so the chat still
# yields a coherent reply alongside the items the RAG use case already found.
# Domain-neutral on purpose: this text is shared by the exercise and meal chats.
_FALLBACK = "Aquí tienes algunas sugerencias que encajan con tu consulta; revisa la lista."


def _log_llm_error(provider: str, exc: httpx.HTTPError) -> None:
    """Log an LLM call failure (status + body when available) without raising."""
    if isinstance(exc, httpx.HTTPStatusError):
        _logger.warning(
            "llm_request_failed",
            provider=provider,
            status=exc.response.status_code,
            body=exc.response.text[:300],
        )
    else:
        _logger.warning("llm_request_failed", provider=provider, error=repr(exc))


class StubLLM(LLMPort):
    """Deterministic reply with no external call.

    The concrete suggestions (exercises or foods) are returned separately by the
    RAG use case, so even this stub yields a coherent response. Kept domain-neutral
    since it backs both the exercise and the meal chats.
    """

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        return (
            "Aquí tienes algunas sugerencias basadas en tu consulta y en el catálogo. "
            "Revisa la lista y elige la que mejor se adapte a ti."
        )


class OllamaLLM(LLMPort):
    """Local, free LLM served by Ollama."""

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{self._base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        return str(data["message"]["content"]).strip()


class GeminiLLM(LLMPort):
    """Google Gemini via its free-tier REST API."""

    _ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self._ENDPOINT}/{self._model}:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
        }
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                response = await client.post(url, params={"key": self._api_key}, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            _log_llm_error("gemini", exc)
            return _FALLBACK
        return self._extract_text(data) or _FALLBACK

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        """Concatenate the text parts of the first candidate, tolerantly.

        Some models (e.g. gemini-2.5 with thinking) return several parts or omit
        `parts` entirely on safety/length stops; skip non-text parts and never
        raise, so a valid HTTP response can't turn into a 500 downstream.
        """
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts") or []
        texts = [p["text"] for p in parts if isinstance(p, dict) and isinstance(p.get("text"), str)]
        return "".join(texts).strip()


class GroqLLM(LLMPort):
    """Groq's free-tier, OpenAI-compatible chat API (Llama models).

    A more generous free tier than Gemini's chat quota, no credit card required.
    """

    _ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                response = await client.post(self._ENDPOINT, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            _log_llm_error("groq", exc)
            return _FALLBACK
        return self._extract_text(data) or _FALLBACK

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            return ""
        content = choices[0].get("message", {}).get("content")
        return content.strip() if isinstance(content, str) else ""
