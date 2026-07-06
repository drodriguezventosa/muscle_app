# 4. Provider-agnostic LLM behind a port

- Status: accepted
- Date: 2026-07-06

## Context

The chatbot needs an LLM, but the project must be free to run and deploy. Local models
(Ollama) are ideal in development; a hosted free tier (Gemini) is better for the deployed
demo since it needs no GPU.

## Decision

Define an `LLMPort` in the domain and provide two adapters: `OllamaLLMAdapter`
(development) and `GeminiLLMAdapter` (deploy). Selection is driven by the `LLM_PROVIDER`
environment variable. Embeddings are generated locally with `sentence-transformers` (free).

## Consequences

- Zero cost in development; free-tier cost in the deployed demo.
- Switching or adding providers never touches the domain or use cases.
- Prompt-injection guards live in the application layer, shared across adapters.
