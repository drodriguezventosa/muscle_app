"""LLM adapters.

StubLLM needs no external service (zero-setup default). OllamaLLM and GeminiLLM
call out over HTTP and are selected via configuration.
"""

from typing import Any

import httpx

from app.domain.ports.ai import LLMPort

_TIMEOUT = httpx.Timeout(30.0)


class StubLLM(LLMPort):
    """Deterministic reply with no external call.

    The concrete exercise suggestions are returned separately by the RAG use
    case, so even this stub yields a coherent, useful response for the demo.
    """

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        return (
            "Estas son algunas recomendaciones basadas en tu consulta y en el "
            "catálogo de ejercicios. Revisa la lista y elige según tu material y nivel."
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
    _FALLBACK = (
        "Aquí tienes ejercicios que encajan con tu consulta; revisa la lista y "
        "elige según tu material y nivel."
    )

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self._ENDPOINT}/{self._model}:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, params={"key": self._api_key}, json=payload)
            response.raise_for_status()
            data = response.json()
        return self._extract_text(data) or self._FALLBACK

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
