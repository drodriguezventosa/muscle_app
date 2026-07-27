# 21. Coaching data: server-side history mirrored from the offline logger

- Status: accepted
- Date: 2026-07-28

## Context

The trainers area was a mockup with hard-coded students (ADR-0012), and workout
progress lived only in the browser (ADR-0011). Once sign-in existed, a trainer
needed something real to follow: what each student trains, how often, and how
their lifts and body weight evolve. That needs history the server can read, over
a period long enough to show a trend.

Two tensions shaped the design:

- The workout logger must keep working **without an account**. Making progress
  server-only would break the free, no-login promise the rest of the app keeps.
- A demo needs data on day one. A brand-new database with empty charts says
  nothing about what the feature does, and the TFM defence cannot wait twelve
  weeks for one student to generate a curve.

## Decision

Store coaching data in four small tables and treat the browser as the working
copy that the server mirrors.

**Schema** (Alembic `0006`):

- `trainer_students` — the roster. Every read of a student goes through it, so
  "is this student mine?" cannot be forgotten (OWASP A01).
- `student_profiles` — birth year, height, goal and level. Separate from `users`
  (identity vs. training attributes) and entirely nullable, because the app
  collects these on different screens. A **birth year** rather than an age, so
  the row does not silently go stale.
- `workout_logs` — one row per exercise and day, `UNIQUE (user_id,
  exercise_id, logged_on)`. Re-sending the same history updates rows instead of
  duplicating them.
- `body_metrics` — one weigh-in per day, same idea.

**Sync**, not migration: `POST /coaching/me/progress` pushes the local history
and whatever attributes the user has typed elsewhere; localStorage stays the
source of truth. It is best effort and failures are swallowed — a network hiccup
must not surface as an error in the middle of a workout. The user id always
comes from the token, never from the payload, and unknown exercise ids are
skipped instead of failing the whole sync.

**Series are computed server-side** (`GetStudentDashboard`): strength as the
best **Epley** 1RM (`w · (1 + reps/30)`) per exercise and day, body weight as
measured, adherence as distinct training days per week over twelve weeks. Epley
because it needs only weight and reps, which is exactly what the logger records.
The frontend renders what it is given, so both the trainer's view and the
student's own view share one definition of "progress".

**Seeded history**: seven demo students with twelve weeks of sessions and weekly
weigh-ins, generated deterministically (a fixed RNG seed per student) so every
machine tells the same story. Only the two advertised accounts can sign in; the
rest of the roster gets a random password nobody holds.

## Consequences

- A trainer sees real, queryable evolution, and a signed-in student's own
  sessions appear there within seconds of being logged.
- Anonymous use is unchanged: no account, no request, no data leaves the device.
- The mirror can drift if the same account logs from two browsers — accepted;
  the upsert is idempotent per day, and the alternative (server as source of
  truth) would break offline logging.
- Seeded students are demo data living in the same tables as real progress; they
  are identifiable by their `@demo.muscleapp` addresses.
- The dashboard charts (phase 3) need no new endpoints: the series they draw are
  already in the response.
