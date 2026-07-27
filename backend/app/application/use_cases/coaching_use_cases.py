"""Use cases for the coaching area: rosters, student evolution and progress sync.

The raw history lives in the repository; turning it into the series the
dashboard draws (strength progression, body weight, weekly adherence) happens
here, so the frontend only renders what it is given.
"""

from collections import defaultdict
from datetime import date, timedelta

from app.application.dto.coaching import (
    ExerciseProgression,
    ProgressUpdate,
    SeriesPoint,
    StudentDashboard,
    WeeklyAdherence,
)
from app.domain.entities.coaching import Student, StudentDetail, WorkoutLog
from app.domain.ports.coaching import CoachingRepository

# Exercises plotted per student: enough to show a trend, few enough to read.
_MAX_TRACKED_EXERCISES = 4
# Weeks of adherence shown, matching the seeded history.
_ADHERENCE_WEEKS = 12


class StudentNotFoundError(Exception):
    """No such student, or not one of this trainer's.

    One error for both cases on purpose: a trainer must not be able to find out
    which student ids exist elsewhere (OWASP A01).
    """


def _monday(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _strength_series(logs: tuple[WorkoutLog, ...]) -> tuple[ExerciseProgression, ...]:
    """Best estimated 1RM per exercise and day, for the most trained exercises."""
    by_exercise: dict[int, dict[date, float]] = defaultdict(dict)
    names: dict[int, str] = {}
    for log in logs:
        one_rm = log.estimated_1rm
        if one_rm <= 0:  # bodyweight work has no 1RM to plot
            continue
        names[log.exercise_id] = log.exercise_name
        best_of_day = by_exercise[log.exercise_id]
        best_of_day[log.logged_on] = max(best_of_day.get(log.logged_on, 0.0), one_rm)

    progressions = [
        ExerciseProgression(
            exercise_id=exercise_id,
            exercise_name=names[exercise_id],
            points=tuple(SeriesPoint(on=day, value=value) for day, value in sorted(days.items())),
        )
        for exercise_id, days in by_exercise.items()
    ]
    # Most sessions first: those are the ones with a story to tell.
    progressions.sort(key=lambda p: (-len(p.points), p.exercise_name))
    return tuple(progressions[:_MAX_TRACKED_EXERCISES])


def _adherence_series(logs: tuple[WorkoutLog, ...], today: date) -> tuple[WeeklyAdherence, ...]:
    """Distinct training days per week over the last `_ADHERENCE_WEEKS` weeks."""
    first_week = _monday(today) - timedelta(weeks=_ADHERENCE_WEEKS - 1)
    days_per_week: dict[date, set[date]] = {
        first_week + timedelta(weeks=i): set() for i in range(_ADHERENCE_WEEKS)
    }
    for log in logs:
        week = _monday(log.logged_on)
        if week in days_per_week:
            days_per_week[week].add(log.logged_on)
    return tuple(
        WeeklyAdherence(week_start=week, sessions=len(days))
        for week, days in sorted(days_per_week.items())
    )


def _to_dashboard(detail: StudentDetail, today: date) -> StudentDashboard:
    return StudentDashboard(
        student=detail.student,
        body_weight=tuple(
            SeriesPoint(on=metric.measured_on, value=metric.weight_kg)
            for metric in detail.body_metrics
        ),
        strength=_strength_series(detail.logs),
        adherence=_adherence_series(detail.logs, today),
        total_sessions=len({log.logged_on for log in detail.logs}),
    )


class ListStudents:
    """The roster a trainer sees when they open their area."""

    def __init__(self, repository: CoachingRepository) -> None:
        self._repository = repository

    async def execute(self, trainer_id: int) -> list[Student]:
        return await self._repository.list_students(trainer_id)


class GetStudentDashboard:
    """One student's evolution, for the trainer that follows them."""

    def __init__(self, repository: CoachingRepository, today: date | None = None) -> None:
        self._repository = repository
        self._today = today or date.today()

    async def execute(self, trainer_id: int, student_id: int) -> StudentDashboard:
        detail = await self._repository.get_student(trainer_id, student_id)
        if detail is None:
            raise StudentNotFoundError
        return _to_dashboard(detail, self._today)


class GetOwnProgress:
    """The signed-in student's own evolution, same shape as the trainer's view."""

    def __init__(self, repository: CoachingRepository, today: date | None = None) -> None:
        self._repository = repository
        self._today = today or date.today()

    async def execute(self, user_id: int) -> StudentDashboard | None:
        detail = await self._repository.get_own_detail(user_id)
        return _to_dashboard(detail, self._today) if detail else None


class SyncProgress:
    """Mirror what the browser recorded onto the server, for the trainer to see.

    The workout logger stays offline-first (ADR-0011): localStorage remains the
    working copy, and this only pushes it up when the user is signed in. It
    writes to the caller's own rows only — the user id comes from the token,
    never from the payload.
    """

    def __init__(self, repository: CoachingRepository, today: date | None = None) -> None:
        self._repository = repository
        self._today = today or date.today()

    async def execute(self, user_id: int, update: ProgressUpdate) -> int:
        written = await self._repository.upsert_sessions(user_id, update.sessions)
        if update.weight_kg:
            await self._repository.record_weight(user_id, self._today, update.weight_kg)
        if update.has_profile_data:
            await self._repository.upsert_profile(
                user_id,
                age=update.age,
                height_cm=update.height_cm,
                goal=update.goal,
                level=update.level,
            )
        return written
