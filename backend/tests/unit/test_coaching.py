"""Unit tests for the coaching use cases, against a fake repository."""

from collections.abc import Sequence
from datetime import date, timedelta

import pytest

from app.application.dto.coaching import ProgressUpdate
from app.application.use_cases.coaching_use_cases import (
    GetOwnProgress,
    GetStudentDashboard,
    ListStudents,
    StudentNotFoundError,
    SyncProgress,
)
from app.domain.entities.coaching import (
    BodyMetric,
    LoggedSession,
    Student,
    StudentDetail,
    WorkoutLog,
)
from app.domain.ports.coaching import CoachingRepository
from app.domain.value_objects.enums import Difficulty, Goal

TODAY = date(2026, 7, 27)  # a Monday-anchored fixed date keeps the weeks stable


def _student(**overrides: object) -> Student:
    defaults: dict[str, object] = {
        "id": 1,
        "name": "Javier M.",
        "goal": Goal.HYPERTROPHY,
        "level": Difficulty.INTERMEDIATE,
        "age": 29,
        "height_cm": 178,
        "weight_kg": 78.0,
        "sessions_last_30d": 10,
        "last_session_on": TODAY,
    }
    return Student(**{**defaults, **overrides})  # type: ignore[arg-type]


def _log(day: date, exercise_id: int = 1, weight: float = 60.0, reps: int = 8) -> WorkoutLog:
    return WorkoutLog(
        logged_on=day,
        exercise_id=exercise_id,
        exercise_name=f"Exercise {exercise_id}",
        weight_kg=weight,
        reps=reps,
        completed=True,
    )


class FakeCoachingRepository(CoachingRepository):
    """In-memory double: records what was written, returns what it was given."""

    def __init__(self, detail: StudentDetail | None = None, roster: list[Student] | None = None):
        self.detail = detail
        self.roster = roster or []
        self.sessions: list[LoggedSession] = []
        self.weights: list[tuple[int, date, float]] = []
        self.profiles: list[dict[str, object]] = []

    async def list_students(self, trainer_id: int) -> list[Student]:
        return self.roster

    async def get_student(self, trainer_id: int, student_id: int) -> StudentDetail | None:
        return self.detail

    async def get_own_detail(self, user_id: int) -> StudentDetail | None:
        return self.detail

    async def upsert_sessions(self, user_id: int, sessions: Sequence[LoggedSession]) -> int:
        self.sessions.extend(sessions)
        return len(sessions)

    async def record_weight(self, user_id: int, measured_on: date, weight_kg: float) -> None:
        self.weights.append((user_id, measured_on, weight_kg))

    async def upsert_profile(
        self,
        user_id: int,
        *,
        age: int | None = None,
        height_cm: int | None = None,
        goal: Goal | None = None,
        level: Difficulty | None = None,
    ) -> None:
        self.profiles.append(
            {"user_id": user_id, "age": age, "height_cm": height_cm, "goal": goal, "level": level}
        )


# -- entities ---------------------------------------------------------------


def test_estimated_1rm_uses_the_epley_formula() -> None:
    # 100 kg x 5 reps -> 100 * (1 + 5/30) = 116.7
    assert _log(TODAY, weight=100, reps=5).estimated_1rm == 116.7


def test_bodyweight_work_has_no_estimated_1rm() -> None:
    assert _log(TODAY, weight=0, reps=12).estimated_1rm == 0.0


def test_bmi_needs_both_height_and_weight() -> None:
    assert _student(height_cm=178, weight_kg=78.0).bmi == 24.6
    assert _student(height_cm=None).bmi is None
    assert _student(weight_kg=None).bmi is None


# -- dashboard --------------------------------------------------------------


async def test_dashboard_keeps_the_best_1rm_of_each_day() -> None:
    detail = StudentDetail(
        student=_student(),
        body_metrics=(),
        # Two sets of the same exercise on the same day: the heavier one wins.
        logs=(_log(TODAY, weight=60, reps=8), _log(TODAY, weight=70, reps=8)),
    )
    dashboard = await GetStudentDashboard(FakeCoachingRepository(detail), TODAY).execute(9, 1)

    assert len(dashboard.strength) == 1
    assert [point.value for point in dashboard.strength[0].points] == [88.7]
    assert dashboard.total_sessions == 1


