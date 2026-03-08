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


def compute_intensity_weights(
    slots_with_load: list[tuple[P, int, float, float | None]],
) -> list[float]:
    """
    Compute plan-relative intensity weights from load data.

    Dose-Response Model (Israetel RP 2020, Haff & Triplett NSCA 2016):
      DOSE = VOLUME x INTENSITY

    Quando il carico (kg) e' presente, la "dose" di una serie viene
    modulata dalla sua intensita' relativa alla media del piano.
    Questo crea una metrica unificata: serie pesate per intensita'.

    Formula:
      tonnage_per_set[i] = rep_avg[i] x carico_kg[i]
      intensity_weight[i] = tonnage_per_set[i] / avg_tonnage_per_set

    Comportamento:
      - Slot SENZA carico: weight = 1.0 (degenera in conteggio serie)
      - Slot CON carico: weight = intensita' relativa (plan-normalized)
      - Se NESSUNO slot ha carico: tutti i pesi = 1.0

    Proprieta':
      - Media(pesi degli slot con carico) ≈ 1.0 (normalizzazione relativa)
      - Totale serie pesate ≈ totale serie grezze (conservazione)
      - Slot pesanti: weight > 1.0 — contano PIU' delle serie grezze
      - Slot leggeri: weight < 1.0 — contano MENO delle serie grezze

    Input: lista di (pattern, serie, rep_avg, carico_kg).
      rep_avg e carico_kg possono essere None (slot senza carico).

    Output: lista di float con un peso per ogni slot (stessa lunghezza).

    Fonti:
      - Haff & Triplett (NSCA 2016) cap. 15 — Volume-Load definition
      - Israetel RP 2020 — Dose-response relationship
      - McBride et al. (2009) — Tonnage as training load metric
    """
    # Raccogli tonnage-per-set per gli slot con carico
    tonnages_per_set: list[float] = []
    for _, _, rep_avg, carico_kg in slots_with_load:
        if (
            carico_kg is not None
            and carico_kg > 0
            and rep_avg is not None
            and rep_avg > 0
        ):
            tonnages_per_set.append(rep_avg * carico_kg)

    # Nessun carico nel piano → tutti i pesi = 1.0 (set counting puro)
    if not tonnages_per_set:
        return [1.0] * len(slots_with_load)

    avg_tonnage = sum(tonnages_per_set) / len(tonnages_per_set)

    weights: list[float] = []
    for _, _, rep_avg, carico_kg in slots_with_load:
        if (
            carico_kg is not None
            and carico_kg > 0
            and rep_avg is not None
            and rep_avg > 0
        ):
            weights.append((rep_avg * carico_kg) / avg_tonnage)
        else:
            weights.append(1.0)

    return weights


