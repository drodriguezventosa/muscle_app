"""Coaching endpoints: a trainer's roster and a student's progress sync.

Everything here requires a signed-in user. Trainer-only routes go through
`TrainerUser`, and the student routes only ever touch the caller's own rows:
the user id comes from the token, never from the request body (OWASP A01).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.v1.deps import (
    CurrentUser,
    TrainerUser,
    provide_get_own_progress,
    provide_list_students,
    provide_student_dashboard,
    provide_sync_progress,
)
from app.api.v1.schemas.coaching import (
    ExerciseProgressionRead,
    SeriesPointRead,
    StudentDashboardRead,
    StudentRead,
    SyncProgressRequest,
    SyncProgressResponse,
    WeeklyAdherenceRead,
)
from app.application.dto.coaching import ProgressUpdate, StudentDashboard
from app.application.use_cases.coaching_use_cases import (
    GetOwnProgress,
    GetStudentDashboard,
    ListStudents,
    StudentNotFoundError,
    SyncProgress,
)
from app.core.rate_limit import RATE_LIMIT, limiter
from app.domain.entities.coaching import LoggedSession, Student

router = APIRouter(prefix="/coaching", tags=["coaching"])


def _to_student_read(student: Student) -> StudentRead:
    return StudentRead(
        id=student.id,
        name=student.name,
        goal=student.goal,
        level=student.level,
        age=student.age,
        height_cm=student.height_cm,
        weight_kg=student.weight_kg,
        bmi=student.bmi,
        sessions_last_30d=student.sessions_last_30d,
        last_session_on=student.last_session_on,
    )


def _to_dashboard_read(dashboard: StudentDashboard) -> StudentDashboardRead:
    return StudentDashboardRead(
        student=_to_student_read(dashboard.student),
        body_weight=[SeriesPointRead(on=p.on, value=p.value) for p in dashboard.body_weight],
        strength=[
            ExerciseProgressionRead(
                exercise_id=progression.exercise_id,
                exercise_name=progression.exercise_name,
                points=[SeriesPointRead(on=p.on, value=p.value) for p in progression.points],
                gain_pct=progression.gain_pct,
            )
            for progression in dashboard.strength
        ],
        adherence=[
            WeeklyAdherenceRead(week_start=week.week_start, sessions=week.sessions)
            for week in dashboard.adherence
        ],
        total_sessions=dashboard.total_sessions,
        weight_change_kg=dashboard.weight_change_kg,
    )


@router.get(
    "/students",
    response_model=list[StudentRead],
    summary="Students followed by the signed-in trainer",
)
async def list_students(
    trainer: TrainerUser,
    use_case: Annotated[ListStudents, Depends(provide_list_students)],
) -> list[StudentRead]:
    return [_to_student_read(student) for student in await use_case.execute(trainer.id)]


@router.get(
    "/students/{student_id}",
    response_model=StudentDashboardRead,
    summary="Evolution of one of the trainer's students",
)
async def get_student(
    student_id: int,
    trainer: TrainerUser,
    use_case: Annotated[GetStudentDashboard, Depends(provide_student_dashboard)],
) -> StudentDashboardRead:
    try:
        dashboard = await use_case.execute(trainer.id, student_id)
    except StudentNotFoundError as exc:
        # Also the answer for "exists, but is someone else's student".
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        ) from exc
    return _to_dashboard_read(dashboard)


@router.get(
    "/me/progress",
    response_model=StudentDashboardRead,
    summary="The signed-in user's own evolution",
)
async def my_progress(
    user: CurrentUser,
    use_case: Annotated[GetOwnProgress, Depends(provide_get_own_progress)],
) -> StudentDashboardRead:
    dashboard = await use_case.execute(user.id)
    if dashboard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No progress recorded")
    return _to_dashboard_read(dashboard)


@router.post(
    "/me/progress",
    response_model=SyncProgressResponse,
    summary="Push the progress recorded in the browser",
)
@limiter.limit(RATE_LIMIT)
async def sync_progress(
    request: Request,  # required by slowapi to identify the client
    payload: SyncProgressRequest,
    user: CurrentUser,
    use_case: Annotated[SyncProgress, Depends(provide_sync_progress)],
) -> SyncProgressResponse:
    synced = await use_case.execute(
        user.id,
        ProgressUpdate(
            sessions=tuple(
                LoggedSession(
                    exercise_id=session.exercise_id,
                    logged_on=session.logged_on,
                    weight_kg=session.weight_kg,
                    reps=session.reps,
                    completed=session.completed,
                )
                for session in payload.sessions
            ),
            weight_kg=payload.weight_kg,
            height_cm=payload.height_cm,
            age=payload.age,
            goal=payload.goal,
            level=payload.level,
        ),
    )
    return SyncProgressResponse(synced=synced)