async def test_dashboard_reports_the_gain_between_first_and_last_point() -> None:
    detail = StudentDetail(
        student=_student(),
        body_metrics=(
            BodyMetric(TODAY - timedelta(weeks=4), 80.0),
            BodyMetric(TODAY, 77.5),
        ),
        logs=(
            _log(TODAY - timedelta(weeks=4), weight=60, reps=8),
            _log(TODAY, weight=75, reps=8),
        ),
    )
    dashboard = await GetStudentDashboard(FakeCoachingRepository(detail), TODAY).execute(9, 1)

    assert dashboard.strength[0].gain_pct == 25.0
    assert dashboard.weight_change_kg == -2.5


async def test_dashboard_adherence_covers_twelve_weeks_and_counts_days_once() -> None:
    detail = StudentDetail(
        student=_student(),
        body_metrics=(),
        # Three exercises on the same day are one session, not three.
        logs=tuple(_log(TODAY, exercise_id=i) for i in (1, 2, 3)),
    )
    dashboard = await GetStudentDashboard(FakeCoachingRepository(detail), TODAY).execute(9, 1)

    assert len(dashboard.adherence) == 12
    assert dashboard.adherence[-1].sessions == 1
    assert sum(week.sessions for week in dashboard.adherence) == 1


async def test_dashboard_plots_at_most_four_exercises() -> None:
    detail = StudentDetail(
        student=_student(),
        body_metrics=(),
        logs=tuple(_log(TODAY, exercise_id=i) for i in range(1, 8)),
    )
    dashboard = await GetStudentDashboard(FakeCoachingRepository(detail), TODAY).execute(9, 1)

    assert len(dashboard.strength) == 4


async def test_a_student_of_another_trainer_is_reported_as_missing() -> None:
    use_case = GetStudentDashboard(FakeCoachingRepository(detail=None), TODAY)
    with pytest.raises(StudentNotFoundError):
        await use_case.execute(trainer_id=9, student_id=1)


async def test_own_progress_is_none_when_there_is_nothing_recorded() -> None:
    assert await GetOwnProgress(FakeCoachingRepository(detail=None), TODAY).execute(1) is None


async def test_the_roster_comes_from_the_repository() -> None:
    repository = FakeCoachingRepository(roster=[_student(), _student(id=2, name="Lucía P.")])
    assert len(await ListStudents(repository).execute(trainer_id=9)) == 2


# -- sync -------------------------------------------------------------------


async def test_sync_writes_sessions_weight_and_profile() -> None:
    repository = FakeCoachingRepository()
    update = ProgressUpdate(
        sessions=(
            LoggedSession(exercise_id=3, logged_on=TODAY, weight_kg=50, reps=10, completed=True),
        ),
        weight_kg=77.4,
        height_cm=178,
        age=29,
        goal=Goal.HYPERTROPHY,
        level=Difficulty.INTERMEDIATE,
    )

    written = await SyncProgress(repository, TODAY).execute(user_id=5, update=update)

    assert written == 1
    assert repository.sessions[0].exercise_id == 3
    assert repository.weights == [(5, TODAY, 77.4)]
    assert repository.profiles[0]["user_id"] == 5


async def test_sync_without_attributes_only_writes_sessions() -> None:
    repository = FakeCoachingRepository()
    update = ProgressUpdate(
        sessions=(
            LoggedSession(exercise_id=3, logged_on=TODAY, weight_kg=50, reps=10, completed=True),
        )
    )

    await SyncProgress(repository, TODAY).execute(user_id=5, update=update)

    # Nothing to merge means nothing is touched: a partial sync must not wipe
    # attributes the student filled in elsewhere.
    assert repository.weights == []
    assert repository.profiles == []


async def test_an_empty_sync_is_a_no_op() -> None:
    repository = FakeCoachingRepository()
    assert await SyncProgress(repository, TODAY).execute(5, ProgressUpdate()) == 0
    assert repository.sessions == []
