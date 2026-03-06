"""
Training Science Engine — Matrice di contribuzione muscolare.

Ogni pattern di movimento attiva i muscoli con intensita' diverse.
Questa matrice, basata su studi EMG, e' il cuore del calcolo del
volume effettivo: permette di sapere QUANTE serie reali riceve
ogni muscolo da ogni esercizio.

Scala contribuzione (0-1):
  1.0 = motore primario (attivazione EMG > 70%)
  0.7 = sinergista maggiore (40-70%)
  0.4 = sinergista minore (20-40%)
  0.2 = stabilizzatore (10-20%)
  0.0 = non coinvolto

Fonti:
  - Contreras — "EMG analysis of resistance exercises" (2010)
  - Schoenfeld — "Regional differences in muscle activation" (2010)
  - NSCA — Essentials of Strength Training (2016) cap. 16-19
  - Boettcher et al. — "Shoulder muscle recruitment patterns" (2008)
  - Ebben et al. — "EMG analysis of lower body exercises" (2009)
"""

from .types import GruppoMuscolare as M, PatternMovimento as P

# Type alias per leggibilita'
ContributionMap = dict[M, float]

# ════════════════════════════════════════════════════════════
# MATRICE DI CONTRIBUZIONE — Pattern → Muscoli
# ════════════════════════════════════════════════════════════
#
# Ogni riga e' un pattern di movimento.
# Ogni valore e' la percentuale di contribuzione (0-1) al muscolo.
# Solo muscoli con contributo > 0 sono elencati.

CONTRIBUTION_MATRIX: dict[P, ContributionMap] = {
    # ── Compound Push ──
    P.PUSH_H: {
        M.PETTO: 1.0,
        M.DELT_ANT: 0.7,
        M.TRICIPITI: 0.7,
        M.CORE: 0.2,
    },
    P.PUSH_V: {
        M.DELT_ANT: 1.0,
        M.DELT_LAT: 0.7,
        M.TRICIPITI: 0.7,
        M.TRAPEZIO: 0.4,
        M.CORE: 0.2,
    },
    # ── Compound Pull ──
    P.PULL_H: {
        M.DORSALI: 1.0,
        M.TRAPEZIO: 0.7,
        M.DELT_POST: 0.7,
        M.BICIPITI: 0.7,
        M.AVAMBRACCI: 0.4,
    },
    P.PULL_V: {
        M.DORSALI: 1.0,
        M.BICIPITI: 0.7,
        M.DELT_POST: 0.4,
        M.TRAPEZIO: 0.4,
        M.AVAMBRACCI: 0.4,
    },
    # ── Compound Lower ──
    P.SQUAT: {
        M.QUADRICIPITI: 1.0,
        M.GLUTEI: 0.7,
        M.FEMORALI: 0.4,
        M.ADDUTTORI: 0.4,
        M.CORE: 0.4,
        M.POLPACCI: 0.2,
    },
    P.HINGE: {
        M.FEMORALI: 1.0,
        M.GLUTEI: 1.0,
        M.DORSALI: 0.4,
        M.TRAPEZIO: 0.4,
        M.CORE: 0.4,
        M.AVAMBRACCI: 0.2,
    },
    # ── Compound Functional ──
    P.CORE: {
        M.CORE: 1.0,
    },
    P.ROTATION: {
        M.CORE: 0.7,
        M.DELT_POST: 0.4,
    },
    P.CARRY: {
        M.AVAMBRACCI: 1.0,
        M.CORE: 0.7,
        M.TRAPEZIO: 0.7,
        M.GLUTEI: 0.2,
    },
    # ── Isolation Lower ──
    P.HIP_THRUST: {
        M.GLUTEI: 1.0,
        M.FEMORALI: 0.4,
        M.CORE: 0.2,
    },
    P.LEG_EXTENSION: {
        M.QUADRICIPITI: 1.0,
    },
    P.LEG_CURL: {
        M.FEMORALI: 1.0,
    },
    P.CALF_RAISE: {
        M.POLPACCI: 1.0,
    },
    P.ADDUCTOR: {
        M.ADDUTTORI: 1.0,
    },
    # ── Isolation Upper ──
    P.CURL: {
        M.BICIPITI: 1.0,
        M.AVAMBRACCI: 0.4,
    },
    P.EXTENSION_TRI: {
        M.TRICIPITI: 1.0,
    },
    P.LATERAL_RAISE: {
        M.DELT_LAT: 1.0,
        M.TRAPEZIO: 0.2,
    },
    P.FACE_PULL: {
        M.DELT_POST: 1.0,
        M.TRAPEZIO: 0.4,
    },
}


