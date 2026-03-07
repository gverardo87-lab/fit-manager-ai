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
#
# Calf_raise e' incluso come pattern obbligatorio in sessioni
# lower/legs/full_body perche' i polpacci non ricevono volume
# ipertrofico sufficiente da squat (contributo 0.2 = sotto soglia
# EMG 40% MVC). Schoenfeld 2019: calves richiedono lavoro diretto.
#
# P.CORE RIMOSSO da full_body/lower/legs: il core riceve volume
# ipertrofico sufficiente da carry (0.7), rotation (0.7),
# squat (0.4) e hinge (0.4). L'aggiunta esplicita di core
# causa overaccumulation sistematica oltre MRV.
# Fonte: Israetel RP 2020 — "direct core work is optional when
# the program includes heavy compounds." Se il core risultasse
# sotto MAV, il plan_builder lo compensera' con isolamento (Fase 3).

# ── FULL BODY ROTATION ──
# 9 pattern in UNA sessione full body = troppe (NSCA 2016: 5-6 esercizi
# per sessione per principiante). Soluzione scientifica standard
# (Helms 2019): distribuire i pattern su piu' varianti complementari.
#
# 2x/sett: A/B
# 3x/sett: A/B/C
#
# A (orizzontale + squat): push_h, pull_h, squat, carry, calf_raise
# B (verticale + posteriore): push_v, pull_v, hinge, rotation
# C (rebalance): squat, hinge, push_h, push_v, pull_h, pull_v
#
# La variante C esiste per la frequenza 3x:
# - riallinea i rapporti orizzontale/verticale
# - porta la catena posteriore a 2 esposizioni/settimana
# - riduce il rischio che A/B/A lasci push_v, pull_v e femorali a 1x

_FULL_BODY_VARIANTS: list[list[P]] = [
    # Variante A — piani orizzontali + squat + carry funzionale
    [P.PUSH_H, P.PULL_H, P.SQUAT, P.CARRY, P.CALF_RAISE],
    # Variante B — piani verticali + hinge + rotazione trasversale
    [P.PUSH_V, P.PULL_V, P.HINGE, P.ROTATION],
    # Variante C — sessione mista per riequilibrare upper/lower su 3x
    [P.SQUAT, P.HINGE, P.PULL_H, P.PULL_V, P.PUSH_H, P.PUSH_V],
]


def get_full_body_patterns(session_index: int) -> list[P]:
    """
    Ritorna i pattern per la sessione full body N-esima (0-indexed).

    Ruota A/B/C per distribuire i pattern su sessioni diverse.
    Con 2x il risultato e' A/B. Con 3x il risultato e' A/B/C.
    """
    return _FULL_BODY_VARIANTS[session_index % len(_FULL_BODY_VARIANTS)]


PATTERN_COMPOUND_PER_RUOLO: dict[RuoloSessione, list[P]] = {
    # Master list: tutti i pattern possibili per full body.
    # Il plan_builder usa get_full_body_patterns() per il subset A/B/C.
    RuoloSessione.FULL_BODY: [
        P.PUSH_H, P.PUSH_V, P.PULL_H, P.PULL_V,
        P.SQUAT, P.HINGE, P.ROTATION, P.CARRY,
        P.CALF_RAISE,
    ],
    RuoloSessione.UPPER: [
        P.PUSH_H, P.PUSH_V, P.PULL_H, P.PULL_V, P.ROTATION,
    ],
    RuoloSessione.LOWER: [
        P.SQUAT, P.HINGE, P.CARRY, P.CALF_RAISE,
    ],
    RuoloSessione.PUSH: [
        P.PUSH_H, P.PUSH_V,
    ],
    RuoloSessione.PULL: [
        P.PULL_H, P.PULL_V, P.ROTATION,
    ],
    RuoloSessione.LEGS: [
        P.SQUAT, P.HINGE, P.CARRY, P.CALF_RAISE,
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


# ════════════════════════════════════════════════════════════
# FREQUENZA MASSIMA PER LIVELLO — Guardrail scientifico
# ════════════════════════════════════════════════════════════
#
# NSCA 2016 (cap. 21-22) e Israetel RP 2020 definiscono range
# di frequenza ottimale per livello:
#   Principiante: 2-3 sessioni/sett (MRV basso, necessita recupero)
#   Intermedio: 2-5 sessioni/sett (MRV medio, tolleranza crescente)
#   Avanzato: 2-6 sessioni/sett (MRV alto, gestisce volume elevato)
#
# Se la frequenza richiesta eccede il massimo per il livello,
# viene clampata al massimo consentito con un warning.

FREQUENZA_MAX_PER_LIVELLO: dict[Livello, int] = {
    Livello.PRINCIPIANTE: 3,
    Livello.INTERMEDIO: 5,
    Livello.AVANZATO: 6,
}


def clamp_frequenza(frequenza: int, livello: Livello) -> tuple[int, str | None]:
    """
    Limita la frequenza al massimo scientifico per il livello.

    Ritorna (frequenza_effettiva, warning_opzionale).
    Se la frequenza e' entro il range, warning e' None.

    Fonte: NSCA 2016, Israetel RP 2020.
    """
    max_freq = FREQUENZA_MAX_PER_LIVELLO[livello]
    if frequenza > max_freq:
        warning = (
            f"Frequenza {frequenza}x ridotta a {max_freq}x per livello {livello.value}. "
            f"NSCA 2016: principianti necessitano piu' recupero, "
            f"MRV insufficiente per {frequenza} sessioni/sett."
        )
        return max_freq, warning
    return frequenza, None


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

    fb_index = 0
    for ruolo in roles:
        if ruolo == RuoloSessione.FULL_BODY:
            patterns = get_full_body_patterns(fb_index)
            fb_index += 1
        else:
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
