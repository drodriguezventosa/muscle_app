"""Unit tests for the query use cases using in-memory fake repositories."""

import pytest

from app.application.use_cases.exercise_use_cases import GetExercise
from app.application.use_cases.muscle_use_cases import (
    GetMuscle,
    ListMuscleExercises,
    ListMuscles,
)
from app.domain.entities.exercise import Exercise, TargetedMuscle
from app.domain.entities.muscle import Muscle
from app.domain.ports.repositories import ExerciseRepository, MuscleRepository
from app.domain.value_objects.enums import Difficulty, Equipment, MuscleGroup, MuscleRole


class FakeMuscleRepository(MuscleRepository):
    def __init__(self, muscles: list[Muscle]) -> None:
        self._muscles = muscles

    async def list_all(self) -> list[Muscle]:
        return list(self._muscles)

    async def get_by_id(self, muscle_id: int) -> Muscle | None:
        return next((m for m in self._muscles if m.id == muscle_id), None)

    async def get_by_svg_id(self, svg_id: str) -> Muscle | None:
        return next((m for m in self._muscles if m.svg_id == svg_id), None)


class FakeExerciseRepository(ExerciseRepository):
    def __init__(self, exercises: list[Exercise]) -> None:
        self._exercises = exercises

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        return next((e for e in self._exercises if e.id == exercise_id), None)

    async def list_for_muscle(self, muscle_id: int) -> list[Exercise]:
        return [e for e in self._exercises if e.works_muscle(muscle_id)]

    async def search_similar(
        self,
        embedding: list[float],
        limit: int,
        equipment: Equipment | None = None,
        difficulty: Difficulty | None = None,
    ) -> list[Exercise]:
        return self._exercises[:limit]


@pytest.fixture
def muscles() -> list[Muscle]:
    return [
        Muscle(id=1, name="Chest", muscle_group=MuscleGroup.CHEST, svg_id="chest", description=""),
        Muscle(id=2, name="Biceps", muscle_group=MuscleGroup.ARMS, svg_id="biceps", description=""),
    ]


@pytest.fixture
def exercises() -> list[Exercise]:
    return [
        Exercise(
            id=10,
            name="Push-up",
            description="",
            equipment=Equipment.BODYWEIGHT,
            difficulty=Difficulty.BEGINNER,
            targeted_muscles=(TargetedMuscle(muscle_id=1, role=MuscleRole.PRIMARY),),
        )
    ]


async def test_list_muscles_returns_all(muscles: list[Muscle]) -> None:
    result = await ListMuscles(FakeMuscleRepository(muscles)).execute()
    assert {m.svg_id for m in result} == {"chest", "biceps"}


async def test_get_muscle_found_and_missing(muscles: list[Muscle]) -> None:
    use_case = GetMuscle(FakeMuscleRepository(muscles))
    assert (await use_case.execute("chest")) is not None
    assert (await use_case.execute("unknown")) is None


async def test_list_muscle_exercises_returns_none_for_unknown_muscle(
    muscles: list[Muscle], exercises: list[Exercise]
) -> None:
    use_case = ListMuscleExercises(FakeMuscleRepository(muscles), FakeExerciseRepository(exercises))
    assert (await use_case.execute("unknown")) is None


async def test_list_muscle_exercises_returns_matching(
    muscles: list[Muscle], exercises: list[Exercise]
) -> None:
    use_case = ListMuscleExercises(FakeMuscleRepository(muscles), FakeExerciseRepository(exercises))
    chest = await use_case.execute("chest")
    biceps = await use_case.execute("biceps")
    assert chest is not None and [e.name for e in chest] == ["Push-up"]
    assert biceps == []  # known muscle, no exercises


async def test_get_exercise_found_and_missing(exercises: list[Exercise]) -> None:
    use_case = GetExercise(FakeExerciseRepository(exercises))
    assert (await use_case.execute(10)) is not None
    assert (await use_case.execute(999)) is None
