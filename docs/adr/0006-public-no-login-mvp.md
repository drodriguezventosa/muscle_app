# 6. Public, no-login MVP; auth and monetization deferred

- Status: accepted
- Date: 2026-07-14

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
