"""Idempotent seed data for the muscle and exercise catalog (ES + EN).

Run as a script (`python -m app.infrastructure.persistence.seed`) or import
`seed` and call it with a session. Embeddings are left null here and computed by
the AI phase. `name`/`description` hold Spanish; `*_en` hold English.
"""

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.value_objects.enums import Difficulty, Equipment, MuscleGroup, MuscleRole
from app.infrastructure.persistence.database import get_session_factory
from app.infrastructure.persistence.models.exercise import ExerciseModel, ExerciseMuscleModel
from app.infrastructure.persistence.models.muscle import MuscleModel

# (name_es, name_en, group, svg_id, description_es, description_en)
MUSCLES: list[tuple[str, str, MuscleGroup, str, str, str]] = [
    (
        "Pectoral mayor",
        "Pectoralis major",
        MuscleGroup.CHEST,
        "chest",
        "Gran músculo del pecho en forma de abanico.",
        "Large fan-shaped chest muscle.",
    ),
    (
        "Dorsal ancho",
        "Latissimus dorsi",
        MuscleGroup.BACK,
        "lats",
        "Músculo ancho de la espalda media y baja.",
        "Broad muscle of the mid/lower back.",
    ),
    (
        "Trapecio",
        "Trapezius",
        MuscleGroup.BACK,
        "traps",
        "Músculo de la espalda alta que mueve la escápula.",
        "Upper-back muscle moving the scapula.",
    ),
    (
        "Deltoides",
        "Deltoid",
        MuscleGroup.SHOULDERS,
        "delts",
        "Músculo redondeado que cubre el hombro.",
        "Rounded muscle capping the shoulder.",
    ),
    (
        "Bíceps braquial",
        "Biceps brachii",
        MuscleGroup.ARMS,
        "biceps",
        "Flexor de la parte frontal del brazo.",
        "Front upper-arm flexor.",
    ),
    (
        "Tríceps braquial",
        "Triceps brachii",
        MuscleGroup.ARMS,
        "triceps",
        "Extensor de la parte posterior del brazo.",
        "Back upper-arm extensor.",
    ),
    (
        "Recto abdominal",
        "Rectus abdominis",
        MuscleGroup.CORE,
        "abs",
        "Músculo frontal del abdomen.",
        "Front abdominal muscle.",
    ),
    (
        "Cuádriceps",
        "Quadriceps",
        MuscleGroup.LEGS,
        "quads",
        "Grupo muscular frontal del muslo.",
        "Front thigh muscle group.",
    ),
    (
        "Isquiotibiales",
        "Hamstrings",
        MuscleGroup.LEGS,
        "hamstrings",
        "Grupo muscular posterior del muslo.",
        "Back thigh muscle group.",
    ),
    (
        "Glúteo mayor",
        "Gluteus maximus",
        MuscleGroup.GLUTES,
        "glutes",
        "El músculo más grande de los glúteos.",
        "Largest muscle of the buttocks.",
    ),
]

# (name_es, name_en, description_es, description_en, equipment, difficulty, [(svg_id, role)])
EXERCISES: list[tuple[str, str, str, str, Equipment, Difficulty, list[tuple[str, MuscleRole]]]] = [
    (
        "Flexiones",
        "Push-up",
        "Empuje con el peso corporal desde el suelo.",
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
        "Press de banca con barra",
        "Barbell bench press",
        "Empuja una barra tumbado en un banco.",
        "Press a barbell while lying on a bench.",
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [("chest", MuscleRole.PRIMARY), ("triceps", MuscleRole.SECONDARY)],
    ),
    (
        "Dominadas",
        "Pull-up",
        "Elévate hasta una barra con agarre prono.",
        "Pull the body up to a bar with an overhand grip.",
        Equipment.BODYWEIGHT,
        Difficulty.ADVANCED,
        [("lats", MuscleRole.PRIMARY), ("biceps", MuscleRole.SECONDARY)],
    ),
    (
        "Remo inclinado",
        "Bent-over row",
        "Rema una barra hacia el torso con el cuerpo inclinado.",
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
        "Press militar",
        "Overhead press",
        "Empuja una barra por encima de la cabeza desde los hombros.",
        "Press a barbell overhead from the shoulders.",
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [("delts", MuscleRole.PRIMARY), ("triceps", MuscleRole.SECONDARY)],
    ),
    (
        "Curl de bíceps con mancuernas",
        "Dumbbell biceps curl",
        "Flexiona las mancuernas hacia los hombros.",
        "Curl dumbbells toward the shoulders.",
        Equipment.DUMBBELL,
        Difficulty.BEGINNER,
        [("biceps", MuscleRole.PRIMARY)],
    ),
    (
        "Extensión de tríceps en polea",
        "Triceps rope pushdown",
        "Extiende los codos contra una polea.",
        "Extend the elbows against a cable.",
        Equipment.CABLE,
        Difficulty.BEGINNER,
        [("triceps", MuscleRole.PRIMARY)],
    ),
    (
        "Plancha",
        "Plank",
        "Mantén el cuerpo recto apoyado en los antebrazos.",
        "Hold a straight-body position on the forearms.",
        Equipment.BODYWEIGHT,
        Difficulty.BEGINNER,
        [("abs", MuscleRole.PRIMARY)],
    ),
    (
        "Sentadilla con barra",
        "Barbell back squat",
        "Sentadilla con una barra sobre la espalda alta.",
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
        "Peso muerto rumano",
        "Romanian deadlift",
        "Bisagra de cadera con barra para la cadena posterior.",
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
        svg_id: MuscleModel(
            name=name_es,
            name_en=name_en,
            muscle_group=group,
            svg_id=svg_id,
            description=desc_es,
            description_en=desc_en,
        )
        for name_es, name_en, group, svg_id, desc_es, desc_en in MUSCLES
    }
    session.add_all(muscles.values())
    await session.flush()  # assign muscle ids

    for name_es, name_en, desc_es, desc_en, equipment, difficulty, links in EXERCISES:
        exercise = ExerciseModel(
            name=name_es,
            name_en=name_en,
            description=desc_es,
            description_en=desc_en,
            equipment=equipment,
            difficulty=difficulty,
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
