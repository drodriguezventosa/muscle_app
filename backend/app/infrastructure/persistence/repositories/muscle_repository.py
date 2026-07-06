"""SQLAlchemy implementation of the MuscleRepository port."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.muscle import Muscle
from app.domain.ports.repositories import MuscleRepository
from app.infrastructure.persistence.models.muscle import MuscleModel
from app.infrastructure.persistence.repositories.localize import pick


class SqlAlchemyMuscleRepository(MuscleRepository):
    def __init__(self, session: AsyncSession, locale: str = "es") -> None:
        self._session = session
        self._locale = locale

    def _to_entity(self, model: MuscleModel) -> Muscle:
        return Muscle(
            id=model.id,
            name=pick(model.name, model.name_en, self._locale),
            muscle_group=model.muscle_group,
            svg_id=model.svg_id,
            description=pick(model.description, model.description_en, self._locale),
        )

    async def list_all(self) -> list[Muscle]:
        result = await self._session.scalars(select(MuscleModel).order_by(MuscleModel.name))
        return [self._to_entity(m) for m in result]

    async def get_by_id(self, muscle_id: int) -> Muscle | None:
        model = await self._session.get(MuscleModel, muscle_id)
        return self._to_entity(model) if model else None

    async def get_by_svg_id(self, svg_id: str) -> Muscle | None:
        result = await self._session.scalars(
            select(MuscleModel).where(MuscleModel.svg_id == svg_id)
        )
        model = result.first()
        return self._to_entity(model) if model else None
