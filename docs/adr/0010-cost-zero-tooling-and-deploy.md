# 10. Cost-zero tooling and deployment (no billable free tiers)

- Status: accepted
- Date: 2026-07-14

## Context

As a thesis project, the hard constraint is zero cost with zero risk of being
charged. "Has a free tier" is not enough if it can bill or requires a credit card.

## Decision

Use only tools that are genuinely free: open-source / self-hostable, or hosted free
tiers that are free because the repo is public, or that our tiny usage will never
exceed and that never auto-charge / require a card.

- Quality/CI: GitHub Actions (free for public), CodeQL, Trivy, Lighthouse CI, k6 OSS
  CLI, SonarCloud & CodeRabbit & Codecov (free for public repos), GlitchTip (self-host)
  or structured logs instead of hosted Sentry.
- Deploy (target 0 €/mo, no card): frontend on Vercel Hobby / Cloudflare Pages;
  database on Neon (Postgres + pgvector, pauses instead of billing); backend on
  Hugging Face Spaces (Docker) or Render free; LLM via Gemini free API or the stub.
  **Avoid GCP Cloud Run** (requires a billing account + card).

## Consequences

- Cold starts and free-tier rate limits are accepted (irrelevant for a demo).
- Any new service must state why it stays free for us and flag card/billing needs.
