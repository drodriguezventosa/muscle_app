"""Unit tests for the query use cases using in-memory fake repositories."""

import pytest

from app.application.use_cases.exercise_use_cases import GetExercise
from app.application.use_cases.muscle_use_cases import (
    GetMuscle,
    ListActiveMuscles,
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

    async def list_with_matching_exercises(
        self,
        equipment: list[Equipment] | None = None,
        difficulty: list[Difficulty] | None = None,
    ) -> list[Muscle]:
        # The real join lives in the SQL adapter; the fake just echoes the catalog.
        return list(self._muscles)


class FakeExerciseRepository(ExerciseRepository):
    def __init__(self, exercises: list[Exercise]) -> None:
        self._exercises = exercises

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        return next((e for e in self._exercises if e.id == exercise_id), None)

    async def list_for_muscle(
        self,
        muscle_id: int,
        equipment: list[Equipment] | None = None,
        difficulty: list[Difficulty] | None = None,
    ) -> list[Exercise]:
        matches = [e for e in self._exercises if e.works_muscle(muscle_id)]
        if equipment:
            matches = [e for e in matches if e.equipment in equipment]
        if difficulty:
            matches = [e for e in matches if e.difficulty in difficulty]
        return matches

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


async def test_list_muscle_exercises_applies_filters(
    muscles: list[Muscle], exercises: list[Exercise]
) -> None:
    use_case = ListMuscleExercises(FakeMuscleRepository(muscles), FakeExerciseRepository(exercises))
    # The single seeded chest exercise is bodyweight/beginner.
    assert await use_case.execute("chest", [Equipment.BODYWEIGHT], None) != []
    assert await use_case.execute("chest", [Equipment.BARBELL], None) == []
    assert await use_case.execute("chest", None, [Difficulty.ADVANCED]) == []


async def test_list_active_muscles_delegates(muscles: list[Muscle]) -> None:
    result = await ListActiveMuscles(FakeMuscleRepository(muscles)).execute()
    assert {m.svg_id for m in result} == {"chest", "biceps"}


async def test_get_exercise_found_and_missing(exercises: list[Exercise]) -> None:
    use_case = GetExercise(FakeExerciseRepository(exercises))
    assert (await use_case.execute(10)) is not None
    assert (await use_case.execute(999)) is None


async def test_generate_workout_scheme_and_bmi(
    muscles: list[Muscle], exercises: list[Exercise]
) -> None:
    from app.application.dto.workout import WorkoutRequest
    from app.application.use_cases.workout_use_cases import GenerateWorkout
    from app.domain.value_objects.enums import Goal

    use_case = GenerateWorkout(
        FakeMuscleRepository(muscles), FakeExerciseRepository(exercises), "es"
    )
    result = await use_case.execute(
        WorkoutRequest(
            goal=Goal.HYPERTROPHY,
            experience=Difficulty.INTERMEDIATE,
            height_cm=180,
            weight_kg=81,
        )
    )
    assert result.bmi == 25.0  # 81 / 1.8^2
    assert result.bmi_category == "overweight"
    assert result.template.goal == Goal.HYPERTROPHY
    # The chest target resolves to the seeded Push-up; hypertrophy scheme applies.
    assert len(result.template.items) >= 1
    assert all(
        i.sets == 4 and i.reps == "8-12" and i.rest_seconds == 75 for i in result.template.items
    )
