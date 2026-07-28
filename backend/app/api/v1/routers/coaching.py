"""Coaching endpoints: a trainer's roster and a student's progress sync.

Everything here requires a signed-in user. Trainer-only routes go through
`TrainerUser`, and the student routes only ever touch the caller's own rows:
the user id comes from the token, never from the request body (OWASP A01).
"""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.v1.deps import (
    CurrentUser,
    TrainerUser,
    provide_cancel_trainer,
    provide_get_own_progress,
    provide_hire_trainer,
    provide_list_own_plan,
    provide_list_student_plan,
    provide_list_students,
    provide_list_trainers,
    provide_my_trainer,
    provide_report_plan_item,
    provide_schedule_exercise,
    provide_student_dashboard,
    provide_sync_progress,
    provide_unschedule_exercise,
)
from app.api.v1.schemas.coaching import (
    ExerciseProgressionRead,
    HireTrainerRequest,
    SeriesPointRead,
    StudentDashboardRead,
    StudentRead,
    SyncProgressRequest,
    SyncProgressResponse,
    TrainerRead,
    WeeklyAdherenceRead,
)
from app.api.v1.schemas.plan import (
    PlanItemRead,
    ReportPlanItemRequest,
    ScheduleExerciseRequest,
)
from app.application.dto.coaching import ProgressUpdate, StudentDashboard
from app.application.use_cases.coaching_use_cases import (
    CancelTrainer,
    GetMyTrainer,
    GetOwnProgress,
    GetStudentDashboard,
    HireTrainer,
    ListStudents,
    ListTrainers,
    StudentNotFoundError,
    SyncProgress,
    TrainerNotFoundError,
)
from app.application.use_cases.plan_use_cases import (
    ListOwnPlan,
    ListStudentPlan,
    PlanItemNotFoundError,
    ReportPlanItem,
    ScheduledExercise,
    ScheduleExercise,
    StudentNotAssignedError,
    UnknownExerciseError,
    UnscheduleExercise,
)
from app.core.rate_limit import RATE_LIMIT, limiter
from app.domain.entities.coaching import LoggedSession, Student, Trainer

router = APIRouter(prefix="/coaching", tags=["coaching"])

# A week either side of today, which is what the calendar opens on.
_DEFAULT_RANGE_DAYS = 7


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


def _to_trainer_read(trainer: Trainer) -> TrainerRead:
    return TrainerRead(
        id=trainer.id,
        name=trainer.name,
        specialty=trainer.specialty,
        rating=trainer.rating,
        price_per_month=trainer.price_per_month,
        bio=trainer.bio,
        students=trainer.students,
    )


@router.get(
    "/trainers",
    response_model=list[TrainerRead],
    summary="Trainers a student can hire (public: browsing needs no account)",
)
async def list_trainers(
    use_case: Annotated[ListTrainers, Depends(provide_list_trainers)],
) -> list[TrainerRead]:
    return [_to_trainer_read(trainer) for trainer in await use_case.execute()]


@router.get(
    "/me/trainer",
    response_model=TrainerRead | None,
    summary="The trainer the signed-in student hired, if any",
)
async def my_trainer(
    user: CurrentUser,
    use_case: Annotated[GetMyTrainer, Depends(provide_my_trainer)],
) -> TrainerRead | None:
    trainer = await use_case.execute(user.id)
    return _to_trainer_read(trainer) if trainer else None


@router.put(
    "/me/trainer",
    response_model=TrainerRead,
    summary="Hire a trainer (replaces the current one: a student has at most one)",
)
@limiter.limit(RATE_LIMIT)
async def hire_trainer(
    request: Request,  # required by slowapi to identify the client
    payload: HireTrainerRequest,
    user: CurrentUser,
    use_case: Annotated[HireTrainer, Depends(provide_hire_trainer)],
) -> TrainerRead:
    try:
        trainer = await use_case.execute(user.id, payload.trainer_id)
    except TrainerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trainer not found"
        ) from exc
    return _to_trainer_read(trainer)


@router.delete(
    "/me/trainer",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Stop working with the current trainer",
)
async def cancel_trainer(
    user: CurrentUser,
    use_case: Annotated[CancelTrainer, Depends(provide_cancel_trainer)],
) -> None:
    await use_case.execute(user.id)


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
                    sets=session.sets,
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


