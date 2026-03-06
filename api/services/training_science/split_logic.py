"""
Training Science Engine — Logica di split e struttura sessioni.

Dato un numero di sessioni/settimana, questo modulo determina:
  1. Il tipo di split ottimale (full_body, upper_lower, PPL)
  2. La struttura delle sessioni (ruoli, pattern primari, volume allocato)

Principio fondante (Schoenfeld 2016):
  Ogni muscolo dovrebbe essere stimolato ALMENO 2 volte a settimana
  per ottimizzare la sintesi proteica muscolare (MPS).

Regola di selezione split (NSCA 2016, Israetel RP 2020):
  - 2-3 sessioni/sett → Full Body (ogni muscolo ogni sessione)
  - 4 sessioni/sett → Upper/Lower (2 upper + 2 lower, freq 2x/muscolo)
  - 5 sessioni/sett → Upper/Lower asimmetrico (3 upper + 2 lower, o viceversa)
  - 6 sessioni/sett → Push/Pull/Legs (2 rotazioni complete, freq 2x/muscolo)

La scelta NON e' arbitraria — e' l'unica che garantisce freq >= 2x
con volume gestibile per sessione. Alternative (bro split, body part)
hanno freq 1x/muscolo → sub-ottimale per MPS (Schoenfeld 2016).

Fonti:
  - Schoenfeld — "Effects of RT frequency on hypertrophy" (2016)
  - NSCA — "Essentials of Strength Training" (Haff & Triplett, 2016) cap. 21-22
  - Israetel — "Scientific Principles of Hypertrophy Training" (2020)
  - Helms — "The Muscle and Strength Pyramid: Training" (2019)
"""

from .types import (
    TipoSplit,
    RuoloSessione,
    PatternMovimento as P,
    GruppoMuscolare as M,
    Obiettivo,
    Livello,
)
from .muscle_contribution import CONTRIBUTION_MATRIX


# ════════════════════════════════════════════════════════════
# SPLIT SELECTION — Frequenza → Split ottimale
# ════════════════════════════════════════════════════════════
#
# Mapping deterministico. Nessuna euristica — la scelta
# e' dettata dalla matematica della frequenza muscolare.

SPLIT_PER_FREQUENZA: dict[int, TipoSplit] = {
    2: TipoSplit.FULL_BODY,
    3: TipoSplit.FULL_BODY,
    4: TipoSplit.UPPER_LOWER,
    5: TipoSplit.UPPER_LOWER,
    6: TipoSplit.PUSH_PULL_LEGS,
}


# ════════════════════════════════════════════════════════════
# STRUTTURA SESSIONI — Split → Lista ruoli sessione
# ════════════════════════════════════════════════════════════
#
# Ogni split definisce QUALI sessioni compongono la settimana.
# Il ruolo determina quali pattern di movimento appartengono
# alla sessione (vedi PATTERN_PER_RUOLO).
#
# Per upper/lower a 5 sessioni: 3 upper + 2 lower.
# Rationale (Helms 2019): la muscolatura upper body ha piu'
# gruppi da coprire (petto, dorsali, deltoidi x3, bicipiti,
# tricipiti, trapezio = 8 gruppi) rispetto a lower body
# (quadricipiti, femorali, glutei, polpacci, adduttori = 5 gruppi).

SESSIONI_PER_SPLIT: dict[tuple[TipoSplit, int], list[RuoloSessione]] = {
    # Full Body: ogni sessione allena tutto
    (TipoSplit.FULL_BODY, 2): [
        RuoloSessione.FULL_BODY,
        RuoloSessione.FULL_BODY,
    ],
    (TipoSplit.FULL_BODY, 3): [
        RuoloSessione.FULL_BODY,
        RuoloSessione.FULL_BODY,
        RuoloSessione.FULL_BODY,
    ],
    # Upper/Lower: bilanciato a 4, asimmetrico a 5
    (TipoSplit.UPPER_LOWER, 4): [
        RuoloSessione.UPPER,
        RuoloSessione.LOWER,
        RuoloSessione.UPPER,
        RuoloSessione.LOWER,
    ],
    (TipoSplit.UPPER_LOWER, 5): [
        RuoloSessione.UPPER,
        RuoloSessione.LOWER,
        RuoloSessione.UPPER,
        RuoloSessione.LOWER,
        RuoloSessione.UPPER,
    ],
    # PPL: 2 rotazioni complete
    (TipoSplit.PUSH_PULL_LEGS, 6): [
        RuoloSessione.PUSH,
        RuoloSessione.PULL,
        RuoloSessione.LEGS,
        RuoloSessione.PUSH,
        RuoloSessione.PULL,
        RuoloSessione.LEGS,
    ],
}


