"""SQLAlchemy adapter for the coaching area."""

from collections.abc import Iterable, Sequence
from datetime import date, timedelta

from sqlalchemy import Select, case, delete, distinct, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.coaching import (
    BodyMetric,
    LoggedSession,
    Student,
    StudentDetail,
    Trainer,
    WorkoutLog,
)
from app.domain.ports.coaching import CoachingRepository
from app.domain.value_objects.enums import Difficulty, Goal, UserRole
from app.infrastructure.persistence.models.coaching import (
    BodyMetricModel,
    StudentProfileModel,
    TrainerProfileModel,
    TrainerStudentModel,
    WorkoutLogModel,
)
from app.infrastructure.persistence.models.exercise import ExerciseModel
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.repositories.localize import pick

# Window used for the "is this student training regularly?" number on the roster.
_ACTIVITY_WINDOW_DAYS = 30


class SqlAlchemyCoachingRepository(CoachingRepository):
    def __init__(
        self, session: AsyncSession, locale: str = "es", today: date | None = None
    ) -> None:
        self._session = session
        self._locale = locale
        # Injectable so tests do not depend on the wall clock.
        self._today = today or date.today()

    # -- reads ---------------------------------------------------------------

    async def list_students(self, trainer_id: int) -> list[Student]:
        rows = (
            await self._session.execute(
                self._profile_query()
                .join(TrainerStudentModel, TrainerStudentModel.student_id == UserModel.id)
                .where(TrainerStudentModel.trainer_id == trainer_id)
                .order_by(UserModel.name)
            )
        ).all()
        ids = [row.UserModel.id for row in rows]
        activity = await self._activity(ids)
        weights = await self._latest_weights(ids)
        return [
            self._to_student(row.UserModel, row.StudentProfileModel, activity, weights)
            for row in rows
        ]

    async def get_student(self, trainer_id: int, student_id: int) -> StudentDetail | None:
        linked = await self._session.scalar(
            select(TrainerStudentModel.id).where(
                TrainerStudentModel.trainer_id == trainer_id,
                TrainerStudentModel.student_id == student_id,
            )
        )
        # Not on the roster is reported exactly like "does not exist", so the
        # endpoint cannot be used to discover other trainers' students.
        return await self._detail(student_id) if linked else None

    async def get_own_detail(self, user_id: int) -> StudentDetail | None:
        return await self._detail(user_id)

    async def list_trainers(self) -> list[Trainer]:
        # The student count comes from the roster, so a trainer's load is real
        # rather than decorative.
        counts = (
            select(TrainerStudentModel.trainer_id, func.count().label("students"))
            .group_by(TrainerStudentModel.trainer_id)
            .subquery()
        )
        rows = await self._session.execute(
            select(UserModel, TrainerProfileModel, func.coalesce(counts.c.students, 0))
            .join(TrainerProfileModel, TrainerProfileModel.user_id == UserModel.id)
            .outerjoin(counts, counts.c.trainer_id == UserModel.id)
            .where(UserModel.role == UserRole.TRAINER)
            .order_by(TrainerProfileModel.rating.desc(), UserModel.name)
        )
        return [self._to_trainer(user, profile, students) for user, profile, students in rows]

    async def get_trainer_of(self, student_id: int) -> Trainer | None:
        counts = (
            select(TrainerStudentModel.trainer_id, func.count().label("students"))
            .group_by(TrainerStudentModel.trainer_id)
            .subquery()
        )
        row = (
            await self._session.execute(
                select(UserModel, TrainerProfileModel, func.coalesce(counts.c.students, 0))
                .join(TrainerStudentModel, TrainerStudentModel.trainer_id == UserModel.id)
                .join(TrainerProfileModel, TrainerProfileModel.user_id == UserModel.id)
                .outerjoin(counts, counts.c.trainer_id == UserModel.id)
                .where(TrainerStudentModel.student_id == student_id)
                # A student has one trainer, so this is the only row — unless a
                # database still carries a second link from the switching bug, in
                # which case the most recent one is the answer and not a 500.
                .order_by(TrainerStudentModel.id.desc())
                .limit(1)
            )
        ).one_or_none()
        return self._to_trainer(*row) if row else None

    # -- writes --------------------------------------------------------------

    async def assign_trainer(self, student_id: int, trainer_id: int) -> Trainer | None:
        is_trainer = await self._session.scalar(
            select(UserModel.id).where(
                UserModel.id == trainer_id, UserModel.role == UserRole.TRAINER
            )
        )
        if is_trainer is None:
            return None
        # One trainer per student, enforced here rather than left to the unique
        # constraint. Relying on the constraint alone made switching trainers
        # fail on the deployed database, where the older shape of the constraint
        # was still in place (`create_all` never alters an existing table): the
        # new pair did not conflict, so the student ended up with two links and
        # the read below raised. Clearing the other links first holds the rule on
        # either shape, and repairs a row pair left behind by that bug.
        await self._session.execute(
            delete(TrainerStudentModel).where(
                TrainerStudentModel.student_id == student_id,
                TrainerStudentModel.trainer_id != trainer_id,
            )
        )
        # No conflict target: the one that exists depends on the deployment.
        await self._session.execute(
            pg_insert(TrainerStudentModel)
            .values(trainer_id=trainer_id, student_id=student_id)
            .on_conflict_do_nothing()
        )
        await self._session.commit()
        return await self.get_trainer_of(student_id)

    async def unassign_trainer(self, student_id: int) -> None:
        await self._session.execute(
            delete(TrainerStudentModel).where(TrainerStudentModel.student_id == student_id)
        )
        await self._session.commit()

    async def upsert_sessions(self, user_id: int, sessions: Sequence[LoggedSession]) -> int:
        if not sessions:
            return 0
        # Last one wins within the payload itself: ON CONFLICT cannot resolve two
        # rows of the same statement that collide with each other.
        deduped = {(s.exercise_id, s.logged_on): s for s in sessions}
        # Ignore ids that are not in the catalog instead of failing the whole
        # sync on a stale browser entry.
        known = set(
            (
                await self._session.scalars(
                    select(ExerciseModel.id).where(
                        ExerciseModel.id.in_({s.exercise_id for s in deduped.values()})
                    )
                )
            ).all()
        )
        values = [
            {
                "user_id": user_id,
                "exercise_id": s.exercise_id,
                "logged_on": s.logged_on,
                "weight_kg": s.weight_kg,
                "reps": s.reps,
                "sets": s.sets,
                "completed": s.completed,
            }
            for s in deduped.values()
            if s.exercise_id in known
        ]
        if not values:
            return 0
        statement = pg_insert(WorkoutLogModel).values(values)
        await self._session.execute(
            statement.on_conflict_do_update(
                constraint="uq_workout_log_day",
                set_={
                    "weight_kg": statement.excluded.weight_kg,
                    "reps": statement.excluded.reps,
                    "sets": statement.excluded.sets,
                    "completed": statement.excluded.completed,
                },
            )
        )
        await self._session.commit()
        return len(values)

    async def record_weight(self, user_id: int, measured_on: date, weight_kg: float) -> None:
        statement = pg_insert(BodyMetricModel).values(
            user_id=user_id, measured_on=measured_on, weight_kg=weight_kg
        )
        await self._session.execute(
            statement.on_conflict_do_update(
                constraint="uq_body_metric_day",
                set_={"weight_kg": statement.excluded.weight_kg},
            )
        )
        await self._session.commit()

    async def upsert_profile(
        self,
        user_id: int,
        *,
        age: int | None = None,
        height_cm: int | None = None,
        goal: Goal | None = None,
        level: Difficulty | None = None,
    ) -> None:
        fields = {
            "birth_year": self._today.year - age if age else None,
            "height_cm": height_cm,
            "goal": goal,
            "level": level,
        }
        # Only overwrite what was actually sent: the app fills these attributes
        # from different screens, at different times.
        provided = {key: value for key, value in fields.items() if value is not None}
        if not provided:
            return
        statement = pg_insert(StudentProfileModel).values(user_id=user_id, **provided)
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[StudentProfileModel.user_id],
                set_={**provided, "updated_at": func.now()},
            )
        )
        await self._session.commit()

    # -- internals -----------------------------------------------------------

    def _to_trainer(self, user: UserModel, profile: TrainerProfileModel, students: int) -> Trainer:
        return Trainer(
            id=user.id,
            name=user.name,
            specialty=Goal(profile.specialty),
            rating=profile.rating,
            price_per_month=profile.price_per_month,
            bio=pick(profile.bio, profile.bio_en, self._locale) if profile.bio else None,
            students=students,
        )

    @staticmethod
    def _profile_query() -> Select[tuple[UserModel, StudentProfileModel]]:
        return select(UserModel, StudentProfileModel).outerjoin(
            StudentProfileModel, StudentProfileModel.user_id == UserModel.id
        )

    async def _detail(self, user_id: int) -> StudentDetail | None:
        row = (
            await self._session.execute(self._profile_query().where(UserModel.id == user_id))
        ).one_or_none()
        if row is None:
            return None
        activity = await self._activity([user_id])
        weights = await self._latest_weights([user_id])
        student = self._to_student(row.UserModel, row.StudentProfileModel, activity, weights)

        metrics = (
            await self._session.execute(
                select(BodyMetricModel)
                .where(BodyMetricModel.user_id == user_id)
                .order_by(BodyMetricModel.measured_on)
            )
        ).scalars()
        logs = (
            await self._session.execute(
                select(WorkoutLogModel, ExerciseModel)
                .join(ExerciseModel, ExerciseModel.id == WorkoutLogModel.exercise_id)
                .where(WorkoutLogModel.user_id == user_id)
                .order_by(WorkoutLogModel.logged_on, ExerciseModel.name)
            )
        ).all()
        return StudentDetail(
            student=student,
            body_metrics=tuple(
                BodyMetric(measured_on=m.measured_on, weight_kg=m.weight_kg) for m in metrics
            ),
            logs=tuple(
                WorkoutLog(
                    logged_on=log.logged_on,
                    exercise_id=log.exercise_id,
                    exercise_name=pick(exercise.name, exercise.name_en, self._locale),
                    weight_kg=log.weight_kg,
                    reps=log.reps,
                    completed=log.completed,
                )
                for log, exercise in logs
            ),
        )

    async def _activity(self, user_ids: Iterable[int]) -> dict[int, tuple[int, date]]:
        """Sessions in the activity window and last training day, per user."""
        ids = list(user_ids)
        if not ids:
            return {}
        cutoff = self._today - timedelta(days=_ACTIVITY_WINDOW_DAYS)
        # A day with three exercises is one session, hence the distinct date.
        recent_days = distinct(
            case((WorkoutLogModel.logged_on >= cutoff, WorkoutLogModel.logged_on))
        )
        rows = await self._session.execute(
            select(
                WorkoutLogModel.user_id,
                func.count(recent_days),
                func.max(WorkoutLogModel.logged_on),
            )
            .where(WorkoutLogModel.user_id.in_(ids))
            .group_by(WorkoutLogModel.user_id)
        )
        return {user_id: (sessions, last) for user_id, sessions, last in rows}

    async def _latest_weights(self, user_ids: Iterable[int]) -> dict[int, float]:
        ids = list(user_ids)
        if not ids:
            return {}
        rows = await self._session.execute(
            select(BodyMetricModel.user_id, BodyMetricModel.weight_kg)
            .where(BodyMetricModel.user_id.in_(ids))
            .order_by(BodyMetricModel.measured_on)
        )
        # Ascending order, so the last row written per user is the most recent.
        return {row.user_id: row.weight_kg for row in rows}

    def _to_student(
        self,
        user: UserModel,
        profile: StudentProfileModel | None,
        activity: dict[int, tuple[int, date]],
        weights: dict[int, float],
    ) -> Student:
        sessions, last_session = activity.get(user.id, (0, None))
        return Student(
            id=user.id,
            name=user.name,
            goal=Goal(profile.goal) if profile and profile.goal else None,
            level=Difficulty(profile.level) if profile and profile.level else None,
            age=self._today.year - profile.birth_year if profile and profile.birth_year else None,
            height_cm=profile.height_cm if profile else None,
            weight_kg=weights.get(user.id),
            sessions_last_30d=sessions,
            last_session_on=last_session,
        )
