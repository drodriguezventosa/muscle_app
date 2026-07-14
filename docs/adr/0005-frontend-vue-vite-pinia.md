# 5. Vue 3 + Vite + TypeScript + Pinia for the frontend

- Status: accepted
- Date: 2026-07-14

## Context

The explorer and chatbot need a fast, maintainable single-page app with a small
bundle, good developer experience and typed API calls, deployable for free.

## Decision

Use Vue 3 (Composition API, `<script setup>`) with Vite, TypeScript (strict) and
Pinia for state. Routes are lazy-loaded; a thin typed API client maps the backend's
snake_case payloads to camelCase. Tests with Vitest + Vue Test Utils, e2e with
Playwright.

## Consequences

- Small, code-split bundles; strong typing catches integration errors early.
- Pinia stores (explorer, chat, workouts) keep views thin and testable.
- Team must follow the Composition API conventions in the `frontend-dev` skill.