# ════════════════════════════════════════════════════════════
# PATTERN PER RUOLO — Quali pattern in quale sessione
# ════════════════════════════════════════════════════════════
#
# Mappatura deterministica ruolo → pattern compound primari.
# Basata sulla classificazione funzionale NSCA:
#   Push = petto + deltoidi anteriori + tricipiti
#   Pull = dorsali + deltoidi posteriori + bicipiti
#   Legs = quadricipiti + femorali + glutei + polpacci
#   Full Body = tutti i pattern compound
#   Upper = push + pull
#   Lower = legs
#
# I pattern funzionali (core, rotation, carry) sono distribuiti
# secondo affinita' biomeccanica (Boyle 2010):
#   - Core: full_body e lower (stabilizzazione pelvica)
#   - Rotation: full_body e upper (piano trasversale spalle)
#   - Carry: full_body e lower (integrazione core + grip)

PATTERN_COMPOUND_PER_RUOLO: dict[RuoloSessione, list[P]] = {
    RuoloSessione.FULL_BODY: [
        P.PUSH_H, P.PUSH_V, P.PULL_H, P.PULL_V,
        P.SQUAT, P.HINGE, P.CORE, P.ROTATION, P.CARRY,
    ],
    RuoloSessione.UPPER: [
        P.PUSH_H, P.PUSH_V, P.PULL_H, P.PULL_V, P.ROTATION,
    ],
    RuoloSessione.LOWER: [
        P.SQUAT, P.HINGE, P.CORE, P.CARRY,
    ],
    RuoloSessione.PUSH: [
        P.PUSH_H, P.PUSH_V,
    ],
    RuoloSessione.PULL: [
        P.PULL_H, P.PULL_V, P.ROTATION,
    ],
    RuoloSessione.LEGS: [
        P.SQUAT, P.HINGE, P.CORE, P.CARRY,
    ],
}


# ════════════════════════════════════════════════════════════
# MUSCOLI PRINCIPALI PER RUOLO — Per il calcolo focus sessione
# ════════════════════════════════════════════════════════════

MUSCOLI_PER_RUOLO: dict[RuoloSessione, list[M]] = {
    RuoloSessione.FULL_BODY: list(M),
    RuoloSessione.UPPER: [
        M.PETTO, M.DORSALI, M.DELT_ANT, M.DELT_LAT, M.DELT_POST,
        M.BICIPITI, M.TRICIPITI, M.TRAPEZIO, M.AVAMBRACCI,
    ],
    RuoloSessione.LOWER: [
        M.QUADRICIPITI, M.FEMORALI, M.GLUTEI, M.POLPACCI,
        M.ADDUTTORI, M.CORE,
    ],
    RuoloSessione.PUSH: [
        M.PETTO, M.DELT_ANT, M.DELT_LAT, M.TRICIPITI,
    ],
    RuoloSessione.PULL: [
        M.DORSALI, M.DELT_POST, M.BICIPITI, M.TRAPEZIO, M.AVAMBRACCI,
    ],
    RuoloSessione.LEGS: [
        M.QUADRICIPITI, M.FEMORALI, M.GLUTEI, M.POLPACCI,
        M.ADDUTTORI, M.CORE,
    ],
}


# ════════════════════════════════════════════════════════════
# NOMI SESSIONE — Etichette descrittive per ruolo
# ════════════════════════════════════════════════════════════

NOMI_SESSIONE: dict[RuoloSessione, str] = {
    RuoloSessione.FULL_BODY: "Full Body",
    RuoloSessione.UPPER: "Upper Body",
    RuoloSessione.LOWER: "Lower Body",
    RuoloSessione.PUSH: "Push",
    RuoloSessione.PULL: "Pull",
    RuoloSessione.LEGS: "Legs",
}

