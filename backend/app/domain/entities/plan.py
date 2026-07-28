"""The training plan: what a trainer schedules for a student, day by day.

A plan item is a *prescription*. Whether it happened is not stored here — it is
read from the student's workout log for that exercise and day, so there is one
source of truth for "what was lifted" and the dashboard charts pick up assigned
work automatically.
"""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class PlanItemStatus(StrEnum):
    """How a scheduled exercise stands today."""

    #: Scheduled for today or later, nothing logged yet.
    PENDING = "pending"
    #: Logged, hitting the target.
    DONE = "done"
    #: Logged, but short of the target weight or reps.
    PARTIAL = "partial"
    #: The day passed with nothing logged.
    MISSED = "missed"


@dataclass(frozen=True)
class PlanItem:
    """One exercise scheduled for one day, with whatever the student logged."""

    id: int
    trainer_id: int
    student_id: int
    exercise_id: int
    exercise_name: str
    scheduled_on: date
    target_sets: int
    target_reps: int
    #: None means "no target weight" — bodyweight work, or the trainer left it open.
    target_weight_kg: float | None
    notes: str | None
    #: What the student actually logged that day, if anything.
    done_weight_kg: float | None = None
    done_reps: int | None = None
    done_sets: int | None = None
    done_completed: bool | None = None

    @property
    def is_logged(self) -> bool:
        return self.done_completed is not None

    def status(self, today: date) -> PlanItemStatus:
        """Resolve the status against the calendar."""
        if not self.is_logged:
            return PlanItemStatus.MISSED if self.scheduled_on < today else PlanItemStatus.PENDING
        if not self.done_completed:
            return PlanItemStatus.PARTIAL
        # Logged as completed, but under the prescribed load is still partial:
        # the student did the work, not the work that was asked for.
        short_on_weight = (
            self.target_weight_kg is not None
            and self.done_weight_kg is not None
            and self.done_weight_kg + 0.01 < self.target_weight_kg
        )
        short_on_reps = self.done_reps is not None and self.done_reps < self.target_reps
        short_on_sets = self.done_sets is not None and self.done_sets < self.target_sets
        short = short_on_weight or short_on_reps or short_on_sets
        return PlanItemStatus.PARTIAL if short else PlanItemStatus.DONE
