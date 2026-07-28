# 25. The boot reconciles schema *changes*, and the seed fills gaps

- Status: accepted
- Date: 2026-07-28

## Context

The deployed app runs `python -m app.bootstrap` — `create_all` plus the seed —
because Alembic on a free-tier deploy needs a migration step nobody runs
(ADR-0016). `create_all` only ever *creates missing tables*. Three changes have
now reached production silently unapplied, each failing more quietly than the
last:

1. **A new column** on an existing table (`workout_logs.sets`): every query
   selecting it returned a 500 while unrelated endpoints kept working. Fixed by
   adding missing columns on boot (ADR-0021 addendum, PR #55).
2. **A changed unique constraint**: `uq_trainer_student` moved from
   `(trainer_id, student_id)` to `(student_id)` to express "a student has at most
   one trainer" (ADR-0024). On the deployed table it stayed on the pair. Nothing
   errored — the rule simply was not enforced. Hiring a *second* trainer did not
   conflict, so it inserted a second link and the read of "my trainer" then
   raised, which the checkout modal showed to the user as a **failed payment**.
   Cancelling first worked, because that deleted the row.
3. **Widened seed data**: the demo calendar grew from one week to the whole year,
   but both the plan and the history seeds returned early when their table had
   any rows. Production kept the single week it was first seeded with — the same
   trap the food catalog fell into (ADR-0019).

The pattern behind all three: **a deploy path that only knows how to create
things cannot deliver a change to something that already exists.**

## Decision

**Reconcile changed unique constraints on boot**, next to the column
reconciliation. Each change runs in its own savepoint: a constraint the existing
rows would violate is rolled back to the old one and logged, because resolving
that conflict is a migration's job, not a startup step. Alembic remains the
source of truth and the only path that may rewrite data.

**Invariants are enforced in code, not delegated to the schema.** Hiring a
trainer now deletes the student's other links explicitly and inserts without a
conflict target, so "one trainer per student" holds on either shape of the
constraint — and repairs a database that already has a stray pair. A rule that
lives only in a constraint is a rule that stops existing the moment the
constraint fails to deploy.

**Seeds fill gaps; they never bail because a table is non-empty.** The history
inserts the sessions that are missing, keyed by (exercise, day). The plan writes
the days that carry no prescription at all — a coarser key on purpose, because
the trainer edits that table from the app and a re-seed must not resurrect what
they removed. Nothing existing is ever overwritten: a redeploy must not rewrite
what a student actually lifted.

## Consequences

- A schema change now reaches production on the next deploy for tables, columns
  and unique constraints. Everything else (types, foreign keys, data rewrites)
  still needs Alembic, and the boot logs rather than guesses.
- The demo year lands on the deployed database without dropping anything.
- These reconciliations are tested against a real database *shaped like the
  deployed one* — a legacy constraint installed by hand, a column dropped — since
  a test on a freshly created schema can never see this class of bug.
- The estimated-1RM charts now label their unit ("kg de 1RM est."). Unrelated to
  the deploy path, same root cause in miniature: a value read away from its title
  looked like the weight lifted, so 3 x 10 with 120 kg appeared as "160 kg".
