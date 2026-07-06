# 2. Hexagonal architecture for the backend

- Status: accepted
- Date: 2026-07-06

## Context

The backend must stay maintainable and testable, and must let us swap infrastructure
(LLM provider, payments, even the database) without rewriting business logic.

## Decision

Adopt hexagonal architecture (ports & adapters): `domain` (entities + ports),
`application` (use cases), `infrastructure` (adapters), `api` (FastAPI). Dependencies
point inwards; the domain has no framework or I/O dependencies.

## Consequences

- Business logic is unit-testable with fake ports (no DB/network needed).
- Swapping an adapter (e.g. Ollama → Gemini) does not touch the domain.
- Slightly more boilerplate than a flat FastAPI app; justified by the requirements.
