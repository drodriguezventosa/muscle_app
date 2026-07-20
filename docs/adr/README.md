# Architecture Decision Records

Short, immutable records of significant architecture decisions — the *why* behind
the design. Format: Status · Context · Decision · Consequences (see
[ADR-0001](0001-record-architecture-decisions.md)). One file per decision, numbered
sequentially; supersede rather than edit past decisions.

| # | Decision | Status |
|---|----------|--------|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions (use ADRs) | accepted |
| [0002](0002-hexagonal-architecture.md) | Hexagonal architecture for the backend | accepted |
| [0003](0003-postgres-pgvector.md) | PostgreSQL + pgvector as the single store | accepted |
| [0004](0004-provider-agnostic-llm.md) | Provider-agnostic LLM (ports & adapters) | accepted |
| [0005](0005-frontend-vue-vite-pinia.md) | Vue 3 + Vite + TypeScript + Pinia frontend | accepted |
| [0006](0006-public-no-login-mvp.md) | Public, no-login MVP; auth/monetization deferred | accepted |
| [0007](0007-content-internationalization.md) | Bilingual content (default + `_en`, `?lang=`) | accepted |
| [0008](0008-exercise-media-videos-and-steps.md) | Exercise videos with subtitles + how-to steps | accepted |
| [0009](0009-stateless-workout-generator.md) | Stateless workout generator (POST body) | accepted |
| [0010](0010-cost-zero-tooling-and-deploy.md) | Cost-zero tooling and deployment | accepted |
| [0011](0011-client-side-workout-progress.md) | Client-side workout progress (localStorage) | accepted |
| [0012](0012-trainers-preview-mockup.md) | Trainers/coaching as a frontend preview mockup | accepted |
| [0013](0013-light-dark-theme.md) | Light/dark theme via CSS token overrides | accepted |
| [0014](0014-continuous-deployment.md) | Continuous deployment on merge to main | accepted |
| [0015](0015-performance-caching-and-keepalive.md) | Performance & resilience on free tiers: keep-alive + caching | accepted |
| [0016](0016-nutrition-module.md) | Nutrition module (calculator + food catalog + RAG meal chat) | accepted |
| [0017](0017-onboarding-guided-tour.md) | Onboarding guided tour and section-aware assistant | accepted |
