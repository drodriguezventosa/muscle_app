# 11. Client-side workout progress via localStorage (progressive overload)

- Status: accepted (implemented)
- Date: 2026-07-14

## Context

We want users to log sessions, see day/week progress, and have exercise weights
recalculated as they improve. This needs data persisted over time, but the MVP is
no-login and stores no per-user data (see ADR-0006, ADR-0009).

## Decision

Persist workout logs and per-exercise weights **client-side in the browser
(localStorage)** — no login, no backend storage. When a user completes all sets at
the top of the rep range, suggest a weight increase (progressive overload, e.g.
+2.5 kg upper body / +5 kg lower body) for next time, and show per-exercise / weekly
history. Migrate this data to the backend if/when accounts are added.

## Consequences

- Keeps the no-login, zero-cost, GDPR-friendly posture (health data stays on-device).
- Progress is per-device and not synced across devices or browsers (documented to users).
- Requires adding a per-session weight/reps log on top of the current
  sets×reps×rest routine model.