def compute_effective_sets(
    slots: list[tuple[P, int]],
    intensity_weights: list[float] | None = None,
) -> dict[M, float]:
    """
    Calcola il volume effettivo per muscolo da una lista di (pattern, serie).

    Questo e' il volume MECCANICO totale — usato per rapporti biomeccanici
    e analisi di recupero dove conta il lavoro reale svolto dal muscolo.

    Se intensity_weights e' fornito (dose-response model), ogni serie
    viene moltiplicata per il peso di intensita' corrispondente:
      volume[M] = Σ(serie × intensity_weight × contributo_EMG)

    Senza intensity_weights (default): degenera nel conteggio serie puro.

    Esempio (senza pesi):
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
    for i, (pattern, serie) in enumerate(slots):
        w = intensity_weights[i] if intensity_weights else 1.0
        for muscolo, contributo in get_contribution(pattern).items():
            effective[muscolo] = effective.get(muscolo, 0.0) + serie * w * contributo
    return effective


# ════════════════════════════════════════════════════════════
# VOLUME IPERTROFICO — Peso differenziato per qualita' stimolo
# ════════════════════════════════════════════════════════════
#
# Non tutto il volume e' uguale per la crescita muscolare.
# Un muscolo che STABILIZZA (core durante squat, 0.2) non riceve
# lo stesso stimolo ipertrofico di quando e' il MOTORE PRIMARIO
# (core durante crunch, 1.0).
#
# Schoenfeld 2017: lo stimolo ipertrofico richiede "sufficient
# mechanical tension" — la soglia EMG e' circa 40% MVC.
# Israetel (RP 2020): il volume indiretto da stabilizzazione
# "conta poco o nulla" verso il volume totale per l'ipertrofia.
#
# Pesi per qualita' di contribuzione (Israetel RP 2020, "half a set" rule):
#   1.0 (primario):           peso 1.0 — stimolo pieno (motore primario)
#   0.7 (sinergista maggiore): peso 0.5 — mezzo set (volume indiretto, ~half a set)
#   0.4 (sinergista minore):   peso 0.25 — quarto di set (contributo marginale)
#   0.2 (stabilizzatore):      peso 0.0 — sotto soglia ipertrofica
#
# Rationale: Israetel RP 2020 — "count indirect volume as roughly half a set".
# Un sinergista maggiore (0.7 EMG) NON riceve lo stesso stimolo ipertrofico
# del motore primario. Esempio: bicipiti durante pull-up ricevono ~0.5 set
# per ogni set di pull-up, NON 1.0 set pieno. Senza questo sconto, muscoli
# hub (trapezio, core, avambracci) accumulano volume fantasma e sfondano MRV.
#
# IMPORTANTE: compute_effective_sets() resta invariato per i calcoli
# di balance ratio e recupero, dove il lavoro meccanico conta tutto.
# compute_hypertrophy_sets() si usa SOLO per confronto con MEV/MAV/MRV.

_HYPERTROPHY_WEIGHT: dict[float, float] = {
    1.0: 1.0,   # motore primario: stimolo pieno
    0.7: 0.5,   # sinergista maggiore: mezzo set (Israetel "half a set" rule)
    0.4: 0.25,  # sinergista minore: quarto di set (contributo marginale)
    0.2: 0.0,   # stabilizzatore: sotto soglia ipertrofica
}


def _get_hypertrophy_weight(contributo: float) -> float:
    """
    Ritorna il peso ipertrofico per un livello di contribuzione.

    Lookup esatto nella tabella dei pesi. Per valori non standard
    (futuri), interpola linearmente.
    """
    if contributo in _HYPERTROPHY_WEIGHT:
        return _HYPERTROPHY_WEIGHT[contributo]
    # Fallback per valori non standard: proporzionale
    if contributo >= 0.7:
        return 0.5
    if contributo >= 0.4:
        return 0.25
    return 0.0


def compute_hypertrophy_sets(
    slots: list[tuple[P, int]],
    intensity_weights: list[float] | None = None,
) -> dict[M, float]:
    """
    Calcola il volume IPERTROFICO per muscolo (serie che contano per la crescita).

    A differenza di compute_effective_sets(), questa funzione sconta il volume
    indiretto secondo la "half a set" rule (Israetel RP 2020).

    Il hypertrophy_weight SOSTITUISCE il contributo EMG, non lo moltiplica:
      - contributo 1.0 (primario)    → weight 1.0  → serie × 1.0  = 1 serie piena
      - contributo 0.7 (sinergista+) → weight 0.5  → serie × 0.5  = mezzo set
      - contributo 0.4 (sinergista-) → weight 0.25 → serie × 0.25 = quarto di set
      - contributo 0.2 (stabiliz.)   → weight 0.0  → serie × 0.0  = zero

    Se intensity_weights e' fornito (dose-response model), ogni serie
    viene ulteriormente moltiplicata per il peso di intensita':
      volume[M] = Σ(serie × intensity_weight × hypertrophy_weight)

    Senza intensity_weights (default): degenera nel conteggio serie puro.

    USARE PER: confronto con target MEV/MAV/MRV (soglie di volume ipertrofico).
    NON USARE PER: rapporti biomeccanici e recupero (usare compute_effective_sets).

    Fonti:
      - Schoenfeld 2017: soglia EMG 40% MVC per stimolo ipertrofico
      - Israetel RP 2020: volume indiretto conta "roughly half a set"
      - Haff & Triplett NSCA 2016: dose-response (con intensity_weights)
    """
    hypertrophy: dict[M, float] = {}
    for i, (pattern, serie) in enumerate(slots):
        w = intensity_weights[i] if intensity_weights else 1.0
        for muscolo, contributo in get_contribution(pattern).items():
            hyp_weight = _get_hypertrophy_weight(contributo)
            if hyp_weight > 0:
                volume = serie * w * hyp_weight
                hypertrophy[muscolo] = hypertrophy.get(muscolo, 0.0) + volume
    return hypertrophy


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
