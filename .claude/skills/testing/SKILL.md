---
name: testing
description: How to write and run tests (unit, integration, e2e), database fixtures and the coverage gate. Use when adding tests or before reporting a change as done.
---

# Testing

## Philosophy

A strong test suite lets us **self-validate every change** by running it — never assume a change works. After any edit, run the relevant tests and report the real result.

## Backend (pytest)

- `tests/unit/` — pure logic and use cases with **fake ports** (no DB, no network).
- `tests/integration/` — routers and repositories against an ephemeral database.
- `tests/e2e/` — full request/response flows through the app.
- Shared fixtures in `tests/conftest.py` (`client`, `settings`).
- Coverage gate: **≥ 80%** (`--cov-fail-under=80` in `pyproject.toml`).
- Integration tests run on a **fixed calendar day** (`FROZEN_NOW` in `tests/integration/conftest.py`, via `time-machine`): the demo seed is generated around "today" and has deload weeks, so real dates made the suite fail on some weeks. Build test dates from `date.today()` inside the test (it is frozen too), never from hardcoded 2026 dates.

```bash
cd backend && pytest                         # tests + coverage gate
pytest tests/unit/test_health.py -v          # a single file
```

## Frontend

- **Vitest** unit/component tests in `tests/*.spec.ts` (jsdom + Vue Test Utils).
- **Playwright** e2e in `tests/e2e/*.e2e.ts` for critical user flows.

```bash
cd frontend && npm run test        # vitest
npm run test:e2e                   # playwright
```

## Rules

- Every feature/bugfix ships with tests. Test behavior, not implementation details.
- Name tests by the behavior they assert. Code and comments in English.
