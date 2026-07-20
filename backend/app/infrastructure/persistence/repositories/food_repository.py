"""SQLAlchemy adapter for the food catalog."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.food import Food
from app.domain.ports.repositories import FoodRepository
from app.infrastructure.persistence.models.food import FoodModel
from app.infrastructure.persistence.repositories.localize import pick


def to_food_entity(model: FoodModel, locale: str) -> Food:
    return Food(
        id=model.id,
        name=pick(model.name, model.name_en, locale),
        category=model.category,
        kcal=model.kcal,
        protein_g=model.protein_g,
        carbs_g=model.carbs_g,
        fat_g=model.fat_g,
        tags=tuple(model.tags or ()),
    )


class SqlAlchemyFoodRepository(FoodRepository):
    def __init__(self, session: AsyncSession, locale: str = "es") -> None:
        self._session = session
        self._locale = locale

    async def list_all(self) -> list[Food]:
        result = await self._session.scalars(select(FoodModel).order_by(FoodModel.name))
        return [to_food_entity(m, self._locale) for m in result]

    async def search_similar(self, embedding: list[float], limit: int) -> list[Food]:
        stmt = (
            select(FoodModel)
            .where(FoodModel.embedding.is_not(None))
            .order_by(FoodModel.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await self._session.scalars(stmt)
        return [to_food_entity(m, self._locale) for m in result]
