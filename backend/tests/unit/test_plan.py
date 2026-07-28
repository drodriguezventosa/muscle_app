"""Unit tests for the training calendar."""

from collections.abc import Sequence
from datetime import date, timedelta

import pytest

from app.application.use_cases.plan_use_cases import (
    ListOwnPlan,
    ListStudentPlan,
    PlanItemNotFoundError,
    ReportPlanItem,
    ScheduleExercise,
    StudentNotAssignedError,
    UnknownExerciseError,
    UnscheduleExercise,
)
from app.domain.entities.coaching import LoggedSession, Student, StudentDetail
from app.domain.entities.plan import PlanItem, PlanItemStatus
from app.domain.ports.plan import TrainingPlanRepository
from app.domain.value_objects.enums import Difficulty, Goal
from tests.unit.test_coaching import FakeCoachingRepository

TODAY = date(2026, 7, 27)


def _item(**overrides: object) -> PlanItem:
    defaults: dict[str, object] = {
        "id": 1,
        "trainer_id": 9,
        "student_id": 2,
        "exercise_id": 5,
        "exercise_name": "Sentadilla con barra",
        "scheduled_on": TODAY,
        "target_sets": 3,
        "target_reps": 8,
        "target_weight_kg": 100.0,
        "notes": None,
    }
    return PlanItem(**{**defaults, **overrides})  # type: ignore[arg-type]


def _detail() -> StudentDetail:
    student = Student(
        id=2,
        name="Javier M.",
        goal=Goal.HYPERTROPHY,
        level=Difficulty.INTERMEDIATE,
        age=29,
        height_cm=178,
        weight_kg=78.0,
        sessions_last_30d=10,
        last_session_on=TODAY,
    )
    return StudentDetail(student=student, body_metrics=(), logs=())


class FakePlanRepository(TrainingPlanRepository):
    def __init__(self, items: list[PlanItem] | None = None, catalog: bool = True) -> None:
        self.items = items or []
        self.catalog = catalog
        self.removed: list[int] = []

    async def list_for_student(self, student_id: int, start: date, end: date) -> list[PlanItem]:
        return [
            item
            for item in self.items
            if item.student_id == student_id and start <= item.scheduled_on <= end
        ]

    async def get(self, item_id: int) -> PlanItem | None:
        return next((item for item in self.items if item.id == item_id), None)

    async def add(self, **kwargs: object) -> PlanItem | None:
        if not self.catalog:
            return None
        item = _item(**kwargs, id=99)
        self.items.append(item)
        return item

    async def remove(self, item_id: int) -> bool:
        self.removed.append(item_id)
        return True


# -- status ------------------------------------------------------------------


def test_a_future_day_with_nothing_logged_is_pending() -> None:
    item = _item(scheduled_on=TODAY + timedelta(days=2))
    assert item.status(TODAY) is PlanItemStatus.PENDING


def test_a_past_day_with_nothing_logged_is_missed() -> None:
    item = _item(scheduled_on=TODAY - timedelta(days=1))
    assert item.status(TODAY) is PlanItemStatus.MISSED


def test_hitting_the_target_is_done() -> None:
    item = _item(done_weight_kg=100.0, done_reps=8, done_completed=True)
    assert item.status(TODAY) is PlanItemStatus.DONE


def test_lifting_more_than_the_target_is_still_done() -> None:
    item = _item(done_weight_kg=105.0, done_reps=8, done_completed=True)
    assert item.status(TODAY) is PlanItemStatus.DONE


def test_falling_short_of_the_target_weight_is_partial() -> None:
    # The student trained, just not with what was asked for.
    item = _item(done_weight_kg=90.0, done_reps=8, done_completed=True)
    assert item.status(TODAY) is PlanItemStatus.PARTIAL


def test_falling_short_of_the_target_reps_is_partial() -> None:
    item = _item(done_weight_kg=100.0, done_reps=5, done_completed=True)
    assert item.status(TODAY) is PlanItemStatus.PARTIAL


def test_falling_short_of_the_target_sets_is_partial() -> None:
    item = _item(done_weight_kg=100.0, done_reps=8, done_sets=2, done_completed=True)
    assert item.status(TODAY) is PlanItemStatus.PARTIAL


def test_not_finishing_the_sets_is_partial() -> None:
    item = _item(done_weight_kg=100.0, done_reps=8, done_completed=False)
    assert item.status(TODAY) is PlanItemStatus.PARTIAL


def test_an_open_target_is_done_with_whatever_was_lifted() -> None:
    item = _item(target_weight_kg=None, done_weight_kg=0.0, done_reps=8, done_completed=True)
    assert item.status(TODAY) is PlanItemStatus.DONE


# -- reading the calendar ----------------------------------------------------


