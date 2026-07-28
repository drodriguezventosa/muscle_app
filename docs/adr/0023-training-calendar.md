# 23. Training calendar: prescription apart from what was lifted

- Status: accepted
- Date: 2026-07-28

## Context

Assigning a routine was the last piece of the coaching area still faked: the
trainer ticked exercises from a hard-coded list and the choice never left their
own browser (`localStorage`), so the student never saw it. Meanwhile the student
had no place to say "I did Wednesday, but only 92.5 kg of the 100 you asked
for" — and that shortfall is exactly the signal a trainer needs.

## Decision

A **plan item is a prescription, not a record of what happened**: exercise, day,
target sets, reps and load. Whether it was done is read from the student's
`workout_logs` for that user, exercise and day (`plan_items` ⟕ `workout_logs`).

That join is the whole design:

- One truth for "what was lifted". Reporting from the calendar writes an
  ordinary workout log, so assigned work feeds the evolution charts (ADR-0021)
  with no extra bookkeeping, and a session logged from the workout page closes
  the scheduled item just the same.
- **Status is derived, never stored**: `pending` while the day is ahead,
  `missed` once it passed with nothing logged, `done` when the target was met,
  `partial` when the student trained but under the prescribed load or reps.
  Nothing to keep in sync.
- Re-scheduling the same exercise on the same day edits the targets
  (`UNIQUE (student_id, exercise_id, scheduled_on)`), so a trainer correcting a
  weight does not create a second row.

Access control follows the roster, as everywhere in this area: the trainer
endpoints check the student is theirs (404 otherwise, so ids cannot be probed),
and the student endpoints only ever touch items whose `student_id` is the one in
the token.

**Reporting under the target is a first-class outcome, not an error.** The form
opens pre-filled with the target — hitting it is one tap — and the student
changes the number when they fell short.

## The calendar as a week strip, not a grid

Seven columns of exercise cards crowd even on a desktop, and inside the
trainer's panel each column had ~90px, which cannot hold "Press de banca con
barra". The calendar is instead **seven small day buttons plus the selected day
at full width**, with a dot per scheduled exercise (coloured by status) under
each day. The same component then works on a phone, on a tablet and inside a
panel, and the week is still readable at a glance.

## Consequences

- The trainer writes a real routine and sees, per day, what came back: done,
  partial with the weight, or missed.
- The student's calendar is the natural home for "what do I do today", and
  logging from it keeps their own progress and their trainer's charts in step.
- The mockup assignment list, its store and its localStorage key are gone.
- A plan does not repeat itself: scheduling next week means adding the days
  again. Copying a week is the obvious next step, deliberately left out until
  the shape of a plan settles.
- The catalog gained a public search endpoint (`GET /exercises?q=`), which the
  trainer's picker uses and any future picker can reuse.
