"""Idempotent seed data for the muscle and exercise catalog.

Run as a script (`python -m app.infrastructure.persistence.seed`) or import
`seed` and call it with a session. Embeddings are left null here and computed by
the AI phase.
"""

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.value_objects.enums import Difficulty, Equipment, MuscleGroup, MuscleRole
from app.infrastructure.persistence.database import get_session_factory
from app.infrastructure.persistence.models.exercise import ExerciseModel, ExerciseMuscleModel
from app.infrastructure.persistence.models.muscle import MuscleModel

# (name, group, svg_id, description)
MUSCLES: list[tuple[str, MuscleGroup, str, str]] = [
    ("Pectoralis major", MuscleGroup.CHEST, "chest", "Large fan-shaped chest muscle."),
    ("Latissimus dorsi", MuscleGroup.BACK, "lats", "Broad muscle of the mid/lower back."),
    ("Trapezius", MuscleGroup.BACK, "traps", "Upper-back muscle moving the scapula."),
    ("Deltoid", MuscleGroup.SHOULDERS, "delts", "Rounded muscle capping the shoulder."),
    ("Biceps brachii", MuscleGroup.ARMS, "biceps", "Front upper-arm flexor."),
    ("Triceps brachii", MuscleGroup.ARMS, "triceps", "Back upper-arm extensor."),
    ("Rectus abdominis", MuscleGroup.CORE, "abs", "Front abdominal muscle."),
    ("Quadriceps", MuscleGroup.LEGS, "quads", "Front thigh muscle group."),
    ("Hamstrings", MuscleGroup.LEGS, "hamstrings", "Back thigh muscle group."),
    ("Gluteus maximus", MuscleGroup.GLUTES, "glutes", "Largest muscle of the buttocks."),
]

# (name, description, equipment, difficulty, [(muscle_svg_id, role)])
EXERCISES: list[tuple[str, str, Equipment, Difficulty, list[tuple[str, MuscleRole]]]] = [
    (
        "Push-up",
        "Bodyweight press from the floor.",
        Equipment.BODYWEIGHT,
        Difficulty.BEGINNER,
        [
            ("chest", MuscleRole.PRIMARY),
            ("triceps", MuscleRole.SECONDARY),
            ("delts", MuscleRole.SECONDARY),
        ],
    ),
    (
        "Barbell bench press",
        "Press a barbell while lying on a bench.",
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [("chest", MuscleRole.PRIMARY), ("triceps", MuscleRole.SECONDARY)],
    ),
    (
        "Pull-up",
        "Pull the body up to a bar with an overhand grip.",
        Equipment.BODYWEIGHT,
        Difficulty.ADVANCED,
        [("lats", MuscleRole.PRIMARY), ("biceps", MuscleRole.SECONDARY)],
    ),
    (
        "Bent-over row",
        "Row a barbell toward the torso while hinged forward.",
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [
            ("lats", MuscleRole.PRIMARY),
            ("traps", MuscleRole.SECONDARY),
            ("biceps", MuscleRole.SECONDARY),
        ],
    ),
    (
        "Overhead press",
        "Press a barbell overhead from the shoulders.",
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [("delts", MuscleRole.PRIMARY), ("triceps", MuscleRole.SECONDARY)],
    ),
    (
        "Dumbbell biceps curl",
        "Curl dumbbells toward the shoulders.",
        Equipment.DUMBBELL,
        Difficulty.BEGINNER,
        [("biceps", MuscleRole.PRIMARY)],
    ),
    (
        "Triceps rope pushdown",
        "Extend the elbows against a cable.",
        Equipment.CABLE,
        Difficulty.BEGINNER,
        [("triceps", MuscleRole.PRIMARY)],
    ),
    (
        "Plank",
        "Hold a straight-body position on the forearms.",
        Equipment.BODYWEIGHT,
        Difficulty.BEGINNER,
        [("abs", MuscleRole.PRIMARY)],
    ),
    (
        "Barbell back squat",
        "Squat with a barbell across the upper back.",
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [
            ("quads", MuscleRole.PRIMARY),
            ("glutes", MuscleRole.SECONDARY),
            ("hamstrings", MuscleRole.SECONDARY),
        ],
    ),
    (
        "Romanian deadlift",
        "Hip-hinge with a barbell to load the posterior chain.",
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [("hamstrings", MuscleRole.PRIMARY), ("glutes", MuscleRole.SECONDARY)],
    ),
]


async def seed(session: AsyncSession) -> bool:
    """Populate the catalog if empty. Returns True if data was inserted."""
    existing = await session.scalar(select(func.count()).select_from(MuscleModel))
    if existing:
        return False

    muscles = {
        svg_id: MuscleModel(name=name, muscle_group=group, svg_id=svg_id, description=desc)
        for name, group, svg_id, desc in MUSCLES
    }
    session.add_all(muscles.values())
    await session.flush()  # assign muscle ids

    for name, desc, equipment, difficulty, links in EXERCISES:
        exercise = ExerciseModel(
            name=name, description=desc, equipment=equipment, difficulty=difficulty
        )
        exercise.muscles = [
            ExerciseMuscleModel(muscle_id=muscles[svg_id].id, role=role) for svg_id, role in links
        ]
        session.add(exercise)

    await session.commit()
    return True


async def _main() -> None:
    factory = get_session_factory()
    async with factory() as session:
        inserted = await seed(session)
    print("Seed inserted." if inserted else "Catalog already seeded; nothing to do.")


if __name__ == "__main__":
    asyncio.run(_main())
