"""SQLAlchemy adapter for the training plan."""

from datetime import date

from sqlalchemy import Row, Select, and_, delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.plan import PlanItem
from app.domain.ports.plan import TrainingPlanRepository
from app.infrastructure.persistence.models.coaching import WorkoutLogModel
from app.infrastructure.persistence.models.exercise import ExerciseModel
from app.infrastructure.persistence.models.plan import PlanItemModel
from app.infrastructure.persistence.repositories.localize import pick


class SqlAlchemyTrainingPlanRepository(TrainingPlanRepository):
    def __init__(self, session: AsyncSession, locale: str = "es") -> None:
        self._session = session
        self._locale = locale

    def _query(self) -> Select[tuple[PlanItemModel, ExerciseModel, WorkoutLogModel]]:
        """Scheduled items with their exercise and the log that fulfils them, if any."""
        return (
            select(PlanItemModel, ExerciseModel, WorkoutLogModel)
            .join(ExerciseModel, ExerciseModel.id == PlanItemModel.exercise_id)
            # The join is on user + exercise + day: that is what "the student did
            # this" means, whether they logged it from the plan or from the
            # workout page.
            .outerjoin(
                WorkoutLogModel,
                and_(
                    WorkoutLogModel.user_id == PlanItemModel.student_id,
                    WorkoutLogModel.exercise_id == PlanItemModel.exercise_id,
                    WorkoutLogModel.logged_on == PlanItemModel.scheduled_on,
                ),
            )
        )

    def _to_entity(
        self, row: Row[tuple[PlanItemModel, ExerciseModel, WorkoutLogModel]]
    ) -> PlanItem:
        item, exercise, log = row
        return PlanItem(
            id=item.id,
            trainer_id=item.trainer_id,
            student_id=item.student_id,
            exercise_id=item.exercise_id,
            exercise_name=pick(exercise.name, exercise.name_en, self._locale),
            scheduled_on=item.scheduled_on,
            target_sets=item.target_sets,
            target_reps=item.target_reps,
            target_weight_kg=item.target_weight_kg,
            notes=item.notes,
            done_weight_kg=log.weight_kg if log else None,
            done_reps=log.reps if log else None,
            done_completed=log.completed if log else None,
        )

    async def list_for_student(self, student_id: int, start: date, end: date) -> list[PlanItem]:
        rows = await self._session.execute(
            self._query()
            .where(
                PlanItemModel.student_id == student_id,
                PlanItemModel.scheduled_on >= start,
                PlanItemModel.scheduled_on <= end,
            )
            .order_by(PlanItemModel.scheduled_on, PlanItemModel.id)
        )
        return [self._to_entity(row) for row in rows]

    async def get(self, item_id: int) -> PlanItem | None:
        row = (
            await self._session.execute(self._query().where(PlanItemModel.id == item_id))
        ).one_or_none()
        return self._to_entity(row) if row else None

    async def add(
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
    ) -> PlanItem | None:
        known = await self._session.scalar(
            select(ExerciseModel.id).where(ExerciseModel.id == exercise_id)
        )
        if known is None:
            return None
        statement = pg_insert(PlanItemModel).values(
            trainer_id=trainer_id,
            student_id=student_id,
            exercise_id=exercise_id,
            scheduled_on=scheduled_on,
            target_sets=target_sets,
            target_reps=target_reps,
            target_weight_kg=target_weight_kg,
            notes=notes,
        )
        item_id = await self._session.scalar(
            statement.on_conflict_do_update(
                constraint="uq_plan_item_day",
                set_={
                    "trainer_id": trainer_id,
                    "target_sets": target_sets,
                    "target_reps": target_reps,
                    "target_weight_kg": target_weight_kg,
                    "notes": notes,
                },
            ).returning(PlanItemModel.id)
        )
        await self._session.commit()
        return await self.get(int(item_id)) if item_id else None

    async def remove(self, item_id: int) -> bool:
        # `returning` rather than rowcount: it is typed, and it says exactly
        # whether a row was there to delete.
        deleted = await self._session.scalar(
            delete(PlanItemModel).where(PlanItemModel.id == item_id).returning(PlanItemModel.id)
        )
        await self._session.commit()
        return deleted is not None
