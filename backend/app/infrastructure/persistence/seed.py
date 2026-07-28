"""Idempotent seed data for the muscle and exercise catalog (ES + EN).

Run as a script (`python -m app.infrastructure.persistence.seed`) or import
`seed` and call it with a session. Embeddings are left null here and computed by
the AI phase. `name`/`description`/`video_url` hold Spanish; `*_en` hold English.
"""

import asyncio
import math
import random
import secrets
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache

from sqlalchemy import func, insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.value_objects.enums import (
    Difficulty,
    Equipment,
    Goal,
    MuscleGroup,
    MuscleRole,
    UserRole,
)
from app.infrastructure.persistence.database import get_session_factory
from app.infrastructure.persistence.models.coaching import (
    BodyMetricModel,
    StudentProfileModel,
    TrainerProfileModel,
    TrainerStudentModel,
    WorkoutLogModel,
)
from app.infrastructure.persistence.models.exercise import ExerciseModel, ExerciseMuscleModel
from app.infrastructure.persistence.models.food import FoodModel
from app.infrastructure.persistence.models.muscle import MuscleModel
from app.infrastructure.persistence.models.plan import PlanItemModel
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.security.hashing import Argon2Hasher


def _yt(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


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

# (name_es, name_en, desc_es, desc_en, video_es, video_en, equipment, difficulty, links)
# video_es/video_en are None for catalog entries without a demonstration video yet.
ExerciseSeed = tuple[
    str,
    str,
    str,
    str,
    str | None,
    str | None,
    Equipment,
    Difficulty,
    list[tuple[str, MuscleRole]],
]
EXERCISES: list[ExerciseSeed] = [
    (
        "Flexiones",
        "Push-up",
        "Empuje con el peso corporal desde el suelo.",
        "Bodyweight press from the floor.",
        _yt("sKmzcJKGKMI"),
        _yt("WDIpL0pjun0"),
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
        _yt("fqsTgdTPRQU"),
        _yt("Pp8rHcFVIYg"),
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [("chest", MuscleRole.PRIMARY), ("triceps", MuscleRole.SECONDARY)],
    ),
    (
        "Dominadas",
        "Pull-up",
        "Elévate hasta una barra con agarre prono.",
        "Pull the body up to a bar with an overhand grip.",
        _yt("8mhDd9Ahl1M"),
        _yt("TMnxKjdYcME"),
        Equipment.BODYWEIGHT,
        Difficulty.ADVANCED,
        [("lats", MuscleRole.PRIMARY), ("biceps", MuscleRole.SECONDARY)],
    ),
    (
        "Remo inclinado",
        "Bent-over row",
        "Rema una barra hacia el torso con el cuerpo inclinado.",
        "Row a barbell toward the torso while hinged forward.",
        _yt("3uiWjik2yEQ"),
        _yt("rqTOAM8WoeM"),
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
        _yt("OHxSwnkSxB8"),
        _yt("a81SaIpjGlA"),
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [("delts", MuscleRole.PRIMARY), ("triceps", MuscleRole.SECONDARY)],
    ),
    (
        "Curl de bíceps con mancuernas",
        "Dumbbell biceps curl",
        "Flexiona las mancuernas hacia los hombros.",
        "Curl dumbbells toward the shoulders.",
        _yt("RsHskJ9k_p0"),
        _yt("ykJmrZ5v0Oo"),
        Equipment.DUMBBELL,
        Difficulty.BEGINNER,
        [("biceps", MuscleRole.PRIMARY)],
    ),
    (
        "Extensión de tríceps en polea",
        "Triceps rope pushdown",
        "Extiende los codos contra una polea.",
        "Extend the elbows against a cable.",
        _yt("20incKRiLek"),
        _yt("qHDrQglWgS4"),
        Equipment.CABLE,
        Difficulty.BEGINNER,
        [("triceps", MuscleRole.PRIMARY)],
    ),
    (
        "Plancha",
        "Plank",
        "Mantén el cuerpo recto apoyado en los antebrazos.",
        "Hold a straight-body position on the forearms.",
        _yt("nmX0DysvqcQ"),
        _yt("mwlp75MS6Rg"),
        Equipment.BODYWEIGHT,
        Difficulty.BEGINNER,
        [("abs", MuscleRole.PRIMARY)],
    ),
    (
        "Sentadilla con barra",
        "Barbell back squat",
        "Sentadilla con una barra sobre la espalda alta.",
        "Squat with a barbell across the upper back.",
        _yt("TPoVS6ag6l4"),
        _yt("eMYjBnIVb_A"),
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
        _yt("rjvlSfZ-PQw"),
        _yt("7j-2w4-P14I"),
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [("hamstrings", MuscleRole.PRIMARY), ("glutes", MuscleRole.SECONDARY)],
    ),
    # --- Extended catalog (no demonstration video yet) --------------------
    # Videos are left null so the "watch example" button simply hides; the
    # variety across equipment/difficulty is what makes the explorer filters
    # useful. Add verified YouTube ids later to light up the button.
    # Chest
    (
        "Press inclinado con mancuernas",
        "Incline dumbbell press",
        "Empuje en banco inclinado para el pecho superior.",
        "Press on an incline bench to bias the upper chest.",
        None,
        None,
        Equipment.DUMBBELL,
        Difficulty.INTERMEDIATE,
        [("chest", MuscleRole.PRIMARY), ("delts", MuscleRole.SECONDARY)],
    ),
    (
        "Aperturas con mancuernas",
        "Dumbbell fly",
        "Apertura de brazos en banco para estirar y contraer el pecho.",
        "Arc the arms open on a bench to stretch and squeeze the chest.",
        None,
        None,
        Equipment.DUMBBELL,
        Difficulty.BEGINNER,
        [("chest", MuscleRole.PRIMARY)],
    ),
    (
        "Fondos en paralelas",
        "Chest dip",
        "Fondos inclinando el torso para cargar el pecho.",
        "Dips with a forward lean to load the chest.",
        None,
        None,
        Equipment.BODYWEIGHT,
        Difficulty.ADVANCED,
        [("chest", MuscleRole.PRIMARY), ("triceps", MuscleRole.SECONDARY)],
    ),
    (
        "Cruce de poleas",
        "Cable crossover",
        "Cruce de poleas para contraer el pecho en el centro.",
        "Bring both cables together to squeeze the chest.",
        None,
        None,
        Equipment.CABLE,
        Difficulty.INTERMEDIATE,
        [("chest", MuscleRole.PRIMARY)],
    ),
    # Lats / back
    (
        "Jalón al pecho en polea",
        "Lat pulldown",
        "Tira de la barra hacia el pecho en la polea alta.",
        "Pull the bar down to the chest on the high pulley.",
        None,
        None,
        Equipment.CABLE,
        Difficulty.BEGINNER,
        [("lats", MuscleRole.PRIMARY), ("biceps", MuscleRole.SECONDARY)],
    ),
    (
        "Remo con mancuerna a una mano",
        "One-arm dumbbell row",
        "Rema una mancuerna apoyado en un banco.",
        "Row a dumbbell with one hand braced on a bench.",
        None,
        None,
        Equipment.DUMBBELL,
        Difficulty.BEGINNER,
        [("lats", MuscleRole.PRIMARY), ("biceps", MuscleRole.SECONDARY)],
    ),
    (
        "Pullover con mancuerna",
        "Dumbbell pullover",
        "Lleva la mancuerna por detrás de la cabeza tumbado.",
        "Take the dumbbell overhead while lying back.",
        None,
        None,
        Equipment.DUMBBELL,
        Difficulty.INTERMEDIATE,
        [("lats", MuscleRole.PRIMARY)],
    ),
    # Traps
    (
        "Encogimientos con barra",
        "Barbell shrug",
        "Eleva los hombros con una barra para el trapecio.",
        "Lift the shoulders with a barbell to work the traps.",
        None,
        None,
        Equipment.BARBELL,
        Difficulty.BEGINNER,
        [("traps", MuscleRole.PRIMARY)],
    ),
    (
        "Remo al mentón",
        "Upright row",
        "Tira de la barra hacia la barbilla pegada al cuerpo.",
        "Pull the bar up toward the chin close to the body.",
        None,
        None,
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [("traps", MuscleRole.PRIMARY), ("delts", MuscleRole.SECONDARY)],
    ),
    (
        "Face pull en polea",
        "Cable face pull",
        "Tira de la cuerda hacia la cara para trapecio y hombro posterior.",
        "Pull the rope toward the face for traps and rear delts.",
        None,
        None,
        Equipment.CABLE,
        Difficulty.BEGINNER,
        [("traps", MuscleRole.PRIMARY), ("delts", MuscleRole.SECONDARY)],
    ),
    # Delts
    (
        "Elevaciones laterales con mancuernas",
        "Dumbbell lateral raise",
        "Eleva las mancuernas a los lados hasta la altura del hombro.",
        "Raise the dumbbells out to shoulder height.",
        None,
        None,
        Equipment.DUMBBELL,
        Difficulty.BEGINNER,
        [("delts", MuscleRole.PRIMARY)],
    ),
    (
        "Press de hombros con mancuernas",
        "Dumbbell shoulder press",
        "Empuja las mancuernas por encima de la cabeza sentado.",
        "Press the dumbbells overhead while seated.",
        None,
        None,
        Equipment.DUMBBELL,
        Difficulty.INTERMEDIATE,
        [("delts", MuscleRole.PRIMARY), ("triceps", MuscleRole.SECONDARY)],
    ),
    (
        "Pájaros con mancuernas",
        "Rear delt fly",
        "Apertura inclinado hacia delante para el hombro posterior.",
        "Bent-over reverse fly for the rear delts.",
        None,
        None,
        Equipment.DUMBBELL,
        Difficulty.BEGINNER,
        [("delts", MuscleRole.PRIMARY)],
    ),
    # Biceps
    (
        "Curl con barra",
        "Barbell curl",
        "Flexiona la barra hacia los hombros de pie.",
        "Curl the barbell up toward the shoulders.",
        None,
        None,
        Equipment.BARBELL,
        Difficulty.BEGINNER,
        [("biceps", MuscleRole.PRIMARY)],
    ),
    (
        "Curl martillo",
        "Hammer curl",
        "Curl con agarre neutro para bíceps y antebrazo.",
        "Neutral-grip curl for biceps and forearm.",
        None,
        None,
        Equipment.DUMBBELL,
        Difficulty.BEGINNER,
        [("biceps", MuscleRole.PRIMARY)],
    ),
    (
        "Curl en banco Scott",
        "Preacher curl",
        "Curl con el brazo apoyado para aislar el bíceps.",
        "Curl with the arm braced to isolate the biceps.",
        None,
        None,
        Equipment.MACHINE,
        Difficulty.INTERMEDIATE,
        [("biceps", MuscleRole.PRIMARY)],
    ),
    # Triceps
    (
        "Press francés con barra",
        "Barbell skull crusher",
        "Extensión de codos tumbado bajando la barra a la frente.",
        "Lying elbow extension lowering the bar to the forehead.",
        None,
        None,
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [("triceps", MuscleRole.PRIMARY)],
    ),
    (
        "Fondos en banco",
        "Bench dip",
        "Fondos apoyando las manos en un banco para el tríceps.",
        "Dips with hands on a bench to work the triceps.",
        None,
        None,
        Equipment.BODYWEIGHT,
        Difficulty.BEGINNER,
        [("triceps", MuscleRole.PRIMARY)],
    ),
    (
        "Press cerrado con barra",
        "Close-grip bench press",
        "Press de banca con agarre estrecho para el tríceps.",
        "Bench press with a narrow grip to bias the triceps.",
        None,
        None,
        Equipment.BARBELL,
        Difficulty.ADVANCED,
        [("triceps", MuscleRole.PRIMARY), ("chest", MuscleRole.SECONDARY)],
    ),
    # Abs
    (
        "Crunch abdominal",
        "Crunch",
        "Flexiona el tronco elevando los hombros del suelo.",
        "Curl the trunk lifting the shoulders off the floor.",
        None,
        None,
        Equipment.BODYWEIGHT,
        Difficulty.BEGINNER,
        [("abs", MuscleRole.PRIMARY)],
    ),
    (
        "Elevación de piernas colgado",
        "Hanging leg raise",
        "Eleva las piernas colgado de una barra.",
        "Raise the legs while hanging from a bar.",
        None,
        None,
        Equipment.BODYWEIGHT,
        Difficulty.ADVANCED,
        [("abs", MuscleRole.PRIMARY)],
    ),
    (
        "Crunch en polea",
        "Cable crunch",
        "Flexiona el tronco arrodillado tirando de la cuerda.",
        "Kneel and crunch the trunk pulling the rope down.",
        None,
        None,
        Equipment.CABLE,
        Difficulty.INTERMEDIATE,
        [("abs", MuscleRole.PRIMARY)],
    ),
    # Quads
    (
        "Prensa de piernas",
        "Leg press",
        "Empuja la plataforma con las piernas en la máquina.",
        "Push the platform away with the legs on the machine.",
        None,
        None,
        Equipment.MACHINE,
        Difficulty.BEGINNER,
        [("quads", MuscleRole.PRIMARY), ("glutes", MuscleRole.SECONDARY)],
    ),
    (
        "Zancadas con mancuernas",
        "Dumbbell lunge",
        "Da un paso al frente y flexiona ambas rodillas.",
        "Step forward and bend both knees under load.",
        None,
        None,
        Equipment.DUMBBELL,
        Difficulty.INTERMEDIATE,
        [("quads", MuscleRole.PRIMARY), ("glutes", MuscleRole.SECONDARY)],
    ),
    (
        "Extensión de cuádriceps en máquina",
        "Leg extension",
        "Extiende las rodillas contra la almohadilla de la máquina.",
        "Extend the knees against the machine pad.",
        None,
        None,
        Equipment.MACHINE,
        Difficulty.BEGINNER,
        [("quads", MuscleRole.PRIMARY)],
    ),
    (
        "Sentadilla goblet",
        "Goblet squat",
        "Sentadilla sujetando una mancuerna contra el pecho.",
        "Squat holding a dumbbell against the chest.",
        None,
        None,
        Equipment.DUMBBELL,
        Difficulty.BEGINNER,
        [("quads", MuscleRole.PRIMARY), ("glutes", MuscleRole.SECONDARY)],
    ),
    # Hamstrings
    (
        "Curl femoral en máquina",
        "Lying leg curl",
        "Flexiona las rodillas contra la máquina tumbado.",
        "Curl the knees against the machine while lying down.",
        None,
        None,
        Equipment.MACHINE,
        Difficulty.BEGINNER,
        [("hamstrings", MuscleRole.PRIMARY)],
    ),
    (
        "Peso muerto rumano con mancuernas",
        "Dumbbell Romanian deadlift",
        "Bisagra de cadera con mancuernas para isquios y glúteo.",
        "Hip-hinge with dumbbells for hamstrings and glutes.",
        None,
        None,
        Equipment.DUMBBELL,
        Difficulty.BEGINNER,
        [("hamstrings", MuscleRole.PRIMARY), ("glutes", MuscleRole.SECONDARY)],
    ),
    (
        "Buenos días con barra",
        "Barbell good morning",
        "Bisagra de cadera con la barra sobre la espalda alta.",
        "Hip-hinge with the barbell across the upper back.",
        None,
        None,
        Equipment.BARBELL,
        Difficulty.ADVANCED,
        [("hamstrings", MuscleRole.PRIMARY), ("glutes", MuscleRole.SECONDARY)],
    ),
    # Glutes
    (
        "Hip thrust con barra",
        "Barbell hip thrust",
        "Empuje de cadera con la espalda apoyada en un banco.",
        "Drive the hips up with the back on a bench.",
        None,
        None,
        Equipment.BARBELL,
        Difficulty.INTERMEDIATE,
        [("glutes", MuscleRole.PRIMARY), ("hamstrings", MuscleRole.SECONDARY)],
    ),
    (
        "Puente de glúteos",
        "Glute bridge",
        "Eleva la cadera desde el suelo apretando el glúteo.",
        "Lift the hips off the floor squeezing the glutes.",
        None,
        None,
        Equipment.BODYWEIGHT,
        Difficulty.BEGINNER,
        [("glutes", MuscleRole.PRIMARY)],
    ),
    (
        "Zancada búlgara",
        "Bulgarian split squat",
        "Sentadilla a una pierna con el pie trasero elevado.",
        "Single-leg squat with the rear foot elevated.",
        None,
        None,
        Equipment.DUMBBELL,
        Difficulty.ADVANCED,
        [("glutes", MuscleRole.PRIMARY), ("quads", MuscleRole.SECONDARY)],
    ),
]


# How-to steps (Spanish, English) keyed by the exercise's Spanish name. Provided
# for exercises without a demonstration video so every exercise has an example.
STEPS: dict[str, tuple[list[str], list[str]]] = {
    "Flexiones": (
        [
            "Colócate en plancha con las manos bajo los hombros.",
            "Baja el pecho flexionando los codos.",
            "Empuja hasta extender los brazos.",
        ],
        [
            "Start in a plank with your hands under the shoulders.",
            "Lower the chest by bending the elbows.",
            "Push up until the arms are extended.",
        ],
    ),
    "Press de banca con barra": (
        [
            "Túmbate en el banco con la barra a la altura de los ojos.",
            "Baja la barra al centro del pecho.",
            "Empuja hasta extender los brazos.",
        ],
        [
            "Lie on the bench with the bar over your eyes.",
            "Lower the bar to the mid-chest.",
            "Press up until the arms are extended.",
        ],
    ),
    "Dominadas": (
        [
            "Cuélgate de la barra con agarre prono.",
            "Tira hasta pasar la barbilla por encima de la barra.",
            "Baja controlando hasta estirar los brazos.",
        ],
        [
            "Hang from the bar with an overhand grip.",
            "Pull until your chin clears the bar.",
            "Lower under control until the arms straighten.",
        ],
    ),
    "Remo inclinado": (
        [
            "Inclina el torso con la espalda recta sujetando la barra.",
            "Rema la barra hacia el abdomen.",
            "Baja despacio hasta estirar los brazos.",
        ],
        [
            "Hinge the torso with a flat back holding the bar.",
            "Row the bar toward the abdomen.",
            "Lower slowly until the arms straighten.",
        ],
    ),
    "Press militar": (
        [
            "De pie, sujeta la barra a la altura de los hombros.",
            "Empuja la barra por encima de la cabeza.",
            "Baja controlando hasta los hombros.",
        ],
        [
            "Stand holding the bar at shoulder height.",
            "Press the bar overhead.",
            "Lower under control to the shoulders.",
        ],
    ),
    "Curl de bíceps con mancuernas": (
        [
            "De pie con una mancuerna en cada mano, palmas al frente.",
            "Flexiona los codos subiendo las mancuernas.",
            "Baja despacio hasta estirar los brazos.",
        ],
        [
            "Stand with a dumbbell in each hand, palms forward.",
            "Curl the dumbbells up by bending the elbows.",
            "Lower slowly to a stretch.",
        ],
    ),
    "Extensión de tríceps en polea": (
        [
            "Sujeta la cuerda en la polea alta con los codos pegados.",
            "Extiende los codos empujando hacia abajo.",
            "Sube despacio controlando el peso.",
        ],
        [
            "Grab the rope on the high pulley with elbows tucked.",
            "Extend the elbows pushing down.",
            "Return slowly, controlling the weight.",
        ],
    ),
    "Plancha": (
        [
            "Apóyate sobre los antebrazos y las puntas de los pies.",
            "Mantén el cuerpo recto sin hundir la cadera.",
            "Aguanta la posición respirando de forma controlada.",
        ],
        [
            "Rest on your forearms and toes.",
            "Keep the body straight without dropping the hips.",
            "Hold the position, breathing steadily.",
        ],
    ),
    "Sentadilla con barra": (
        [
            "Coloca la barra sobre la espalda alta, pies a la anchura de los hombros.",
            "Baja flexionando caderas y rodillas con la espalda recta.",
            "Sube empujando con los talones.",
        ],
        [
            "Place the bar on the upper back, feet shoulder-width apart.",
            "Lower by bending the hips and knees with a flat back.",
            "Stand up driving through the heels.",
        ],
    ),
    "Peso muerto rumano": (
        [
            "De pie con la barra delante de los muslos.",
            "Lleva la cadera atrás bajando la barra pegada a las piernas.",
            "Vuelve extendiendo la cadera y apretando glúteos.",
        ],
        [
            "Stand with the bar in front of the thighs.",
            "Push the hips back, lowering the bar along the legs.",
            "Return by extending the hips and squeezing the glutes.",
        ],
    ),
    "Press inclinado con mancuernas": (
        [
            "Túmbate en un banco inclinado a 30-45° con una mancuerna en cada mano.",
            "Baja las mancuernas de forma controlada hasta la parte alta del pecho.",
            "Empuja hacia arriba hasta extender los codos sin bloquearlos.",
        ],
        [
            "Lie on a 30-45° incline bench holding a dumbbell in each hand.",
            "Lower the dumbbells under control to the upper chest.",
            "Press up until the elbows are extended but not locked.",
        ],
    ),
    "Aperturas con mancuernas": (
        [
            "Túmbate en banco plano con las mancuernas sobre el pecho y codos algo flexionados.",
            "Abre los brazos en arco hasta notar estiramiento en el pecho.",
            "Junta las mancuernas arriba siguiendo el mismo arco.",
        ],
        [
            "Lie on a flat bench with the dumbbells over the chest, elbows slightly bent.",
            "Open the arms in an arc until you feel a chest stretch.",
            "Bring the dumbbells back together along the same arc.",
        ],
    ),
    "Fondos en paralelas": (
        [
            "Sujétate en las paralelas con los brazos extendidos e inclina el torso al frente.",
            "Baja flexionando los codos hasta notar estiramiento en el pecho.",
            "Empuja hacia arriba hasta extender los brazos.",
        ],
        [
            "Support yourself on parallel bars with arms extended and torso leaning forward.",
            "Lower by bending the elbows until you feel a chest stretch.",
            "Press back up until the arms are extended.",
        ],
    ),
    "Cruce de poleas": (
        [
            "Coloca las poleas altas y agarra un asa en cada mano, un pie adelantado.",
            "Con los codos ligeramente flexionados, junta las manos delante del pecho.",
            "Vuelve despacio controlando la apertura.",
        ],
        [
            "Set the pulleys high and grab a handle in each hand, one foot forward.",
            "With elbows slightly bent, bring both hands together in front of the chest.",
            "Return slowly, controlling the stretch.",
        ],
    ),
    "Jalón al pecho en polea": (
        [
            "Siéntate y sujeta la barra con agarre ancho, muslos fijados bajo el rodillo.",
            "Tira de la barra hacia la parte alta del pecho llevando los codos abajo.",
            "Sube la barra de forma controlada hasta extender los brazos.",
        ],
        [
            "Sit and grip the bar wide, thighs secured under the pad.",
            "Pull the bar to the upper chest, driving the elbows down.",
            "Let the bar rise under control until the arms extend.",
        ],
    ),
    "Remo con mancuerna a una mano": (
        [
            "Apoya una rodilla y una mano en un banco, la mancuerna cuelga en la otra mano.",
            "Rema la mancuerna hacia la cadera llevando el codo atrás.",
            "Baja despacio hasta estirar el brazo.",
        ],
        [
            "Place one knee and hand on a bench, the dumbbell hanging in the other hand.",
            "Row the dumbbell toward the hip, driving the elbow back.",
            "Lower slowly until the arm is straight.",
        ],
    ),
    "Pullover con mancuerna": (
        [
            "Túmbate en un banco con una mancuerna sujeta con ambas manos sobre el pecho.",
            "Lleva la mancuerna por detrás de la cabeza con los brazos casi rectos.",
            "Devuélvela sobre el pecho contrayendo la espalda.",
        ],
        [
            "Lie on a bench holding one dumbbell with both hands over the chest.",
            "Take the dumbbell behind the head with arms nearly straight.",
            "Pull it back over the chest, contracting the back.",
        ],
    ),
    "Encogimientos con barra": (
        [
            "De pie, sujeta la barra con las manos a la anchura de los hombros.",
            "Eleva los hombros hacia las orejas sin flexionar los codos.",
            "Baja despacio hasta estirar del todo.",
        ],
        [
            "Stand holding the bar with hands shoulder-width apart.",
            "Shrug the shoulders toward the ears without bending the elbows.",
            "Lower slowly to a full stretch.",
        ],
    ),
    "Remo al mentón": (
        [
            "De pie, sujeta la barra con agarre estrecho delante de los muslos.",
            "Tira de la barra hacia la barbilla llevando los codos altos.",
            "Baja controlando el movimiento.",
        ],
        [
            "Stand holding the bar with a narrow grip in front of the thighs.",
            "Pull the bar toward the chin, keeping the elbows high.",
            "Lower under control.",
        ],
    ),
    "Face pull en polea": (
        [
            "Coloca la polea a la altura de la cara y agarra la cuerda con ambas manos.",
            "Tira de la cuerda hacia la frente separando las manos y abriendo los codos.",
            "Vuelve despacio a la posición inicial.",
        ],
        [
            "Set the pulley at face height and grab the rope with both hands.",
            "Pull the rope toward the forehead, spreading the hands and flaring the elbows.",
            "Return slowly to the start.",
        ],
    ),
    "Elevaciones laterales con mancuernas": (
        [
            "De pie, una mancuerna en cada mano a los lados y codos ligeramente flexionados.",
            "Eleva los brazos a los lados hasta la altura de los hombros.",
            "Baja despacio sin coger impulso.",
        ],
        [
            "Stand with a dumbbell in each hand at your sides, elbows slightly bent.",
            "Raise the arms out to the sides up to shoulder height.",
            "Lower slowly without swinging.",
        ],
    ),
    "Press de hombros con mancuernas": (
        [
            "Sentado, sube las mancuernas a la altura de los hombros con las palmas al frente.",
            "Empuja hacia arriba hasta casi extender los codos.",
            "Baja controlando hasta los hombros.",
        ],
        [
            "Seated, bring the dumbbells to shoulder height, palms facing forward.",
            "Press overhead until the elbows are nearly extended.",
            "Lower under control back to the shoulders.",
        ],
    ),
    "Pájaros con mancuernas": (
        [
            "Inclina el torso hacia delante con una mancuerna en cada mano colgando.",
            "Abre los brazos hacia los lados apretando la parte posterior del hombro.",
            "Baja despacio a la posición inicial.",
        ],
        [
            "Hinge the torso forward with a dumbbell hanging in each hand.",
            "Open the arms out to the sides, squeezing the rear delts.",
            "Lower slowly to the start.",
        ],
    ),
    "Curl con barra": (
        [
            "De pie, sujeta la barra con agarre supino a la anchura de los hombros.",
            "Flexiona los codos subiendo la barra hacia los hombros sin mover los codos.",
            "Baja despacio hasta estirar los brazos.",
        ],
        [
            "Stand holding the bar with an underhand, shoulder-width grip.",
            "Curl the bar toward the shoulders without moving the elbows.",
            "Lower slowly until the arms are straight.",
        ],
    ),
    "Curl martillo": (
        [
            "De pie, una mancuerna en cada mano con las palmas mirándose (agarre neutro).",
            "Flexiona los codos subiendo las mancuernas sin girar las muñecas.",
            "Baja controlando el movimiento.",
        ],
        [
            "Stand with a dumbbell in each hand, palms facing each other (neutral grip).",
            "Curl the dumbbells up without rotating the wrists.",
            "Lower under control.",
        ],
    ),
    "Curl en banco Scott": (
        [
            "Apoya la parte posterior de los brazos en el banco Scott y sujeta la barra.",
            "Flexiona los codos subiendo el peso hacia los hombros.",
            "Baja despacio sin extender del todo de golpe.",
        ],
        [
            "Rest the back of the arms on the preacher pad and hold the bar or dumbbell.",
            "Curl the weight up toward the shoulders.",
            "Lower slowly without snapping the elbows straight.",
        ],
    ),
    "Press francés con barra": (
        [
            "Túmbate en un banco y sujeta la barra con los brazos extendidos sobre el pecho.",
            "Flexiona solo los codos bajando la barra hacia la frente.",
            "Extiende los codos hasta la posición inicial.",
        ],
        [
            "Lie on a bench holding the bar with arms extended over the chest.",
            "Bend only the elbows, lowering the bar toward the forehead.",
            "Extend the elbows back to the start.",
        ],
    ),
    "Fondos en banco": (
        [
            "Apoya las manos en el borde de un banco con las piernas extendidas al frente.",
            "Baja flexionando los codos hacia atrás.",
            "Empuja hacia arriba hasta extender los brazos.",
        ],
        [
            "Place your hands on the edge of a bench with legs extended forward.",
            "Lower by bending the elbows backward.",
            "Press up until the arms are extended.",
        ],
    ),
    "Press cerrado con barra": (
        [
            "Túmbate en un banco y sujeta la barra con las manos a la anchura de los hombros.",
            "Baja la barra al pecho manteniendo los codos cerca del cuerpo.",
            "Empuja hacia arriba hasta extender los brazos.",
        ],
        [
            "Lie on a bench and grip the bar shoulder-width apart.",
            "Lower the bar to the chest keeping the elbows close to the body.",
            "Press up until the arms are extended.",
        ],
    ),
    "Crunch abdominal": (
        [
            "Túmbate boca arriba con las rodillas flexionadas y las manos en la nuca.",
            "Eleva los hombros del suelo acercando las costillas a la cadera.",
            "Baja despacio sin apoyar del todo la cabeza.",
        ],
        [
            "Lie on your back with knees bent and hands by your head.",
            "Lift the shoulders off the floor, bringing the ribs toward the hips.",
            "Lower slowly without fully resting the head.",
        ],
    ),
    "Elevación de piernas colgado": (
        [
            "Cuélgate de una barra con los brazos extendidos.",
            "Eleva las piernas rectas o con rodillas flexionadas hacia arriba.",
            "Baja despacio sin balancearte.",
        ],
        [
            "Hang from a bar with arms extended.",
            "Raise the legs (straight or with bent knees) upward.",
            "Lower slowly without swinging.",
        ],
    ),
    "Crunch en polea": (
        [
            "Arrodíllate frente a la polea alta sujetando la cuerda junto a la cabeza.",
            "Flexiona el tronco llevando los codos hacia los muslos.",
            "Sube despacio controlando el peso.",
        ],
        [
            "Kneel in front of the high pulley holding the rope by your head.",
            "Crunch the torso, bringing the elbows toward the thighs.",
            "Rise slowly, controlling the weight.",
        ],
    ),
    "Prensa de piernas": (
        [
            "Siéntate en la máquina con los pies a la anchura de las caderas en la plataforma.",
            "Baja la plataforma flexionando las rodillas hasta unos 90°.",
            "Empuja hasta casi extender las piernas sin bloquear.",
        ],
        [
            "Sit in the machine with feet hip-width on the platform.",
            "Lower the platform by bending the knees to about 90°.",
            "Push until the legs are nearly extended without locking.",
        ],
    ),
    "Zancadas con mancuernas": (
        [
            "De pie con una mancuerna en cada mano, da un paso largo al frente.",
            "Baja flexionando ambas rodillas hasta que la trasera casi toque el suelo.",
            "Empuja con la pierna delantera para volver y alterna.",
        ],
        [
            "Stand with a dumbbell in each hand and take a long step forward.",
            "Lower by bending both knees until the rear one nearly touches the floor.",
            "Push through the front leg to return, then alternate.",
        ],
    ),
    "Extensión de cuádriceps en máquina": (
        [
            "Siéntate en la máquina con el rodillo sobre los tobillos.",
            "Extiende las rodillas hasta estirar las piernas.",
            "Baja despacio controlando el peso.",
        ],
        [
            "Sit in the machine with the pad on your ankles.",
            "Extend the knees until the legs are straight.",
            "Lower slowly, controlling the weight.",
        ],
    ),
    "Sentadilla goblet": (
        [
            "Sujeta una mancuerna verticalmente contra el pecho con ambas manos.",
            "Baja en sentadilla manteniendo la espalda recta y el pecho alto.",
            "Sube empujando con los talones.",
        ],
        [
            "Hold a dumbbell vertically against the chest with both hands.",
            "Squat down keeping the back straight and chest up.",
            "Stand up driving through the heels.",
        ],
    ),
    "Curl femoral en máquina": (
        [
            "Túmbate boca abajo en la máquina con el rodillo sobre los talones.",
            "Flexiona las rodillas llevando los talones hacia los glúteos.",
            "Baja despacio hasta estirar.",
        ],
        [
            "Lie face down on the machine with the pad on your heels.",
            "Curl the knees, bringing the heels toward the glutes.",
            "Lower slowly to a stretch.",
        ],
    ),
    "Peso muerto rumano con mancuernas": (
        [
            "De pie con una mancuerna en cada mano delante de los muslos.",
            "Lleva la cadera atrás bajando las mancuernas pegadas a las piernas.",
            "Vuelve extendiendo la cadera y apretando glúteos.",
        ],
        [
            "Stand with a dumbbell in each hand in front of the thighs.",
            "Push the hips back, lowering the dumbbells along the legs.",
            "Return by extending the hips and squeezing the glutes.",
        ],
    ),
    "Buenos días con barra": (
        [
            "Coloca la barra sobre la espalda alta, pies a la anchura de las caderas.",
            "Lleva la cadera atrás inclinando el torso con la espalda recta.",
            "Vuelve extendiendo la cadera hasta ponerte erguido.",
        ],
        [
            "Place the bar across the upper back, feet hip-width apart.",
            "Push the hips back, hinging the torso with a flat back.",
            "Return by extending the hips to stand tall.",
        ],
    ),
    "Hip thrust con barra": (
        [
            "Apoya la espalda alta en un banco con la barra sobre la cadera.",
            "Empuja la cadera hacia arriba hasta alinear torso y muslos.",
            "Baja despacio sin apoyar del todo.",
        ],
        [
            "Rest the upper back on a bench with the bar over the hips.",
            "Drive the hips up until torso and thighs are aligned.",
            "Lower slowly without fully resting.",
        ],
    ),
    "Puente de glúteos": (
        [
            "Túmbate boca arriba con las rodillas flexionadas y los pies apoyados.",
            "Eleva la cadera apretando los glúteos hasta alinear el cuerpo.",
            "Baja despacio a la posición inicial.",
        ],
        [
            "Lie on your back with knees bent and feet flat.",
            "Lift the hips, squeezing the glutes until the body is aligned.",
            "Lower slowly to the start.",
        ],
    ),
    "Zancada búlgara": (
        [
            "Apoya el empeine del pie trasero en un banco, mancuernas en las manos.",
            "Baja flexionando la rodilla delantera manteniendo el torso erguido.",
            "Empuja con la pierna delantera para subir.",
        ],
        [
            "Place the top of the rear foot on a bench, dumbbells in hands.",
            "Lower by bending the front knee, keeping the torso upright.",
            "Push through the front leg to rise.",
        ],
    ),
}


# Demonstration videos for previously video-less exercises, keyed by Spanish
# name → YouTube id. English-language tutorials verified as public/embeddable;
# stored in the default video slot so both locales get the video (subtitles are
# forced to the UI language by the player).
VIDEOS: dict[str, str] = {
    "Pullover con mancuerna": "tpLnfSQJ0gg",
    "Remo al mentón": "amCU-ziHITM",
    "Encogimientos con barra": "KbsQ1E8Hg0o",
    "Peso muerto rumano con mancuernas": "aa57T45iFSE",
    "Press inclinado con mancuernas": "PEiIOW7HGnA",
    "Aperturas con mancuernas": "eozdVDA78K0",
    "Fondos en paralelas": "2z8JmcrW-As",
    "Cruce de poleas": "taI4XduLpTk",
    "Jalón al pecho en polea": "CAwf7n6Luuc",
    "Remo con mancuerna a una mano": "pYcpY20QaE8",
    "Face pull en polea": "eIq5CB9JfKE",
    "Elevaciones laterales con mancuernas": "3VcKaXpzqRo",
    "Press de hombros con mancuernas": "qEwKCR5JCog",
    "Pájaros con mancuernas": "EA7u4Q_8HQ0",
    "Curl con barra": "kwG2ipFRgfo",
    "Curl martillo": "zC3nLlEvin4",
    "Curl en banco Scott": "fIWP-FRFNU0",
    "Press francés con barra": "d_KZxkY_0cM",
    "Fondos en banco": "c3ZGl4pAwZ4",
    "Press cerrado con barra": "nEF0bv2FW94",
    "Crunch abdominal": "Xyd_fa5zoEU",
    "Elevación de piernas colgado": "Pr1ieGZ5atk",
    "Crunch en polea": "AV5PmZJIrrw",
    "Prensa de piernas": "IZxyjW7MPJQ",
    "Zancadas con mancuernas": "D7KaRcUTQeE",
    "Extensión de cuádriceps en máquina": "YyvSfVjQeL0",
    "Sentadilla goblet": "MeIiIdhvXT4",
    "Curl femoral en máquina": "1Tq3QdYUuHs",
    "Buenos días con barra": "vKPGe8zb2S4",
    "Hip thrust con barra": "LM8XHLYJoYs",
    "Puente de glúteos": "wPM8icPu6H8",
    "Zancada búlgara": "2C-uNgKwPLE",
}


# Nutrition catalog per 100 g:
# (name_es, name_en, emoji, category, kcal, protein_g, carbs_g, fat_g, tags)
# fmt: off
FOODS: list[tuple[str, str, str, str, float, float, float, float, list[str]]] = [
    ("Pechuga de pollo", "Chicken breast", "🍗", "protein", 165, 31, 0, 3.6, ["high_protein", "gluten_free"]),
    ("Muslo de pollo", "Chicken thigh", "🍗", "protein", 209, 26, 0, 11, ["high_protein", "gluten_free"]),
    ("Pechuga de pavo", "Turkey breast", "🦃", "protein", 135, 30, 0, 1, ["high_protein", "gluten_free"]),
    ("Huevo", "Egg", "🥚", "protein", 155, 13, 1.1, 11, ["vegetarian", "gluten_free", "high_protein"]),
    ("Clara de huevo", "Egg white", "🥚", "protein", 52, 11, 0.7, 0.2, ["vegetarian", "gluten_free", "high_protein"]),
    ("Salmón", "Salmon", "🐟", "protein", 208, 20, 0, 13, ["gluten_free", "high_protein"]),
    ("Atún", "Tuna", "🐟", "protein", 132, 28, 0, 1, ["gluten_free", "high_protein"]),
    ("Bacalao", "Cod", "🐟", "protein", 82, 18, 0, 0.7, ["gluten_free", "high_protein"]),
    ("Gambas", "Shrimp", "🦐", "protein", 99, 24, 0.2, 0.3, ["gluten_free", "high_protein"]),
    ("Ternera magra", "Lean beef", "🥩", "protein", 187, 26, 0, 9, ["gluten_free", "high_protein"]),
    ("Lomo de cerdo", "Pork loin", "🥩", "protein", 143, 21, 0, 6, ["gluten_free", "high_protein"]),
    ("Jamón cocido", "Lean ham", "🍖", "protein", 145, 21, 1.5, 6, ["gluten_free", "high_protein"]),
    ("Tofu", "Tofu", "🌱", "protein", 144, 15, 3, 8, ["vegan", "vegetarian", "gluten_free", "high_protein"]),
    ("Tempeh", "Tempeh", "🌱", "protein", 192, 20, 8, 11, ["vegan", "vegetarian", "high_protein"]),
    ("Seitán", "Seitan", "🌱", "protein", 370, 75, 14, 2, ["vegan", "vegetarian", "high_protein"]),
    ("Lentejas", "Lentils", "🫘", "protein", 116, 9, 20, 0.4, ["vegan", "vegetarian", "gluten_free"]),
    ("Garbanzos", "Chickpeas", "🫘", "protein", 164, 9, 27, 2.6, ["vegan", "vegetarian", "gluten_free"]),
    ("Alubias negras", "Black beans", "🫘", "protein", 132, 9, 24, 0.5, ["vegan", "vegetarian", "gluten_free"]),
    ("Judías rojas", "Kidney beans", "🫘", "protein", 127, 9, 22, 0.5, ["vegan", "vegetarian", "gluten_free"]),
    ("Edamame", "Edamame", "🫛", "protein", 121, 12, 9, 5, ["vegan", "vegetarian", "gluten_free", "high_protein"]),
    ("Yogur griego", "Greek yogurt", "🥛", "dairy", 59, 10, 3.6, 0.4, ["vegetarian", "gluten_free", "high_protein"]),
    ("Queso fresco batido", "Cottage cheese", "🧀", "dairy", 98, 11, 3.4, 4.3, ["vegetarian", "gluten_free", "high_protein"]),
    ("Leche", "Milk", "🥛", "dairy", 61, 3.2, 4.8, 3.3, ["vegetarian", "gluten_free"]),
    ("Leche desnatada", "Skimmed milk", "🥛", "dairy", 34, 3.4, 5, 0.1, ["vegetarian", "gluten_free"]),
    ("Queso curado", "Cheddar cheese", "🧀", "dairy", 402, 25, 1.3, 33, ["vegetarian", "gluten_free", "high_protein"]),
    ("Mozzarella", "Mozzarella", "🧀", "dairy", 280, 28, 3.1, 17, ["vegetarian", "gluten_free", "high_protein"]),
    ("Mantequilla", "Butter", "🧈", "dairy", 717, 0.9, 0.1, 81, ["vegetarian", "gluten_free"]),
    ("Arroz blanco", "White rice", "🍚", "carb", 130, 2.7, 28, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Arroz integral", "Brown rice", "🍚", "carb", 111, 2.6, 23, 0.9, ["vegan", "vegetarian", "gluten_free"]),
    ("Avena", "Oats", "🌾", "carb", 389, 17, 66, 7, ["vegan", "vegetarian"]),
    ("Pan integral", "Whole-wheat bread", "🍞", "carb", 247, 13, 41, 3.4, ["vegan", "vegetarian"]),
    ("Pan blanco", "White bread", "🍞", "carb", 265, 9, 49, 3.2, ["vegan", "vegetarian"]),
    ("Patata", "Potato", "🥔", "carb", 77, 2, 17, 0.1, ["vegan", "vegetarian", "gluten_free"]),
    ("Boniato", "Sweet potato", "🍠", "carb", 86, 1.6, 20, 0.1, ["vegan", "vegetarian", "gluten_free"]),
    ("Pasta", "Pasta", "🍝", "carb", 158, 6, 31, 0.9, ["vegetarian", "vegan"]),
    ("Quinoa", "Quinoa", "🌾", "carb", 120, 4.4, 21, 1.9, ["vegan", "vegetarian", "gluten_free"]),
    ("Cuscús", "Couscous", "🌾", "carb", 112, 3.8, 23, 0.2, ["vegan", "vegetarian"]),
    ("Maíz", "Corn", "🌽", "carb", 96, 3.4, 21, 1.5, ["vegan", "vegetarian", "gluten_free"]),
    ("Brócoli", "Broccoli", "🥦", "vegetable", 34, 2.8, 7, 0.4, ["vegan", "vegetarian", "gluten_free"]),
    ("Coliflor", "Cauliflower", "🥦", "vegetable", 25, 1.9, 5, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Espinacas", "Spinach", "🥬", "vegetable", 23, 2.9, 3.6, 0.4, ["vegan", "vegetarian", "gluten_free"]),
    ("Lechuga", "Lettuce", "🥬", "vegetable", 15, 1.4, 2.9, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Pepino", "Cucumber", "🥒", "vegetable", 15, 0.7, 3.6, 0.1, ["vegan", "vegetarian", "gluten_free"]),
    ("Calabacín", "Zucchini", "🥒", "vegetable", 17, 1.2, 3.1, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Tomate", "Tomato", "🍅", "vegetable", 18, 0.9, 3.9, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Zanahoria", "Carrot", "🥕", "vegetable", 41, 0.9, 10, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Pimiento", "Bell pepper", "🫑", "vegetable", 31, 1, 6, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Cebolla", "Onion", "🧅", "vegetable", 40, 1.1, 9, 0.1, ["vegan", "vegetarian", "gluten_free"]),
    ("Champiñón", "Mushroom", "🍄", "vegetable", 22, 3.1, 3.3, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Berenjena", "Eggplant", "🍆", "vegetable", 25, 1, 6, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Judías verdes", "Green beans", "🫛", "vegetable", 31, 1.8, 7, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Guisantes", "Peas", "🫛", "vegetable", 81, 5, 14, 0.4, ["vegan", "vegetarian", "gluten_free"]),
    ("Ajo", "Garlic", "🧄", "vegetable", 149, 6.4, 33, 0.5, ["vegan", "vegetarian", "gluten_free"]),
    ("Espárragos", "Asparagus", "🥬", "vegetable", 20, 2.2, 3.9, 0.1, ["vegan", "vegetarian", "gluten_free"]),
    ("Plátano", "Banana", "🍌", "fruit", 89, 1.1, 23, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Manzana", "Apple", "🍎", "fruit", 52, 0.3, 14, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Naranja", "Orange", "🍊", "fruit", 47, 0.9, 12, 0.1, ["vegan", "vegetarian", "gluten_free"]),
    ("Fresa", "Strawberry", "🍓", "fruit", 32, 0.7, 7.7, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Sandía", "Watermelon", "🍉", "fruit", 30, 0.6, 7.6, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Uvas", "Grapes", "🍇", "fruit", 69, 0.7, 18, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Piña", "Pineapple", "🍍", "fruit", 50, 0.5, 13, 0.1, ["vegan", "vegetarian", "gluten_free"]),
    ("Mango", "Mango", "🥭", "fruit", 60, 0.8, 15, 0.4, ["vegan", "vegetarian", "gluten_free"]),
    ("Arándanos", "Blueberries", "🫐", "fruit", 57, 0.7, 14, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Pera", "Pear", "🍐", "fruit", 57, 0.4, 15, 0.1, ["vegan", "vegetarian", "gluten_free"]),
    ("Melocotón", "Peach", "🍑", "fruit", 39, 0.9, 10, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Kiwi", "Kiwi", "🥝", "fruit", 61, 1.1, 15, 0.5, ["vegan", "vegetarian", "gluten_free"]),
    ("Melón", "Melon", "🍈", "fruit", 34, 0.8, 8, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Limón", "Lemon", "🍋", "fruit", 29, 1.1, 9, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Aguacate", "Avocado", "🥑", "fat", 160, 2, 9, 15, ["vegan", "vegetarian", "gluten_free"]),
    ("Almendras", "Almonds", "🥜", "fat", 579, 21, 22, 50, ["vegan", "vegetarian", "gluten_free", "high_protein"]),
    ("Nueces", "Walnuts", "🥜", "fat", 654, 15, 14, 65, ["vegan", "vegetarian", "gluten_free"]),
    ("Anacardos", "Cashews", "🥜", "fat", 553, 18, 30, 44, ["vegan", "vegetarian", "gluten_free"]),
    ("Mantequilla de cacahuete", "Peanut butter", "🥜", "fat", 588, 25, 20, 50, ["vegan", "vegetarian", "high_protein"]),
    ("Aceite de oliva", "Olive oil", "🫒", "fat", 884, 0, 0, 100, ["vegan", "vegetarian", "gluten_free"]),
    ("Semillas de chía", "Chia seeds", "🌰", "fat", 486, 17, 42, 31, ["vegan", "vegetarian", "gluten_free"]),
    ("Chocolate negro", "Dark chocolate", "🍫", "fat", 546, 5, 61, 31, ["vegetarian", "gluten_free"]),
    # --- Added 2026-07-27: common gaps found while testing the meal-photo feature ---
    ("Calabaza", "Pumpkin", "🎃", "vegetable", 26, 1, 6.5, 0.1, ["vegan", "vegetarian", "gluten_free"]),
    ("Setas", "Mushrooms", "🍄", "vegetable", 22, 3.1, 3.3, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Puerro", "Leek", "🥬", "vegetable", 61, 1.5, 14, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Apio", "Celery", "🥬", "vegetable", 16, 0.7, 3, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Remolacha", "Beetroot", "🥬", "vegetable", 43, 1.6, 10, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Col", "Cabbage", "🥬", "vegetable", 25, 1.3, 6, 0.1, ["vegan", "vegetarian", "gluten_free"]),
    ("Alcachofa", "Artichoke", "🥬", "vegetable", 47, 3.3, 11, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Rúcula", "Rocket", "🥬", "vegetable", 25, 2.6, 3.7, 0.7, ["vegan", "vegetarian", "gluten_free"]),
    ("Aceituna", "Olives", "🫒", "fat", 145, 1, 3.8, 15, ["vegan", "vegetarian", "gluten_free"]),
    ("Sardina", "Sardine", "🐟", "protein", 208, 25, 0, 11, ["gluten_free", "high_protein"]),
    ("Merluza", "Hake", "🐟", "protein", 90, 18, 0, 2, ["gluten_free", "high_protein"]),
    ("Caballa", "Mackerel", "🐟", "protein", 205, 19, 0, 14, ["gluten_free", "high_protein"]),
    ("Trucha", "Trout", "🐟", "protein", 148, 21, 0, 7, ["gluten_free", "high_protein"]),
    ("Mejillón", "Mussels", "🦪", "protein", 86, 12, 3.7, 2.2, ["gluten_free", "high_protein"]),
    ("Calamar", "Squid", "🦑", "protein", 92, 16, 3.1, 1.4, ["gluten_free", "high_protein"]),
    ("Pulpo", "Octopus", "🐙", "protein", 82, 15, 2.2, 1, ["gluten_free", "high_protein"]),
    ("Conejo", "Rabbit", "🍖", "protein", 173, 33, 0, 3.5, ["gluten_free", "high_protein"]),
    ("Cordero", "Lamb", "🍖", "protein", 258, 25, 0, 17, ["gluten_free", "high_protein"]),
    ("Salchicha", "Sausage", "🌭", "protein", 301, 12, 3, 27, ["gluten_free"]),
    ("Beicon", "Bacon", "🥓", "protein", 541, 37, 1.4, 42, ["gluten_free", "high_protein"]),
    ("Soja texturizada", "Textured soy protein", "🌱", "protein", 336, 52, 30, 1.5, ["vegan", "vegetarian", "high_protein"]),
    ("Requesón", "Cottage cheese", "🧀", "dairy", 98, 11, 3.4, 4.3, ["vegetarian", "gluten_free", "high_protein"]),
    ("Kéfir", "Kefir", "🥛", "dairy", 55, 3.3, 4.5, 2.5, ["vegetarian", "gluten_free"]),
    ("Queso feta", "Feta cheese", "🧀", "dairy", 264, 14, 4.1, 21, ["vegetarian", "gluten_free"]),
    ("Bebida de soja", "Soy milk", "🥛", "dairy", 43, 3.3, 2.6, 1.8, ["vegan", "vegetarian", "gluten_free"]),
    ("Arroz de sushi", "Sushi rice", "🍚", "carb", 130, 2.4, 29, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Tortilla de maíz", "Corn tortilla", "🫓", "carb", 218, 5.7, 45, 2.9, ["vegan", "vegetarian", "gluten_free"]),
    ("Pan de centeno", "Rye bread", "🍞", "carb", 259, 8.5, 48, 3.3, ["vegan", "vegetarian"]),
    ("Yuca", "Cassava", "🥔", "carb", 160, 1.4, 38, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Cereales integrales", "Whole grain cereal", "🥣", "carb", 379, 10, 68, 5, ["vegetarian"]),
    ("Cerezas", "Cherries", "🍒", "fruit", 63, 1.1, 16, 0.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Higo", "Fig", "🫐", "fruit", 74, 0.8, 19, 0.3, ["vegan", "vegetarian", "gluten_free"]),
    ("Granada", "Pomegranate", "🍎", "fruit", 83, 1.7, 19, 1.2, ["vegan", "vegetarian", "gluten_free"]),
    ("Frambuesa", "Raspberry", "🫐", "fruit", 52, 1.2, 12, 0.7, ["vegan", "vegetarian", "gluten_free"]),
    ("Dátil", "Date", "🌴", "fruit", 282, 2.5, 75, 0.4, ["vegan", "vegetarian", "gluten_free"]),
]
# fmt: on


# Demo accounts, so the app can be tried without credentials (they are shown in
# the sign-in form). They only ever hold demo data; there is no public sign-up,
# so these are the only accounts that exist. (name, email, role)
DEMO_USERS: list[tuple[str, str, UserRole]] = [
    ("Ana López", "entrenador@demo.muscleapp", UserRole.TRAINER),
    ("Javier M.", "alumno@demo.muscleapp", UserRole.CLIENT),
]


@dataclass(frozen=True)
class _TrainerSeed:
    """A trainer on offer. Only the advertised one can sign in."""

    name: str
    email: str
    specialty: Goal
    rating: float
    price_per_month: int
    bio: str
    bio_en: str


# The first is the demo account; the rest exist so a student has a real choice.
DEMO_TRAINERS: list[_TrainerSeed] = [
    _TrainerSeed(
        name="Ana López",
        email="entrenador@demo.muscleapp",
        specialty=Goal.STRENGTH,
        rating=4.9,
        price_per_month=39,
        bio="Fuerza y técnica. Progresiones medidas, sin prisa.",
        bio_en="Strength and technique. Measured progressions, no rush.",
    ),
    _TrainerSeed(
        name="Marco Ruiz",
        email="marco@demo.muscleapp",
        specialty=Goal.HYPERTROPHY,
        rating=4.8,
        price_per_month=45,
        bio="Hipertrofia con volumen ajustado a lo que puedas recuperar.",
        bio_en="Hypertrophy with the volume you can actually recover from.",
    ),
    _TrainerSeed(
        name="Sara Gil",
        email="sara@demo.muscleapp",
        specialty=Goal.FAT_LOSS,
        rating=5.0,
        price_per_month=35,
        bio="Pérdida de grasa sostenible: fuerza, cardio y hábitos.",
        bio_en="Sustainable fat loss: lifting, cardio and habits.",
    ),
    _TrainerSeed(
        name="Leo Torres",
        email="leo@demo.muscleapp",
        specialty=Goal.HYPERTROPHY,
        rating=4.7,
        price_per_month=29,
        bio="Rutinas sencillas para empezar y no abandonar.",
        bio_en="Simple routines to start with and stick to.",
    ),
]


@lru_cache(maxsize=2)
def _hash_once(password: str) -> str:
    """Argon2 is deliberately slow, so hash a given password once per process.

    The seed runs on every boot and, in the tests, once per case: hashing ten
    accounts each time was costing more than the rest of the seed together.
    """
    return Argon2Hasher().hash(password)


async def _seed_users(session: AsyncSession, password: str) -> int:
    """Insert the missing demo accounts and roster students, keyed by email.

    Hashing is deliberate work (Argon2), so it only happens when there is
    actually an account to create — not on every boot.
    """
    known = set((await session.scalars(select(UserModel.email))).all())
    advertised = {email for _, email, _ in DEMO_USERS}
    missing = [u for u in DEMO_USERS if u[1] not in known]
    # The rest of the roster exists only as data for the trainer's dashboard.
    # They are given a random password nobody holds, so the two advertised
    # accounts remain the only way into the app.
    roster = [
        (student.name, student.email, UserRole.CLIENT)
        for student in DEMO_STUDENTS
        if student.email not in known and student.email not in advertised
    ] + [
        (trainer.name, trainer.email, UserRole.TRAINER)
        for trainer in DEMO_TRAINERS
        if trainer.email not in known and trainer.email not in advertised
    ]
    if not missing and not roster:
        return 0
    demo_hash = _hash_once(password)
    # One unusable hash for the whole roster: they are data, not accounts, and
    # nobody holds the secret either way.
    locked_hash = _hash_once(secrets.token_urlsafe(32))
    rows = [
        {"name": name, "email": email, "role": role, "password_hash": demo_hash}
        for name, email, role in missing
    ] + [
        {"name": name, "email": email, "role": role, "password_hash": locked_hash}
        for name, email, role in roster
    ]
    # DO NOTHING on the email rather than trusting the read above: two sessions
    # can seed at once (the test fixtures do), and losing that race must not
    # raise — the row exists either way, which is all the caller needs.
    await session.execute(
        pg_insert(UserModel).on_conflict_do_nothing(index_elements=[UserModel.email]), rows
    )
    await session.commit()
    return len(rows)


@dataclass(frozen=True)
class _StudentSeed:
    """A demo student and the shape of the history generated for them.

    `lifts` are (English exercise name, starting kg, target reps, weekly gain),
    which is what turns into the strength curves of the trainer's dashboard.
    """

    name: str
    email: str
    age: int
    height_cm: int
    goal: Goal
    level: Difficulty
    start_weight_kg: float
    weekly_weight_delta: float  # body weight drift per week, signed
    adherence: float  # probability of showing up on a scheduled day
    lifts: tuple[tuple[str, float, int, float], ...]


# The first entry is the demo student anyone can sign in as; the rest exist only
# to give the trainer a roster worth charting.
DEMO_STUDENTS: list[_StudentSeed] = [
    _StudentSeed(
        name="Javier M.",
        email="alumno@demo.muscleapp",
        age=29,
        height_cm=178,
        goal=Goal.HYPERTROPHY,
        level=Difficulty.INTERMEDIATE,
        start_weight_kg=78.0,
        weekly_weight_delta=0.15,
        adherence=0.88,
        lifts=(
            ("Barbell bench press", 60.0, 8, 1.25),
            ("Barbell back squat", 80.0, 8, 1.75),
            ("Barbell curl", 25.0, 10, 0.4),
        ),
    ),
    _StudentSeed(
        name="Lucía P.",
        email="lucia@demo.muscleapp",
        age=34,
        height_cm=165,
        goal=Goal.FAT_LOSS,
        level=Difficulty.BEGINNER,
        start_weight_kg=72.0,
        weekly_weight_delta=-0.45,
        adherence=0.75,
        lifts=(
            ("Goblet squat", 12.0, 12, 0.6),
            ("Lat pulldown", 25.0, 12, 0.9),
            ("Plank", 0.0, 1, 0.0),
        ),
    ),
    _StudentSeed(
        name="Diego R.",
        email="diego@demo.muscleapp",
        age=41,
        height_cm=182,
        goal=Goal.STRENGTH,
        level=Difficulty.ADVANCED,
        start_weight_kg=88.0,
        weekly_weight_delta=0.05,
        adherence=0.94,
        lifts=(
            ("Barbell back squat", 120.0, 5, 2.0),
            ("Romanian deadlift", 100.0, 5, 2.0),
            ("Overhead press", 45.0, 5, 0.75),
        ),
    ),
    _StudentSeed(
        name="Marta S.",
        email="marta@demo.muscleapp",
        age=25,
        height_cm=170,
        goal=Goal.HYPERTROPHY,
        level=Difficulty.BEGINNER,
        start_weight_kg=61.0,
        weekly_weight_delta=0.2,
        adherence=0.8,
        lifts=(
            ("Leg press", 60.0, 12, 2.5),
            ("Lat pulldown", 30.0, 10, 1.0),
            ("Barbell curl", 15.0, 12, 0.3),
        ),
    ),
    _StudentSeed(
        name="Carlos V.",
        email="carlos@demo.muscleapp",
        age=37,
        height_cm=175,
        goal=Goal.STRENGTH,
        level=Difficulty.INTERMEDIATE,
        start_weight_kg=83.0,
        weekly_weight_delta=-0.1,
        adherence=0.62,  # the roster needs someone the trainer should chase
        lifts=(
            ("Barbell bench press", 70.0, 5, 1.25),
            ("Barbell back squat", 95.0, 5, 1.75),
            ("Pull-up", 0.0, 6, 0.0),
        ),
    ),
    _StudentSeed(
        name="Nerea B.",
        email="nerea@demo.muscleapp",
        age=30,
        height_cm=168,
        goal=Goal.FAT_LOSS,
        level=Difficulty.INTERMEDIATE,
        start_weight_kg=69.0,
        weekly_weight_delta=-0.35,
        adherence=0.9,
        lifts=(
            ("Goblet squat", 16.0, 12, 0.8),
            ("Romanian deadlift", 40.0, 10, 1.25),
            ("Plank", 0.0, 1, 0.0),
        ),
    ),
    _StudentSeed(
        name="Iván T.",
        email="ivan@demo.muscleapp",
        age=22,
        height_cm=186,
        goal=Goal.HYPERTROPHY,
        level=Difficulty.ADVANCED,
        start_weight_kg=80.0,
        weekly_weight_delta=0.25,
        adherence=0.85,
        lifts=(
            ("Barbell bench press", 80.0, 8, 1.5),
            ("Overhead press", 50.0, 8, 0.75),
            ("Pull-up", 0.0, 10, 0.0),
        ),
    ),
]

# The demo year: the calendar and the charts cover it end to end, so navigating
# to any week of 2026 shows a plan and a trained (or missed) session.
DEMO_YEAR = 2026
# Monday, Wednesday and Friday.
_TRAINING_WEEKDAYS = (0, 2, 4)
# Weeks it takes to reach most of a lift's yearly progress. Real strength gains
# are fast at first and flatten; a straight line would put a beginner's squat
# past 200 kg by December.
_PROGRESS_TIME_CONSTANT = 14.0
# Total gain over the year, as a share of the starting load.
_YEARLY_GAIN = 0.35
# Every so often a lighter week: deloads are part of any real plan.
_DELOAD_EVERY = 9
_DELOAD_FACTOR = 0.9


def _plate_rounded(weight: float) -> float:
    """Round to the nearest 2.5 kg, the smallest plate pair in a normal gym."""
    return round(weight / 2.5) * 2.5


def _demo_weeks(today: date, weeks: int | None) -> list[tuple[int, date]]:
    """The Mondays to write, paired with their week number in the plan.

    The default is every week of the demo year, which is what makes the deployed
    app feel lived-in. `weeks` trims that to a window around today — the tests
    re-seed a fresh schema for every case, and a full year each time turned a
    one-minute suite into eight.
    """
    first = date(DEMO_YEAR, 1, 1)
    monday = first - timedelta(days=first.weekday())
    numbered: list[tuple[int, date]] = []
    number = 0
    while monday <= date(DEMO_YEAR, 12, 31):
        numbered.append((number, monday))
        monday += timedelta(weeks=1)
        number += 1
    if weeks is None:
        return numbered
    # Keep the weeks around today: some trained, some still ahead.
    this_monday = today - timedelta(days=today.weekday())
    lower = this_monday - timedelta(weeks=weeks - 1)
    upper = this_monday + timedelta(weeks=1)
    return [(number, day) for number, day in numbered if lower <= day <= upper]


def _load_at(start_kg: float, week: int) -> float:
    """The load for a lift on a given week of the plan.

    Asymptotic rather than linear, with a deload every few weeks, so a year of
    training reads like training instead of arithmetic.
    """
    if not start_kg:
        return 0.0
    progress = 1 - math.exp(-week / _PROGRESS_TIME_CONSTANT)
    load = start_kg * (1 + _YEARLY_GAIN * progress)
    if week and week % _DELOAD_EVERY == 0:
        load *= _DELOAD_FACTOR
    return _plate_rounded(load)


def _generate_history(
    student: _StudentSeed,
    exercise_ids: dict[str, int],
    today: date,
    rng: random.Random,
    *,
    reliable_this_week: bool = False,
    weeks: int | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Build (workout logs, body metrics) for one student across the demo year.

    Only up to today: the rest of the year is scheduled, not trained. The body
    weight drifts toward the goal with a little noise so the line looks measured
    rather than computed. Deterministic given the same seed, so re-seeding tells
    the same story instead of a new one.

    `reliable_this_week` writes the current week as trained on target. It is for
    the account the app is demonstrated with: whether that week came out well is
    a coin toss the demo should not depend on, and every other week still shows
    the misses and the shortfalls.
    """
    logs: list[dict[str, object]] = []
    metrics: list[dict[str, object]] = []
    this_monday = today - timedelta(days=today.weekday())

    for week, monday in _demo_weeks(today, weeks):
        weight = student.start_weight_kg + student.weekly_weight_delta * week
        if monday <= today:
            metrics.append(
                {
                    "measured_on": monday,
                    "weight_kg": round(weight + rng.uniform(-0.4, 0.4), 1),
                }
            )

        for weekday in _TRAINING_WEEKDAYS:
            day = monday + timedelta(days=weekday)
            if day > today or day.year != DEMO_YEAR:
                continue
            showcase = reliable_this_week and monday == this_monday
            if not showcase and rng.random() > student.adherence:
                continue  # a session they skipped
            for name, start_kg, reps, _ in student.lifts:
                exercise_id = exercise_ids.get(name)
                if exercise_id is None:  # catalog changed; skip rather than fail
                    continue
                completed = showcase or rng.random() < 0.85
                logs.append(
                    {
                        "exercise_id": exercise_id,
                        "logged_on": day,
                        "weight_kg": _load_at(start_kg, week),
                        # Bodyweight work progresses in reps instead of kilos.
                        "reps": reps if start_kg else reps + week // 6,
                        "sets": 3 if completed else rng.choice((1, 2)),
                        "completed": completed,
                    }
                )
    return logs, metrics


async def _seed_trainer_profiles(session: AsyncSession) -> int:
    """Give every demo trainer the offer shown on their card.

    Merged so a curated change (a price, a bio) reaches an already-seeded
    database, but only genuinely new rows are counted: the caller reports
    "something was inserted", and re-running must be able to say no.
    """
    known = set((await session.scalars(select(TrainerProfileModel.user_id))).all())
    inserted = 0
    for trainer in DEMO_TRAINERS:
        user_id = await session.scalar(select(UserModel.id).where(UserModel.email == trainer.email))
        if user_id is None:
            continue
        await session.merge(
            TrainerProfileModel(
                user_id=user_id,
                specialty=trainer.specialty,
                rating=trainer.rating,
                price_per_month=trainer.price_per_month,
                bio=trainer.bio,
                bio_en=trainer.bio_en,
            )
        )
        if user_id not in known:
            inserted += 1
    await session.commit()
    return inserted


async def _seed_coaching(session: AsyncSession, weeks: int | None = None) -> int:
    """Give the demo trainer a roster with a year of history behind it.

    Incremental per day, not per student: it inserts the sessions that are
    missing and leaves every row that already exists untouched. Skipping a
    student who had *any* log meant the year of history never reached the
    deployed database — it already held a few recent weeks from an earlier
    release, so the widened window was silently ignored (the same trap the food
    catalog fell into). Leaving existing rows alone is what keeps a student's own
    synced progress safe: a redeploy must not rewrite what they actually did.
    """
    trainer_email = next(email for _, email, role in DEMO_USERS if role is UserRole.TRAINER)
    trainer_id = await session.scalar(select(UserModel.id).where(UserModel.email == trainer_email))
    exercise_ids = {
        name_en: exercise_id
        for exercise_id, name_en in await session.execute(
            select(ExerciseModel.id, ExerciseModel.name_en)
        )
        if name_en
    }
    if trainer_id is None or not exercise_ids:
        return 0  # catalog not seeded yet; nothing to attach history to

    today = date.today()
    seeded = 0
    for index, student in enumerate(DEMO_STUDENTS):
        user_id = await session.scalar(select(UserModel.id).where(UserModel.email == student.email))
        if user_id is None:
            continue
        await session.merge(
            StudentProfileModel(
                user_id=user_id,
                birth_year=today.year - student.age,
                height_cm=student.height_cm,
                goal=student.goal,
                level=student.level,
            )
        )
        # One trainer per student, so the check is on the student alone: a demo
        # student who hired someone else keeps their choice.
        linked = await session.scalar(
            select(TrainerStudentModel.id).where(TrainerStudentModel.student_id == user_id)
        )
        if linked is None:
            await session.execute(
                pg_insert(TrainerStudentModel)
                .values(trainer_id=trainer_id, student_id=user_id)
                .on_conflict_do_nothing(constraint="uq_trainer_student")
            )

        # Fixed seed per student: the same demo data on every machine. Not a
        # security context — this only shapes fake training history.
        rng = random.Random(index)  # noqa: S311  # nosec B311
        logs, metrics = _generate_history(
            student,
            exercise_ids,
            today,
            rng,
            # The first entry is the account the app is demonstrated with.
            reliable_this_week=student.email == DEMO_STUDENTS[0].email,
            weeks=weeks,
        )
        logged_days = {
            (exercise_id, day)
            for exercise_id, day in await session.execute(
                select(WorkoutLogModel.exercise_id, WorkoutLogModel.logged_on).where(
                    WorkoutLogModel.user_id == user_id
                )
            )
        }
        measured_days = set(
            (
                await session.scalars(
                    select(BodyMetricModel.measured_on).where(BodyMetricModel.user_id == user_id)
                )
            ).all()
        )
        new_logs = [
            log for log in logs if (log["exercise_id"], log["logged_on"]) not in logged_days
        ]
        new_metrics = [metric for metric in metrics if metric["measured_on"] not in measured_days]
        # Bulk-inserted: a year is a few thousand rows per student, and the ORM
        # would spend seconds building objects nobody reads. It also keeps the
        # integration tests quick, since each one re-seeds a fresh schema.
        if new_logs:
            await session.execute(
                insert(WorkoutLogModel), [{"user_id": user_id, **log} for log in new_logs]
            )
        if new_metrics:
            await session.execute(
                insert(BodyMetricModel), [{"user_id": user_id, **metric} for metric in new_metrics]
            )
        if new_logs or new_metrics:
            seeded += 1

    await session.commit()
    return seeded


async def _seed_foods(session: AsyncSession) -> int:
    """Insert the catalog foods that are missing, keyed by Spanish name.

    Incremental on purpose: an "only if the table is empty" seed would never
    deliver newly curated foods to an already-populated database (e.g. the
    deployed one). New rows are created without an embedding, so the boot-time
    backfill vectorizes them on the same deploy. Returns how many were inserted.
    """
    known = set((await session.scalars(select(FoodModel.name))).all())
    missing = [food for food in FOODS if food[0] not in known]
    if not missing:
        return 0
    session.add_all(
        FoodModel(
            name=name_es,
            name_en=name_en,
            emoji=emoji,
            category=category,
            kcal=kcal,
            protein_g=protein,
            carbs_g=carbs,
            fat_g=fat,
            tags=tags,
        )
        for name_es, name_en, emoji, category, kcal, protein, carbs, fat, tags in missing
    )
    await session.commit()
    return len(missing)


async def _seed_plan(session: AsyncSession, weeks: int | None = None) -> int:
    """Write every student's calendar for the whole demo year.

    The trainer's plan is the same three lifts on Monday, Wednesday and Friday,
    with the load stepping up as the year goes on. Past days already have their
    logs from the history seed, so they show as done, partial or missed; from
    today on they are pending, which is what makes navigating forward useful.

    Bulk-inserted: this is a few thousand rows, and the ORM would spend a second
    building objects nobody reads.

    Only the days that are missing are written. An "insert nothing if the table
    has rows" guard kept the deployed calendar at the single week an earlier
    release had seeded, and it would also fight the trainer: every prescription
    they add or remove lives in this table, and re-running the seed must not
    resurrect what they deleted or overwrite what they changed.
    """
    trainer_email = next(email for _, email, role in DEMO_USERS if role is UserRole.TRAINER)
    trainer_id = await session.scalar(select(UserModel.id).where(UserModel.email == trainer_email))
    exercise_ids = {
        name_en: exercise_id
        for exercise_id, name_en in await session.execute(
            select(ExerciseModel.id, ExerciseModel.name_en)
        )
        if name_en
    }
    if trainer_id is None or not exercise_ids:
        return 0

    today = date.today()
    rows: list[dict[str, object]] = []
    for student in DEMO_STUDENTS:
        user_id = await session.scalar(select(UserModel.id).where(UserModel.email == student.email))
        if user_id is None:
            continue
        # A day that already carries a prescription belongs to whoever wrote it:
        # the trainer edits this table from the app, so the seed fills the empty
        # days of the year and never revisits one it (or they) already wrote.
        prescribed_days = set(
            (
                await session.scalars(
                    select(PlanItemModel.scheduled_on).where(PlanItemModel.student_id == user_id)
                )
            ).all()
        )
        for week, monday in _demo_weeks(today, weeks):
            for weekday in _TRAINING_WEEKDAYS:
                day = monday + timedelta(days=weekday)
                if day.year != DEMO_YEAR or day in prescribed_days:
                    continue
                for name, start_kg, reps, _ in student.lifts:
                    exercise_id = exercise_ids.get(name)
                    if exercise_id is None:
                        continue
                    rows.append(
                        {
                            "trainer_id": trainer_id,
                            "student_id": user_id,
                            "exercise_id": exercise_id,
                            "scheduled_on": day,
                            "target_sets": 3,
                            "target_reps": reps if start_kg else reps + week // 6,
                            "target_weight_kg": _load_at(start_kg, week) or None,
                            "notes": None,
                        }
                    )

    if rows:
        await session.execute(insert(PlanItemModel), rows)
        await session.commit()
    return len(rows)


async def seed(session: AsyncSession, weeks: int | None = None) -> bool:
    """Populate every catalog that needs it. Returns True if anything was inserted.

    `weeks` trims the demo history and plan to a window around today; the
    default writes the whole demo year, which is what the deployed app serves.
    """
    users_inserted = await _seed_users(session, get_settings().demo_password)
    foods_inserted = await _seed_foods(session)
    catalog_inserted = await _seed_catalog(session)
    # Last: the history needs both the demo users and the exercise catalog.
    trainers_inserted = await _seed_trainer_profiles(session)
    coaching_inserted = await _seed_coaching(session, weeks)
    plan_inserted = await _seed_plan(session, weeks)
    return bool(
        users_inserted
        or foods_inserted
        or catalog_inserted
        or trainers_inserted
        or coaching_inserted
        or plan_inserted
    )


async def _seed_catalog(session: AsyncSession) -> bool:
    """Insert muscles and exercises, only when the catalog is still empty."""
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

    for (
        name_es,
        name_en,
        desc_es,
        desc_en,
        video_es,
        video_en,
        equipment,
        difficulty,
        links,
    ) in EXERCISES:
        steps_es, steps_en = STEPS.get(name_es, (None, None))
        if video_es is None and name_es in VIDEOS:
            video_es = _yt(VIDEOS[name_es])
        exercise = ExerciseModel(
            name=name_es,
            name_en=name_en,
            description=desc_es,
            description_en=desc_en,
            video_url=video_es,
            video_url_en=video_en,
            steps=steps_es,
            steps_en=steps_en,
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
