"""Unit tests for the pure domain entities and value objects."""

from app.domain.entities.exercise import Exercise, TargetedMuscle
from app.domain.entities.muscle import Muscle
from app.domain.value_objects.enums import Difficulty, Equipment, MuscleGroup, MuscleRole


def test_muscle_is_immutable() -> None:
    muscle = Muscle(name="Biceps", muscle_group=MuscleGroup.ARMS, svg_id="biceps", description="")
    assert muscle.id is None
    assert muscle.muscle_group is MuscleGroup.ARMS


def test_exercise_works_muscle() -> None:
    exercise = Exercise(
        name="Push-up",
        description="",
        equipment=Equipment.BODYWEIGHT,
        difficulty=Difficulty.BEGINNER,
        targeted_muscles=(
            TargetedMuscle(muscle_id=1, role=MuscleRole.PRIMARY),
            TargetedMuscle(muscle_id=2, role=MuscleRole.SECONDARY),
        ),
    )
    assert exercise.works_muscle(1) is True
    assert exercise.works_muscle(2) is True
    assert exercise.works_muscle(99) is False


def test_exercise_defaults_to_no_targeted_muscles() -> None:
    exercise = Exercise(
        name="Mystery",
        description="",
        equipment=Equipment.MACHINE,
        difficulty=Difficulty.INTERMEDIATE,
    )
    assert exercise.targeted_muscles == ()
    assert exercise.works_muscle(1) is False


def test_enum_values_are_stable_strings() -> None:
    # The API and DB rely on these string values staying constant.
    assert MuscleGroup.CHEST.value == "chest"
    assert Equipment.BODYWEIGHT.value == "bodyweight"
    assert Difficulty.ADVANCED.value == "advanced"
    assert MuscleRole.PRIMARY.value == "primary"
