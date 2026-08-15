# 12. Trainers/coaching shown as a frontend preview mockup

- Status: superseded by [ADR-0021](0021-coaching-data-and-progress-sync.md),
  [ADR-0024](0024-one-trainer-per-student.md) and
  [ADR-0026](0026-the-plan-belongs-to-the-pair.md)
- Date: 2026-07-14

> The mockup is gone. The coaching area is a real feature: trainers are users with
> a profile, the trainer-student link lives in the database and gates the plan, and
> the hard-coded student list and the `localStorage` subscription were deleted.

## Context

The personal-trainer feature (hire a coach; a coach manages students, sees their
progress and assigns workouts) is the future monetizable part. We want to show it
now to demonstrate the app's potential, without building auth or payments yet.

## Decision

Ship it as a **frontend-only mockup** with sample data, clearly labelled "preview".
A single `/trainers` route with two tabs: *Hire a trainer* (cards with € prices and
a demo "hire" dialog that explains payments come later) and *Trainer dashboard*
(sample students → their sample progress → assign exercises via checkboxes). Demo
assignments persist in localStorage. No backend, no login, no real payment (see
ADR-0006).

## Consequences

- Communicates the product vision without auth/payment scope or cost.
- When the deferred auth+monetization phase lands, these views get wired to real
  accounts, a `PaymentPort` and persisted assignments.
- Sample trainer/student data is hardcoded and not localized (acceptable for a preview).
