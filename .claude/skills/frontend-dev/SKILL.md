---
name: frontend-dev
description: Conventions for the Vue 3 + Vite + TypeScript frontend — Composition API, Pinia, the typed API client, minimalist accessible design and performance. Use when editing anything under frontend/src.
---

# Frontend development (Vue 3 + Vite + TypeScript)

## Structure

- `src/components/` — reusable, presentational components.
- `src/views/` — route-level pages (lazy-loaded in `src/router/index.ts`).
- `src/stores/` — Pinia stores for shared state.
- `src/api/client.ts` — the single typed HTTP client; call the API only through it.
- `src/assets/styles.css` — design tokens (colors, spacing, radius). Reuse them, don't hardcode values.

## Rules

- **Composition API + `<script setup lang="ts">`** everywhere. Strict TypeScript, no `any`.
- Code and comments in **English**; user-facing UI copy may be in Spanish.
- **Design**: modern and minimalist — use the CSS tokens, generous whitespace, few colors.
- **Accessibility (WCAG)**: semantic HTML, ARIA roles/labels (especially the interactive SVG body and the chat), visible focus, sufficient contrast, honor `prefers-reduced-motion`.
- **Performance**: lazy-load views, keep bundles small, optimize the SVG, avoid heavy dependencies.
- Always render the `HealthDisclaimer` on views with exercise recommendations.

## Recipe: add a view

1. Create `src/views/XxxView.vue` with `<script setup lang="ts">`.
2. Add a lazy route in `src/router/index.ts`.
3. Fetch data via `@/api/client`.
4. Add a Vitest spec in `tests/Xxx.spec.ts`; add a Playwright `*.e2e.ts` for critical flows.

## Commands

```bash
npm run dev          # dev server
npm run lint         # eslint + prettier
npm run typecheck    # vue-tsc
npm run test         # vitest
npm run test:e2e     # playwright
```
