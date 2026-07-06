"""SQLAlchemy implementation of the MuscleRepository port."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.muscle import Muscle
from app.domain.ports.repositories import MuscleRepository
from app.infrastructure.persistence.models.muscle import MuscleModel


def _to_entity(model: MuscleModel) -> Muscle:
    return Muscle(
        id=model.id,
        name=model.name,
        muscle_group=model.muscle_group,
        svg_id=model.svg_id,
        description=model.description,
    )


class SqlAlchemyMuscleRepository(MuscleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Muscle]:
        result = await self._session.scalars(select(MuscleModel).order_by(MuscleModel.name))
        return [_to_entity(m) for m in result]

    async def get_by_id(self, muscle_id: int) -> Muscle | None:
        model = await self._session.get(MuscleModel, muscle_id)
        return _to_entity(model) if model else None

    async def get_by_svg_id(self, svg_id: str) -> Muscle | None:
        result = await self._session.scalars(
            select(MuscleModel).where(MuscleModel.svg_id == svg_id)
        )
        model = result.first()
        return _to_entity(model) if model else None