def _to_plan_read(scheduled: ScheduledExercise) -> PlanItemRead:
    item = scheduled.item
    return PlanItemRead(
        id=item.id,
        exercise_id=item.exercise_id,
        exercise_name=item.exercise_name,
        scheduled_on=item.scheduled_on,
        target_sets=item.target_sets,
        target_reps=item.target_reps,
        target_weight_kg=item.target_weight_kg,
        notes=item.notes,
        done_weight_kg=item.done_weight_kg,
        done_reps=item.done_reps,
        done_sets=item.done_sets,
        status=scheduled.status,
    )


def _range(start: date | None, end: date | None, today: date | None = None) -> tuple[date, date]:
    """Default to the week around today when the client sends no window."""
    anchor = today or date.today()
    return (
        start or anchor - timedelta(days=_DEFAULT_RANGE_DAYS),
        end or anchor + timedelta(days=_DEFAULT_RANGE_DAYS),
    )


@router.get(
    "/students/{student_id}/plan",
    response_model=list[PlanItemRead],
    summary="Training calendar of one of the trainer's students",
)
async def student_plan(
    student_id: int,
    trainer: TrainerUser,
    use_case: Annotated[ListStudentPlan, Depends(provide_list_student_plan)],
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
) -> list[PlanItemRead]:
    window = _range(start, end)
    try:
        scheduled = await use_case.execute(trainer.id, student_id, *window)
    except StudentNotAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        ) from exc
    return [_to_plan_read(entry) for entry in scheduled]


@router.post(
    "/students/{student_id}/plan",
    response_model=PlanItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule an exercise for a student (or edit that day's targets)",
)
@limiter.limit(RATE_LIMIT)
async def schedule_exercise(
    request: Request,  # required by slowapi to identify the client
    student_id: int,
    payload: ScheduleExerciseRequest,
    trainer: TrainerUser,
    use_case: Annotated[ScheduleExercise, Depends(provide_schedule_exercise)],
) -> PlanItemRead:
    try:
        item = await use_case.execute(
            trainer_id=trainer.id,
            student_id=student_id,
            exercise_id=payload.exercise_id,
            scheduled_on=payload.scheduled_on,
            target_sets=payload.target_sets,
            target_reps=payload.target_reps,
            target_weight_kg=payload.target_weight_kg,
            notes=payload.notes,
        )
    except StudentNotAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        ) from exc
    except UnknownExerciseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown exercise"
        ) from exc
    return _to_plan_read(ScheduledExercise(item, item.status(date.today())))


@router.delete(
    "/plan/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a scheduled exercise",
)
async def unschedule_exercise(
    item_id: int,
    trainer: TrainerUser,
    use_case: Annotated[UnscheduleExercise, Depends(provide_unschedule_exercise)],
) -> None:
    try:
        await use_case.execute(trainer.id, item_id)
    except PlanItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled exercise not found"
        ) from exc


@router.get(
    "/me/plan",
    response_model=list[PlanItemRead],
    summary="The signed-in student's training calendar",
)
async def my_plan(
    user: CurrentUser,
    use_case: Annotated[ListOwnPlan, Depends(provide_list_own_plan)],
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
) -> list[PlanItemRead]:
    scheduled = await use_case.execute(user.id, *_range(start, end))
    return [_to_plan_read(entry) for entry in scheduled]


@router.post(
    "/me/plan/{item_id}/report",
    response_model=PlanItemRead,
    summary="Report what was lifted for a scheduled exercise",
)
@limiter.limit(RATE_LIMIT)
async def report_plan_item(
    request: Request,  # required by slowapi to identify the client
    item_id: int,
    payload: ReportPlanItemRequest,
    user: CurrentUser,
    use_case: Annotated[ReportPlanItem, Depends(provide_report_plan_item)],
) -> PlanItemRead:
    try:
        item = await use_case.execute(
            student_id=user.id,
            item_id=item_id,
            weight_kg=payload.weight_kg,
            reps=payload.reps,
            sets=payload.sets,
        )
    except PlanItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled exercise not found"
        ) from exc
    return _to_plan_read(ScheduledExercise(item, item.status(date.today())))
