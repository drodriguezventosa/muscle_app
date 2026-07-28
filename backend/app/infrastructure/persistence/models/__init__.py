"""ORM models package.

Importing the models here ensures they are registered on `Base.metadata`, which
Alembic autogenerate and `create_all` rely on.
"""

from app.infrastructure.persistence.models.base import EMBEDDING_DIM, Base
from app.infrastructure.persistence.models.coaching import (
    BodyMetricModel,
    StudentProfileModel,
    TrainerStudentModel,
    WorkoutLogModel,
)
from app.infrastructure.persistence.models.exercise import ExerciseModel, ExerciseMuscleModel
from app.infrastructure.persistence.models.food import FoodModel
from app.infrastructure.persistence.models.muscle import MuscleModel
from app.infrastructure.persistence.models.user import UserModel

__all__ = [
    "EMBEDDING_DIM",
    "Base",
    "BodyMetricModel",
    "ExerciseModel",
    "ExerciseMuscleModel",
    "FoodModel",
    "MuscleModel",
    "StudentProfileModel",
    "TrainerStudentModel",
    "UserModel",
    "WorkoutLogModel",
]
