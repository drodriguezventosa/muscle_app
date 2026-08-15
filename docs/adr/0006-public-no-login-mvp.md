# 6. Public, no-login MVP; auth and monetization deferred

- Status: partially superseded by [ADR-0021](0021-coaching-data-and-progress-sync.md)
- Date: 2026-07-14

> Still true for the explorer, the chatbot, the workout generator and nutrition:
> all of them work with no account. What changed is that the coaching area now has
> real sign-in (Argon2id + JWT, demo accounts only, no public sign-up). Monetization
> remains a labelled simulation.

## Context

The product hook (muscle explorer + recommendation chatbot) should be usable with
zero friction. Trainers/subscriptions are the future monetizable part but must not
block or complicate the MVP.

## Decision

Ship the MVP fully public: no registration, no login. The API only exposes
non-sensitive catalog data (muscles, exercises, generated routines), so there is no
per-user resource to protect. The domain is still modelled to accept auth later
(roles, `PaymentPort`, user/subscription tables foreseen) without rework.

## Consequences

- No auth attack surface in the MVP; simpler UX and deployment.
- Personal input (e.g. workout attributes) is processed statelessly, never stored.
- Auth + monetization become a separate, additive phase (see product roadmap).
