"""ORM models for exercises and their relation to muscles."""

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.value_objects.enums import Difficulty, Equipment, MuscleRole
from app.infrastructure.persistence.models.base import EMBEDDING_DIM, Base


class ExerciseModel(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    # `name`/`description` hold the Spanish (default) text; `*_en` are the English
    # overrides. The repository resolves the right one per requested locale.
    name: Mapped[str] = mapped_column(String(120), unique=True)
    name_en: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    equipment: Mapped[Equipment] = mapped_column(SAEnum(Equipment, native_enum=False, length=20))
    difficulty: Mapped[Difficulty] = mapped_column(SAEnum(Difficulty, native_enum=False, length=20))
    # Semantic embedding for RAG search. Nullable: populated by the AI phase.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    muscles: Mapped[list["ExerciseMuscleModel"]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ExerciseMuscleModel(Base):
    __tablename__ = "exercise_muscles"

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True
    )
    muscle_id: Mapped[int] = mapped_column(
        ForeignKey("muscles.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[MuscleRole] = mapped_column(SAEnum(MuscleRole, native_enum=False, length=20))

    exercise: Mapped["ExerciseModel"] = relationship(back_populates="muscles")
