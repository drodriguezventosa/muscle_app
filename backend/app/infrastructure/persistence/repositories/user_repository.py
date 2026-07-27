"""SQLAlchemy adapter for the user directory."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.ports.auth import UserRepository
from app.domain.value_objects.enums import UserRole
from app.infrastructure.persistence.models.user import UserModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(id=model.id, email=model.email, name=model.name, role=UserRole(model.role))

    async def get_by_email(self, email: str) -> User | None:
        model = await self._session.scalar(
            select(UserModel).where(UserModel.email == email.strip().lower())
        )
        return self._to_entity(model) if model else None

    async def get_by_id(self, user_id: int) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return self._to_entity(model) if model else None

    async def get_password_hash(self, user_id: int) -> str | None:
        model = await self._session.get(UserModel, user_id)
        return model.password_hash if model else None
