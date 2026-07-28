# 26. The plan belongs to the trainer-student pair

- Status: accepted
- Date: 2026-07-28

## Context

`plan_items` has always carried both `trainer_id` and `student_id` (ADR-0023),
but every read was keyed by the student alone. With one trainer per student
(ADR-0024) that gap became visible the moment a student switched: the new trainer
inherited the previous one's calendar, the student kept seeing prescriptions from
someone who no longer coaches them, and the plan header credited them to the new
trainer. Three views of the same rows, none of them true.

## Decision

**Reads are keyed by the pair.** A trainer sees the calendar they wrote for that
student; a student sees the calendar of the trainer they have now. Writes already
were: scheduling stamps the trainer, and removing an item requires it to be
theirs — checked on the item, not only on the roster, so two trainers who both
coached the same person can never edit each other's work.

**Reporting follows what is visible.** A prescription from a previous trainer is
no longer the student's to report on: the item is gone from their calendar, so the
report is a 404 like any other item that is not theirs.

**Nothing is deleted on a switch.** The previous trainer's plan stays with that
trainer and comes back if the student hires them again. What was asked, was asked
(ADR-0024) — and the logs are untouched either way, because a session the student
trained is theirs and not the trainer's: history, charts and adherence carry over
to the new trainer intact.

**A new trainer starts from an empty week.** That is the honest state, and the
calendar already says whose turn it is: "Marco Ruiz has not scheduled anything
for this week yet."

## Consequences

- Switching trainer is now a clean handover rather than an inheritance.
- The trainer's calendar is private to them; the student's plan always has exactly
  one author.
- `TrainingPlanRepository.list_for_student` takes the trainer id, so the port
  states the rule instead of leaving it to each caller.
- The guided tour explains this, along with the rest of the coaching area: it is
  built per audience, so a trainer is walked through their students and a student
  through their plan, and no step navigates to a page the visitor cannot open.
