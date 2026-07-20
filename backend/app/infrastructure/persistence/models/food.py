"""ORM model for foods (nutrition catalog). Macros are per 100 g."""

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import EMBEDDING_DIM, Base


class FoodModel(Base):
    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(primary_key=True)
    # `name` holds Spanish (default); `name_en` the English override.
    name: Mapped[str] = mapped_column(String(120), unique=True)
    name_en: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category: Mapped[str] = mapped_column(String(40))
    kcal: Mapped[float] = mapped_column(Float)
    protein_g: Mapped[float] = mapped_column(Float)
    carbs_g: Mapped[float] = mapped_column(Float)
    fat_g: Mapped[float] = mapped_column(Float)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # Semantic embedding for RAG meal recommendations (filled by the AI phase).
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
