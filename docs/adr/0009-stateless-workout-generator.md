# 9. Stateless workout generator (no persistence; attributes via POST body)

- Status: accepted
- Date: 2026-07-14

## Context

Users want a basic routine tailored to a goal (fat loss / hypertrophy / strength)
and minimal attributes (level, height, weight, where they train). The MVP has no
login, so there is no account to attach routines to.

## Decision

A `GenerateWorkout` use case builds the routine on the fly from the existing
exercise catalog: the goal selects the set/rep/rest scheme and the target muscles;
the experience level bounds exercise difficulty; height/weight only compute the BMI
shown as context. Nothing is persisted and no new tables are added. Attributes are
sent in the **POST body**, not the query string, to keep personal data out of URLs.

## Consequences

- No stored user data / PII; reuses the catalog and the muscle/exercise repositories.
- Height/weight do not reshape the routine (they inform BMI only) — communicated to users.
- Beginner + strength currently yields machine/isolation picks (compound barbell lifts
  are intermediate+); acceptable for a "basic" generator, revisit if needed.
