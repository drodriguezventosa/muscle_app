# 24. One trainer per student, and a demo year behind it

- Status: accepted
- Date: 2026-07-28

## Context

The coaching relationship was half real. `trainer_students` held who follows
whom and drove every access check (ADR-0021), but nothing in the app could
create a row: the trainers on offer were hard-coded in the frontend, and
"hiring" one wrote a subscription into the student's own `localStorage`. So a
student whose trainer was seeded saw no sign of it on the trainers page, and a
student who hired someone gained no plan.

The rule the product wants is simple and was not expressed anywhere: **a student
has at most one trainer; a trainer has many students.**

## Decision

**The relationship is the subscription.** Hiring writes `trainer_students`;
cancelling deletes it. The uniqueness moves from the pair to the student alone
(`UNIQUE (student_id)`), so hiring another trainer *replaces* the link instead of
adding a second — the endpoint is a `PUT`, because there is one slot to set.

**Trainers are users, not frontend data.** A new `trainer_profiles` table holds
what the card shows — specialty, rating, price and a bio in both languages — and
the student count comes from the roster, so a trainer's load is real rather than
decorative. Four are seeded; only the advertised one can sign in, the rest carry
a random password nobody holds, exactly like the roster students.

**The link gates the plan.** "Mi plan" appears in the navigation only when a
trainer is writing it, the route sends a student without one to the trainers
page, and the plan names its author. A plan with nobody behind it is not an
empty state worth showing.

**The payment stays a simulation, and it no longer pretends to be the
relationship.** The checkout modal still fakes a gateway (no card data, ever),
and on success it calls the API. When a real `PaymentPort` arrives it slots in
front of the same call.

## A year of demo data

The calendar and the charts now cover the whole demo year: ~3,300 scheduled
exercises and ~1,500 logged sessions per seed, so navigating to any week of 2026
shows a plan, and the past shows what came of it (roughly 190 done, 40 partial,
36 missed for the demo student). Two details make it read as training rather
than arithmetic:

- **The load curve is asymptotic**, not linear: fast gains that flatten, with a
  deload every nine weeks. A straight line would have put a beginner's squat
  past 200 kg by December.
- **The demo account's current week is written as trained on target.** Whether
  that week came out well is a coin toss the demonstration should not depend on;
  every other week keeps its misses and shortfalls.

The seed takes a `weeks` window. Production writes the year; the tests pass a
short window, because each case re-seeds a fresh schema and a full year each
time turned a one-minute suite into eight.

## Consequences

- What the trainers page shows, what the student's calendar contains and what
  the trainer's roster lists are all the same fact, read from one table.
- Switching trainers moves the whole relationship: the new trainer sees the
  student and their history, the previous one gets a 404 — verified in the tests.
- Cancelling keeps the history and the scheduled plan: what happened, happened,
  and a plan is a record of what was asked.
- The `subscriptions` store, the hard-coded trainer list and the last
  `localStorage` key of the mockup are gone.
- Seeding is heavier. Boot on an empty database writes a few thousand rows once
  (~2 s, bulk-inserted); every later boot finds them and skips.