def get_contribution(pattern: P) -> ContributionMap:
    """
    Ritorna la mappa di contribuzione muscolare per un pattern.
    Muscoli non elencati hanno contributo 0.
    """
    return CONTRIBUTION_MATRIX.get(pattern, {})


def get_muscle_contribution(pattern: P, muscolo: M) -> float:
    """Ritorna il contributo (0-1) di un pattern su un muscolo specifico."""
    return CONTRIBUTION_MATRIX.get(pattern, {}).get(muscolo, 0.0)


def get_primary_muscles(pattern: P) -> list[M]:
    """Ritorna i muscoli con contributo >= 0.7 (motori primari e sinergisti maggiori)."""
    return [m for m, c in get_contribution(pattern).items() if c >= 0.7]


def get_all_muscles(pattern: P) -> list[M]:
    """Ritorna tutti i muscoli coinvolti (contributo > 0)."""
    return list(get_contribution(pattern).keys())


def is_compound(pattern: P) -> bool:
    """True se il pattern e' multi-articolare (coinvolge 3+ muscoli con contributo >= 0.4)."""
    return sum(1 for c in get_contribution(pattern).values() if c >= 0.4) >= 3


def compute_effective_sets(
    slots: list[tuple[P, int]],
) -> dict[M, float]:
    """
    Calcola il volume effettivo per muscolo da una lista di (pattern, serie).

    Esempio:
        slots = [(P.PUSH_H, 4), (P.PUSH_V, 3), (P.CURL, 3)]
        result = {
            M.PETTO: 4.0,          # 4 × 1.0
            M.DELT_ANT: 5.8,       # 4 × 0.7 + 3 × 1.0
            M.DELT_LAT: 2.1,       # 3 × 0.7
            M.TRICIPITI: 4.9,       # 4 × 0.7 + 3 × 0.7
            M.BICIPITI: 3.0,        # 3 × 1.0
            ...
        }
    """
    effective: dict[M, float] = {}
    for pattern, serie in slots:
        for muscolo, contributo in get_contribution(pattern).items():
            effective[muscolo] = effective.get(muscolo, 0.0) + serie * contributo
    return effective


# ════════════════════════════════════════════════════════════
# BRIDGE — Mapping dal DB esercizi esistente
# ════════════════════════════════════════════════════════════

# Il DB ha `pattern_movimento` come stringa. Questo mapping collega
# i pattern del DB ai PatternMovimento del motore scientifico.
# I pattern di isolamento si derivano da categoria + muscolo primario.

DB_PATTERN_MAP: dict[str, P | None] = {
    "squat": P.SQUAT,
    "hinge": P.HINGE,
    "push_h": P.PUSH_H,
    "push_v": P.PUSH_V,
    "pull_h": P.PULL_H,
    "pull_v": P.PULL_V,
    "core": P.CORE,
    "rotation": P.ROTATION,
    "carry": P.CARRY,
    "warmup": None,
    "stretch": None,
    "mobility": None,
}

# Per esercizi di isolamento nel DB: categoria + muscolo primario → pattern
ISOLATION_INFERENCE: dict[str, P] = {
    "bicipiti": P.CURL,
    "tricipiti": P.EXTENSION_TRI,
    "polpacci": P.CALF_RAISE,
    "femorali": P.LEG_CURL,
    "quadricipiti": P.LEG_EXTENSION,
    "glutei": P.HIP_THRUST,
    "adduttori": P.ADDUCTOR,
    "deltoide_laterale": P.LATERAL_RAISE,
    "deltoide_posteriore": P.FACE_PULL,
}


def resolve_pattern(
    db_pattern: str | None,
    categoria: str | None = None,
    muscolo_primario: str | None = None,
) -> P | None:
    """
    Risolve un esercizio del DB al PatternMovimento del motore scientifico.

    1. Se ha un pattern_movimento nel DB → mapping diretto
    2. Se e' isolation → inferisce dal muscolo primario
    3. Se non mappabile → None (es. warmup, stretch)
    """
    if db_pattern and db_pattern in DB_PATTERN_MAP:
        result = DB_PATTERN_MAP[db_pattern]
        if result is not None:
            return result

    if categoria == "isolation" and muscolo_primario:
        return ISOLATION_INFERENCE.get(muscolo_primario)

    return None
