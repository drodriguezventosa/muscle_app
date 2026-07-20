"""Idempotent seed data for the muscle and exercise catalog (ES + EN).

Run as a script (`python -m app.infrastructure.persistence.seed`) or import
`seed` and call it with a session. Embeddings are left null here and computed by
the AI phase. `name`/`description`/`video_url` hold Spanish; `*_en` hold English.
"""

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.value_objects.enums import Difficulty, Equipment, MuscleGroup, MuscleRole
from app.infrastructure.persistence.database import get_session_factory
from app.infrastructure.persistence.models.exercise import ExerciseModel, ExerciseMuscleModel
from app.infrastructure.persistence.models.food import FoodModel
from app.infrastructure.persistence.models.muscle import MuscleModel


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
]
# fmt: on


async def _seed_foods(session: AsyncSession) -> bool:
    """Seed the food catalog if empty. Independent of muscles/exercises so it
    lands on an already-seeded database (e.g. an existing production DB)."""
    if await session.scalar(select(func.count()).select_from(FoodModel)):
        return False
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
        for name_es, name_en, emoji, category, kcal, protein, carbs, fat, tags in FOODS
    )
    await session.commit()
    return True


async def seed(session: AsyncSession) -> bool:
    """Populate the catalog if empty. Returns True if any data was inserted."""
    foods_inserted = await _seed_foods(session)
    existing = await session.scalar(select(func.count()).select_from(MuscleModel))
    if existing:
        return foods_inserted

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
