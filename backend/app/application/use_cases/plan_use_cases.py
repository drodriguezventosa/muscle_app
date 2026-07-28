"""Use cases for the training calendar.

The trainer schedules exercises for a student; the student sees what is due and
reports what they lifted. Reporting writes an ordinary workout log — the same
rows the dashboard charts read — so an assigned session and a free one are the
same fact, recorded once.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.entities.coaching import LoggedSession
from app.domain.entities.plan import PlanItem, PlanItemStatus
from app.domain.ports.coaching import CoachingRepository
from app.domain.ports.plan import TrainingPlanRepository

# Bound on how much calendar one request may ask for (OWASP A04).
MAX_RANGE_DAYS = 62


class StudentNotAssignedError(Exception):
    """The student is not on this trainer's roster (or does not exist)."""


class PlanItemNotFoundError(Exception):
    """No such scheduled exercise, or it belongs to someone else."""


class UnknownExerciseError(Exception):
    """The exercise is not in the catalog."""


@dataclass(frozen=True, slots=True)
class ScheduledExercise:
    """A plan item with its status already resolved against today."""

    item: PlanItem
    status: PlanItemStatus


def _clamp(start: date, end: date) -> tuple[date, date]:
    """Keep the requested window sane and in order."""
    if end < start:
        start, end = end, start
    return start, min(end, start + timedelta(days=MAX_RANGE_DAYS))


class ListStudentPlan:
    """The calendar of one of the trainer's students."""

    def __init__(
        self,
        plans: TrainingPlanRepository,
        coaching: CoachingRepository,
        today: date | None = None,
    ) -> None:
        self._plans = plans
        self._coaching = coaching
        self._today = today or date.today()

    async def execute(
        self, trainer_id: int, student_id: int, start: date, end: date
    ) -> list[ScheduledExercise]:
        # Deny by default: the roster is what makes this student "theirs".
        if await self._coaching.get_student(trainer_id, student_id) is None:
            raise StudentNotAssignedError
        start, end = _clamp(start, end)
        items = await self._plans.list_for_student(student_id, start, end)
        return [ScheduledExercise(item, item.status(self._today)) for item in items]


class ListOwnPlan:
    """The signed-in student's own calendar."""

    def __init__(self, plans: TrainingPlanRepository, today: date | None = None) -> None:
        self._plans = plans
        self._today = today or date.today()

    async def execute(self, student_id: int, start: date, end: date) -> list[ScheduledExercise]:
        start, end = _clamp(start, end)
        items = await self._plans.list_for_student(student_id, start, end)
        return [ScheduledExercise(item, item.status(self._today)) for item in items]


class ScheduleExercise:
    """Put an exercise on a student's calendar (or edit the targets on that day)."""

    def __init__(self, plans: TrainingPlanRepository, coaching: CoachingRepository) -> None:
        self._plans = plans
        self._coaching = coaching

    async def execute(
        self,
        *,
        trainer_id: int,
        student_id: int,
        exercise_id: int,
        scheduled_on: date,
        target_sets: int,
        target_reps: int,
        target_weight_kg: float | None,
        notes: str | None,
    ) -> PlanItem:
        if await self._coaching.get_student(trainer_id, student_id) is None:
            raise StudentNotAssignedError
        item = await self._plans.add(
            trainer_id=trainer_id,
            student_id=student_id,
            exercise_id=exercise_id,
            scheduled_on=scheduled_on,
            target_sets=target_sets,
            target_reps=target_reps,
            target_weight_kg=target_weight_kg,
            notes=notes,
        )
        if item is None:
            raise UnknownExerciseError
        return item


class UnscheduleExercise:
    """Remove a scheduled exercise, if it is one of this trainer's students'."""

    def __init__(self, plans: TrainingPlanRepository, coaching: CoachingRepository) -> None:
        self._plans = plans
        self._coaching = coaching

    async def execute(self, trainer_id: int, item_id: int) -> None:
        item = await self._plans.get(item_id)
        # Checked against the roster rather than "who created it", so a trainer
        # can tidy up a plan they inherited — but never another trainer's.
        if item is None or await self._coaching.get_student(trainer_id, item.student_id) is None:
            raise PlanItemNotFoundError
        await self._plans.remove(item_id)


class ReportPlanItem:
    """The student reports what they lifted for a scheduled exercise.

    Writes a normal workout log, so the trainer's charts and the student's own
    progress see it without any extra bookkeeping. Reporting less than the
    target is expected, not an error: the status turns "partial" and the
    trainer can see where the plan was too ambitious — whether the student fell
    short on the load, the repetitions or the number of sets.
    """

    def __init__(self, plans: TrainingPlanRepository, coaching: CoachingRepository) -> None:
        self._plans = plans
        self._coaching = coaching

    async def execute(
        self,
        *,
        student_id: int,
        item_id: int,
        weight_kg: float,
        reps: int,
        sets: int,
    ) -> PlanItem:
        item = await self._plans.get(item_id)
        if item is None or item.student_id != student_id:
            raise PlanItemNotFoundError
        # Whether the plan was met is arithmetic on the three numbers, so the
        # server works it out rather than trusting a flag from the client.
        completed = sets >= item.target_sets and reps >= item.target_reps
        await self._coaching.upsert_sessions(
            student_id,
            [
                LoggedSession(
                    exercise_id=item.exercise_id,
                    logged_on=item.scheduled_on,
                    weight_kg=weight_kg,
                    reps=reps,
                    sets=sets,
                    completed=completed,
                )
            ],
        )
        refreshed = await self._plans.get(item_id)
        # The row cannot vanish between two statements of the same request, but
        # the type says it might; fall back to what we already had.
        return refreshed or item
