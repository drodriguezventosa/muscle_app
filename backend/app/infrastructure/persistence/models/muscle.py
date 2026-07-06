"""ORM model for muscles."""

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.value_objects.enums import MuscleGroup
from app.infrastructure.persistence.models.base import Base


class MuscleModel(Base):
    __tablename__ = "muscles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    # native_enum=False stores the value as VARCHAR with a CHECK constraint,
    # which keeps migrations simple (no Postgres ENUM types to alter).
    muscle_group: Mapped[MuscleGroup] = mapped_column(
        SAEnum(MuscleGroup, native_enum=False, length=20)
    )
    svg_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
