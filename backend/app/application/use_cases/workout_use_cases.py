"""Generate a basic workout routine from a goal and minimal user attributes.

Read-only and stateless: nothing is persisted. The goal picks the set/rep/rest
scheme and the target muscles; the experience level bounds exercise difficulty;
height/weight only feed the BMI shown as context.
"""

from app.application.dto.workout import GeneratedWorkout, WorkoutRequest
from app.domain.entities.exercise import Exercise
from app.domain.entities.workout import WorkoutItem, WorkoutTemplate
from app.domain.ports.repositories import ExerciseRepository, MuscleRepository
from app.domain.value_objects.enums import Difficulty, Goal, MuscleRole

# Set / rep / rest scheme per goal.
_SCHEME: dict[Goal, tuple[int, str, int]] = {
    Goal.FAT_LOSS: (3, "12-15", 30),
    Goal.HYPERTROPHY: (4, "8-12", 75),
    Goal.STRENGTH: (5, "5", 180),
}

# Ordered target muscles (svg ids) that make up a balanced routine per goal.
_TARGETS: dict[Goal, list[str]] = {
    Goal.FAT_LOSS: ["quads", "chest", "lats", "glutes", "abs"],
    Goal.HYPERTROPHY: ["chest", "lats", "quads", "delts", "biceps", "triceps"],
    Goal.STRENGTH: ["quads", "chest", "lats", "hamstrings", "delts"],
}

# Difficulties offered for each experience level (at or below the level).
_ALLOWED: dict[Difficulty, list[Difficulty]] = {
    Difficulty.BEGINNER: [Difficulty.BEGINNER],
    Difficulty.INTERMEDIATE: [Difficulty.BEGINNER, Difficulty.INTERMEDIATE],
    Difficulty.ADVANCED: [Difficulty.BEGINNER, Difficulty.INTERMEDIATE, Difficulty.ADVANCED],
}

# Localized routine name/description per goal.
_NAMES: dict[Goal, dict[str, str]] = {
    Goal.FAT_LOSS: {"es": "Rutina de pérdida de grasa", "en": "Fat-loss routine"},
    Goal.HYPERTROPHY: {"es": "Rutina de hipertrofia", "en": "Hypertrophy routine"},
    Goal.STRENGTH: {"es": "Rutina de fuerza", "en": "Strength routine"},
}
_DESCS: dict[Goal, dict[str, str]] = {
    Goal.FAT_LOSS: {
        "es": "Circuito de cuerpo completo con repeticiones altas y descansos cortos.",
        "en": "Full-body circuit with high reps and short rests.",
    },
    Goal.HYPERTROPHY: {
        "es": "Cuerpo completo con volumen moderado para ganar masa muscular.",
        "en": "Full-body with moderate volume to build muscle.",
    },
    Goal.STRENGTH: {
        "es": "Básicos pesados con pocas repeticiones y descansos largos.",
        "en": "Heavy compound lifts with low reps and long rests.",
    },
}


def _bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "underweight"
    if bmi < 25:
        return "normal"
    if bmi < 30:
        return "overweight"
    return "obese"


class GenerateWorkout:
    """Build a basic routine for the requested goal and attributes."""

    def __init__(
        self, muscles: MuscleRepository, exercises: ExerciseRepository, locale: str = "es"
    ) -> None:
        self._muscles = muscles
        self._exercises = exercises
        self._locale = locale

    def _lang(self, table: dict[Goal, dict[str, str]], goal: Goal) -> str:
        return table[goal].get(self._locale, table[goal]["es"])

    def _pick(self, candidates: list[Exercise], muscle_id: int, used: set[int]) -> Exercise | None:
        pool = [e for e in candidates if e.id not in used] or candidates
        # Prefer an exercise where this muscle is the primary mover.
        for exercise in pool:
            if any(
                tm.muscle_id == muscle_id and tm.role == MuscleRole.PRIMARY
                for tm in exercise.targeted_muscles
            ):
                return exercise
        return pool[0] if pool else None

    async def execute(self, request: WorkoutRequest) -> GeneratedWorkout:
        sets, reps, rest = _SCHEME[request.goal]
        # Beginners train with a little less volume.
        if request.experience == Difficulty.BEGINNER:
            sets = min(sets, 3)
        allowed = _ALLOWED[request.experience]

        items: list[WorkoutItem] = []
        used: set[int] = set()
        for svg_id in _TARGETS[request.goal]:
            muscle = await self._muscles.get_by_svg_id(svg_id)
            if muscle is None or muscle.id is None:
                continue
            candidates = await self._exercises.list_for_muscle(
                muscle.id, request.equipment, allowed
            )
            exercise = self._pick(candidates, muscle.id, used)
            if exercise is None or exercise.id is None:
                continue
            used.add(exercise.id)
            items.append(WorkoutItem(exercise=exercise, sets=sets, reps=reps, rest_seconds=rest))

        template = WorkoutTemplate(
            goal=request.goal,
            name=self._lang(_NAMES, request.goal),
            description=self._lang(_DESCS, request.goal),
            difficulty=request.experience,
            items=tuple(items),
        )

        height_m = request.height_cm / 100
        bmi = round(request.weight_kg / (height_m * height_m), 1) if height_m > 0 else 0.0
        return GeneratedWorkout(template=template, bmi=bmi, bmi_category=_bmi_category(bmi))
