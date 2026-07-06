"""ORM models package.

Importing the models here ensures they are registered on `Base.metadata`, which
Alembic autogenerate and `create_all` rely on.
"""

from app.infrastructure.persistence.models.base import EMBEDDING_DIM, Base
from app.infrastructure.persistence.models.exercise import ExerciseModel, ExerciseMuscleModel
from app.infrastructure.persistence.models.muscle import MuscleModel

__all__ = [
    "EMBEDDING_DIM",
    "Base",
    "ExerciseModel",
    "ExerciseMuscleModel",
    "MuscleModel",
]