FOCUS_SESSIONE: dict[RuoloSessione, str] = {
    RuoloSessione.FULL_BODY: "tutti i gruppi muscolari",
    RuoloSessione.UPPER: "petto, dorsali, spalle, braccia",
    RuoloSessione.LOWER: "quadricipiti, femorali, glutei, polpacci",
    RuoloSessione.PUSH: "petto, deltoidi anteriori/laterali, tricipiti",
    RuoloSessione.PULL: "dorsali, deltoidi posteriori, bicipiti, trapezio",
    RuoloSessione.LEGS: "quadricipiti, femorali, glutei, polpacci",
}


# ════════════════════════════════════════════════════════════
# API PUBBLICA
# ════════════════════════════════════════════════════════════


def get_split(frequenza: int) -> TipoSplit:
    """
    Ritorna lo split ottimale per la frequenza specificata (2-6).

    Regola (NSCA 2016, Schoenfeld 2016):
      2-3 → Full Body (unico modo per freq 2x/muscolo con poche sessioni)
      4-5 → Upper/Lower (split naturale con freq 2x/muscolo garantita)
      6   → PPL (volume distribuito, freq 2x esatta per ogni catena)

    Raises: ValueError se frequenza non in [2, 6].
    """
    if frequenza not in SPLIT_PER_FREQUENZA:
        raise ValueError(
            f"Frequenza {frequenza} non supportata. Range valido: 2-6 sessioni/settimana."
        )
    return SPLIT_PER_FREQUENZA[frequenza]


def get_session_roles(frequenza: int) -> list[RuoloSessione]:
    """
    Ritorna la lista ordinata dei ruoli sessione per la settimana.

    L'ordine rappresenta la sequenza consigliata dei giorni.
    Per upper/lower: alternanza U-L per ottimizzare recupero (NSCA 2016).
    Per PPL: sequenza P-P-L ripetuta (ogni catena ha 48h+ di recupero).
    """
    split = get_split(frequenza)
    return SESSIONI_PER_SPLIT[(split, frequenza)]


def get_patterns_for_role(ruolo: RuoloSessione) -> list[P]:
    """Ritorna i pattern compound assegnati a un ruolo sessione."""
    return PATTERN_COMPOUND_PER_RUOLO[ruolo]


def get_muscles_for_role(ruolo: RuoloSessione) -> list[M]:
    """Ritorna i gruppi muscolari principali di un ruolo sessione."""
    return MUSCOLI_PER_RUOLO[ruolo]


def compute_frequency_per_muscle(
    frequenza: int,
) -> dict[M, int]:
    """
    Calcola la frequenza settimanale per ogni muscolo dato lo split.

    Conta quante sessioni nella settimana includono pattern che
    attivano ogni muscolo (contributo >= 0.4, ovvero sinergista minore+).

    Questa e' una verifica fondamentale: se un muscolo ha freq < 2,
    il piano va corretto con isolamento aggiuntivo.

    Soglia 0.4 (Schoenfeld 2017): sotto il 40% di attivazione EMG
    il volume non e' sufficiente per contare come stimolo allenante.
    """
    roles = get_session_roles(frequenza)
    freq: dict[M, int] = {m: 0 for m in M}

    for ruolo in roles:
        patterns = PATTERN_COMPOUND_PER_RUOLO[ruolo]
        muscoli_stimolati: set[M] = set()

        for pattern in patterns:
            contribution = CONTRIBUTION_MATRIX.get(pattern, {})
            for muscolo, valore in contribution.items():
                if valore >= 0.4:
                    muscoli_stimolati.add(muscolo)

        for muscolo in muscoli_stimolati:
            freq[muscolo] += 1

    return freq


def identify_underhit_muscles(
    frequenza: int, min_freq: int = 2
) -> list[M]:
    """
    Identifica muscoli che non raggiungono la frequenza minima.

    Questi muscoli necessitano di isolamento aggiuntivo nel piano.
    La frequenza minima di default e' 2 (Schoenfeld 2016).
    """
    freq = compute_frequency_per_muscle(frequenza)
    return [m for m, f in freq.items() if f < min_freq]


def get_session_structure(
    frequenza: int,
    obiettivo: Obiettivo,
    livello: Livello,
) -> list[tuple[RuoloSessione, list[P]]]:
    """
    Ritorna la struttura settimanale: lista di (ruolo, pattern_compound).

    Questo e' l'input per il plan_builder che dovra' assegnare
    serie e aggiungere isolamento dove necessario.
    """
    roles = get_session_roles(frequenza)
    return [(r, PATTERN_COMPOUND_PER_RUOLO[r]) for r in roles]
