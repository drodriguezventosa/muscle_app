# 4. Provider-agnostic LLM behind a port

- Status: accepted
- Date: 2026-07-06

## Context

The chatbot needs an LLM, but the project must be free to run and deploy. Local models
(Ollama) are ideal in development; a hosted free tier (Gemini) is better for the deployed
demo since it needs no GPU.

## Decision

Define an `LLMPort` in the domain and provide adapters selected by the `LLM_PROVIDER`
environment variable: `StubLLM` (zero-setup default), `OllamaLLM` (development),
`GeminiLLM`, and `GroqLLM`. The deployed demo uses **Groq** for chat text, because
Gemini's free *chat* quota (`generateContent`) proved too low (429 on the first
request), while Groq offers a generous free tier with no credit card. Embeddings are
generated via the Gemini API (its embedding quota is separate and sufficient).

The hosted adapters degrade gracefully: on any HTTP error (notably free-tier 429s)
they log and return a fallback message, so the chat endpoint returns the retrieved
exercises instead of a 500 — the LLM only narrates results the RAG step already found.

## Consequences

- Zero cost in development and deploy (Groq + Gemini embeddings free tiers, no card).
- Switching or adding providers never touches the domain or use cases.
- Prompt-injection guards live in the application layer, shared across adapters.
- The chat stays useful even when a provider is rate-limited (graceful fallback).