async def test_a_trainer_only_reads_their_own_students_calendar() -> None:
    use_case = ListStudentPlan(FakePlanRepository(), FakeCoachingRepository(detail=None), TODAY)
    with pytest.raises(StudentNotAssignedError):
        await use_case.execute(9, 2, TODAY, TODAY)


async def test_the_calendar_comes_back_with_the_status_resolved() -> None:
    plans = FakePlanRepository([_item(), _item(id=2, scheduled_on=TODAY - timedelta(days=3))])
    use_case = ListStudentPlan(plans, FakeCoachingRepository(detail=_detail()), TODAY)

    entries = await use_case.execute(9, 2, TODAY - timedelta(days=7), TODAY)

    assert [entry.status for entry in entries] == [
        PlanItemStatus.PENDING,
        PlanItemStatus.MISSED,
    ]


async def test_a_student_reads_their_own_calendar_without_a_roster_check() -> None:
    plans = FakePlanRepository([_item()])
    entries = await ListOwnPlan(plans, TODAY).execute(2, TODAY, TODAY)
    assert len(entries) == 1


async def test_an_over_long_window_is_clamped_not_rejected() -> None:
    plans = FakePlanRepository([_item(id=7, scheduled_on=TODAY + timedelta(days=200))])
    entries = await ListOwnPlan(plans, TODAY).execute(2, TODAY, TODAY + timedelta(days=365))
    # The far-future item falls outside the clamped window.
    assert entries == []


# -- scheduling --------------------------------------------------------------


async def test_scheduling_requires_the_student_to_be_on_the_roster() -> None:
    use_case = ScheduleExercise(FakePlanRepository(), FakeCoachingRepository(detail=None))
    with pytest.raises(StudentNotAssignedError):
        await use_case.execute(
            trainer_id=9,
            student_id=2,
            exercise_id=5,
            scheduled_on=TODAY,
            target_sets=3,
            target_reps=8,
            target_weight_kg=100,
            notes=None,
        )


async def test_scheduling_an_unknown_exercise_is_rejected() -> None:
    use_case = ScheduleExercise(
        FakePlanRepository(catalog=False), FakeCoachingRepository(detail=_detail())
    )
    with pytest.raises(UnknownExerciseError):
        await use_case.execute(
            trainer_id=9,
            student_id=2,
            exercise_id=404,
            scheduled_on=TODAY,
            target_sets=3,
            target_reps=8,
            target_weight_kg=None,
            notes=None,
        )


async def test_removing_someone_elses_item_is_reported_as_missing() -> None:
    plans = FakePlanRepository([_item()])
    use_case = UnscheduleExercise(plans, FakeCoachingRepository(detail=None))

    with pytest.raises(PlanItemNotFoundError):
        await use_case.execute(trainer_id=7, item_id=1)
    assert plans.removed == []


# -- reporting ---------------------------------------------------------------


class RecordingCoaching(FakeCoachingRepository):
    """Captures the sessions written when a student reports a scheduled lift."""

    def __init__(self) -> None:
        super().__init__(detail=_detail())
        self.written: list[LoggedSession] = []

    async def upsert_sessions(self, user_id: int, sessions: Sequence[LoggedSession]) -> int:
        self.written.extend(sessions)
        return len(sessions)


async def test_reporting_writes_an_ordinary_workout_log() -> None:
    plans = FakePlanRepository([_item()])
    coaching = RecordingCoaching()

    await ReportPlanItem(plans, coaching).execute(
        student_id=2, item_id=1, weight_kg=92.5, reps=8, sets=3
    )

    # One log, on the scheduled day and exercise: the charts need nothing extra.
    assert len(coaching.written) == 1
    written = coaching.written[0]
    assert (written.exercise_id, written.logged_on, written.weight_kg) == (5, TODAY, 92.5)
    assert (written.reps, written.sets) == (8, 3)
    # Three of three sets at the target reps: the server calls that complete.
    assert written.completed is True


async def test_stopping_short_of_the_sets_is_not_completed() -> None:
    plans = FakePlanRepository([_item()])
    coaching = RecordingCoaching()

    await ReportPlanItem(plans, coaching).execute(
        student_id=2, item_id=1, weight_kg=100, reps=8, sets=1
    )

    # The flag is derived from the numbers, never taken from the client.
    assert coaching.written[0].completed is False


async def test_a_student_cannot_report_another_students_item() -> None:
    plans = FakePlanRepository([_item(student_id=3)])
    coaching = RecordingCoaching()

    with pytest.raises(PlanItemNotFoundError):
        await ReportPlanItem(plans, coaching).execute(
            student_id=2, item_id=1, weight_kg=90, reps=8, sets=3
        )
    assert coaching.written == []
