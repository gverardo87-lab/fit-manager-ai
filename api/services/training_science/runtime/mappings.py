"""Mapping espliciti tra builder UI, dominio scientifico e catalogo esercizi."""

from api.schemas.training_science import TSBuilderObjective
from api.services.training_science.types import GruppoMuscolare, Livello, Obiettivo, PatternMovimento

BUILDER_OBJECTIVE_TO_SCIENTIFIC: dict[TSBuilderObjective, Obiettivo] = {
    "generale": Obiettivo.TONIFICAZIONE,
    "forza": Obiettivo.FORZA,
    "ipertrofia": Obiettivo.IPERTROFIA,
    "resistenza": Obiettivo.RESISTENZA,
    "dimagrimento": Obiettivo.DIMAGRIMENTO,
}

BUILDER_LEVEL_TO_SCIENTIFIC: dict[str, Livello] = {
    "beginner": Livello.PRINCIPIANTE,
    "intermedio": Livello.INTERMEDIO,
    "avanzato": Livello.AVANZATO,
}

SCIENTIFIC_LEVEL_TO_WORKOUT: dict[Livello, str] = {
    Livello.PRINCIPIANTE: "beginner",
    Livello.INTERMEDIO: "intermedio",
    Livello.AVANZATO: "avanzato",
}

MUSCLE_GROUP_TO_CATALOG: dict[GruppoMuscolare, set[str]] = {
    GruppoMuscolare.PETTO: {"chest", "pecs", "petto"},
    GruppoMuscolare.DORSALI: {"back", "lats", "dorsali"},
    GruppoMuscolare.DELT_ANT: {"shoulders", "shoulder", "front_delts", "deltoide_anteriore"},
    GruppoMuscolare.DELT_LAT: {"shoulders", "shoulder", "side_delts", "deltoide_laterale"},
    GruppoMuscolare.DELT_POST: {"rear_delts", "shoulders", "shoulder", "deltoide_posteriore"},
    GruppoMuscolare.BICIPITI: {"biceps", "bicipiti"},
    GruppoMuscolare.TRICIPITI: {"triceps", "tricipiti"},
    GruppoMuscolare.QUADRICIPITI: {"quadriceps", "quads", "quadricipiti"},
    GruppoMuscolare.FEMORALI: {"hamstrings", "femorali"},
    GruppoMuscolare.GLUTEI: {"glutes", "glutei"},
    GruppoMuscolare.POLPACCI: {"calves", "polpacci"},
    GruppoMuscolare.TRAPEZIO: {"traps", "trapezius", "trapezio"},
    GruppoMuscolare.CORE: {"core", "abs", "abdominals"},
    GruppoMuscolare.AVAMBRACCI: {"forearms", "avambracci", "grip"},
    GruppoMuscolare.ADDUTTORI: {"adductors", "adduttori"},
}

PATTERN_TO_CATALOG_PATTERNS: dict[PatternMovimento, set[str]] = {
    PatternMovimento.PUSH_H: {"push_h"},
    PatternMovimento.PUSH_V: {"push_v"},
    PatternMovimento.SQUAT: {"squat"},
    PatternMovimento.HINGE: {"hinge"},
    PatternMovimento.PULL_H: {"pull_h"},
    PatternMovimento.PULL_V: {"pull_v"},
    PatternMovimento.CORE: {"core"},
    PatternMovimento.ROTATION: {"rotation"},
    PatternMovimento.CARRY: {"carry"},
    PatternMovimento.HIP_THRUST: {"hinge"},
    PatternMovimento.CURL: {"pull_h", "pull_v"},
    PatternMovimento.EXTENSION_TRI: {"push_h", "push_v"},
    PatternMovimento.LATERAL_RAISE: {"push_v"},
    PatternMovimento.FACE_PULL: {"pull_h", "pull_v"},
    PatternMovimento.CALF_RAISE: {"squat", "hinge"},
    PatternMovimento.LEG_CURL: {"hinge"},
    PatternMovimento.LEG_EXTENSION: {"squat"},
    PatternMovimento.ADDUCTOR: {"squat"},
}
