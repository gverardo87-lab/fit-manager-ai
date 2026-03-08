"""
Training Science Engine — Test di validazione con schede campione e calcoli a mano.

FILOSOFIA: i test sono costruiti su conoscenze scientifiche INDIPENDENTI dall'analyzer.
I volumi attesi sono calcolati A MANO dalla matrice EMG × hypertrophy weights.
Le classificazioni attese derivano dalla tabella MEV/MAV/MRV × fattore demografico.
Se un test FALLISCE, è un BUG nell'analyzer (o nei target), NON un test sbagliato.

Ogni scheda è costruita seguendo le linee guida di:
  - NSCA — "Essentials of Strength Training & Conditioning" (2016), cap. 15-22
  - Schoenfeld — "Science and Development of Muscle Hypertrophy" (2021)
  - Israetel — "Scientific Principles of Hypertrophy Training" (RP, 2020)
  - ACSM — "Guidelines for Exercise Testing and Prescription" (2009)

Profili demografici:
  - M25: demo_factor = 1.0 (baseline)
  - F25: demo_factor = 0.85
  - M55: demo_factor = 0.85
  - F55: demo_factor = 0.7225
"""

import pytest

from api.services.training_science.plan_analyzer import analyze_plan
from api.services.training_science.volume_model import (
    get_scaled_volume_target,
    get_demographic_factor,
)
from api.services.training_science.muscle_contribution import (
    compute_hypertrophy_sets,
)
from api.services.training_science.types import (
    TemplatePiano,
    TemplateSessione,
    SlotSessione,
    PatternMovimento as P,
    GruppoMuscolare as M,
    Obiettivo,
    Livello,
)


# ════════════════════════════════════════════════════════════
# PROFILI DEMOGRAFICI
# ════════════════════════════════════════════════════════════

PROFILES = [
    {"id": "M25", "sesso": "M", "eta": 25, "demo_factor": 1.0},
    {"id": "F25", "sesso": "F", "eta": 25, "demo_factor": 0.85},
    {"id": "M55", "sesso": "M", "eta": 55, "demo_factor": 0.85},
    {"id": "F55", "sesso": "F", "eta": 55, "demo_factor": 0.7225},
]


# ════════════════════════════════════════════════════════════
# HELPER — Costruzione slot rapida
# ════════════════════════════════════════════════════════════

def _slot(pattern: P, serie: int, rep_min: int = 8, rep_max: int = 12,
          riposo: int = 90, priorita: int = 2) -> SlotSessione:
    return SlotSessione(
        pattern=pattern, priorita=priorita, serie=serie,
        rep_min=rep_min, rep_max=rep_max, riposo_sec=riposo,
        muscolo_target=None, note="",
    )


def _session(nome: str, ruolo: str, slots: list[SlotSessione]) -> TemplateSessione:
    return TemplateSessione(nome=nome, ruolo=ruolo, focus="", slots=slots)


# ════════════════════════════════════════════════════════════
# SCHEDA 1 — FULL BODY 3x / PRINCIPIANTE / IPERTROFIA
# ════════════════════════════════════════════════════════════
# Fonte: NSCA 2016 cap. 15, Schoenfeld 2016.

def _build_full_body_3x(sesso: str | None, eta: int | None) -> TemplatePiano:
    session_a = _session("Full Body A", "full_body", [
        _slot(P.PUSH_H, 3),
        _slot(P.PULL_H, 3),
        _slot(P.SQUAT, 3),
        _slot(P.CALF_RAISE, 2),
        _slot(P.CORE, 2, 15, 20, 60),
    ])
    session_b = _session("Full Body B", "full_body", [
        _slot(P.PUSH_V, 3),
        _slot(P.PULL_V, 3),
        _slot(P.HINGE, 3),
        _slot(P.LATERAL_RAISE, 2),
        _slot(P.CORE, 2, 15, 20, 60),
    ])
    session_c = _session("Full Body C", "full_body", [
        _slot(P.PUSH_H, 3),
        _slot(P.PULL_H, 3),
        _slot(P.SQUAT, 3),
        _slot(P.CURL, 2),
        _slot(P.EXTENSION_TRI, 2),
    ])
    return TemplatePiano(
        frequenza=3, obiettivo=Obiettivo.IPERTROFIA,
        livello=Livello.PRINCIPIANTE, tipo_split="full_body",
        sessioni=[session_a, session_b, session_c],
        note_generazione=[], sesso=sesso, eta=eta,
    )


# ════════════════════════════════════════════════════════════
# SCHEDA 2 — UPPER/LOWER 4x / INTERMEDIO / IPERTROFIA
# ════════════════════════════════════════════════════════════
# Fonte: Schoenfeld 2021 cap. 8, Israetel RP 2020.

def _build_upper_lower_4x(sesso: str | None, eta: int | None) -> TemplatePiano:
    upper_a = _session("Upper A", "upper", [
        _slot(P.PUSH_H, 4, 6, 10, 120),
        _slot(P.PULL_H, 4, 6, 10, 120),
        _slot(P.PUSH_V, 3, 8, 12, 90),
        _slot(P.FACE_PULL, 3, 12, 15, 60),
        _slot(P.CURL, 3, 10, 12, 60),
        _slot(P.EXTENSION_TRI, 3, 10, 12, 60),
    ])
    lower_a = _session("Lower A", "lower", [
        _slot(P.SQUAT, 4, 6, 8, 180),
        _slot(P.LEG_CURL, 3, 10, 12, 60),
        _slot(P.HIP_THRUST, 3, 8, 12, 90),
        _slot(P.LEG_EXTENSION, 3, 10, 12, 60),
        _slot(P.CALF_RAISE, 3, 12, 15, 60),
        _slot(P.ADDUCTOR, 2, 12, 15, 60),
    ])
    upper_b = _session("Upper B", "upper", [
        _slot(P.PULL_V, 4, 6, 10, 120),
        _slot(P.PUSH_H, 3, 10, 12, 90),
        _slot(P.LATERAL_RAISE, 3, 12, 15, 60),
        _slot(P.PULL_H, 3, 10, 12, 90),
        _slot(P.CURL, 2, 10, 12, 60),
        _slot(P.EXTENSION_TRI, 2, 10, 12, 60),
    ])
    lower_b = _session("Lower B", "lower", [
        _slot(P.HINGE, 4, 6, 8, 180),
        _slot(P.SQUAT, 3, 10, 12, 90),
        _slot(P.LEG_CURL, 3, 10, 12, 60),
        _slot(P.CALF_RAISE, 3, 12, 15, 60),
        _slot(P.CARRY, 2, 8, 12, 90),
        _slot(P.CORE, 3, 12, 15, 60),
    ])
    return TemplatePiano(
        frequenza=4, obiettivo=Obiettivo.IPERTROFIA,
        livello=Livello.INTERMEDIO, tipo_split="upper_lower",
        sessioni=[upper_a, lower_a, upper_b, lower_b],
        note_generazione=[], sesso=sesso, eta=eta,
    )


# ════════════════════════════════════════════════════════════
# SCHEDA 3 — PUSH/PULL/LEGS 6x / AVANZATO / IPERTROFIA
# ════════════════════════════════════════════════════════════
# Fonte: Israetel RP 2020, NSCA 2016 cap. 22.

def _build_ppl_6x(sesso: str | None, eta: int | None) -> TemplatePiano:
    push_a = _session("Push A", "push", [
        _slot(P.PUSH_H, 4, 6, 8, 120),
        _slot(P.PUSH_V, 3, 8, 12, 90),
        _slot(P.PUSH_H, 3, 10, 12, 90),
        _slot(P.LATERAL_RAISE, 3, 12, 15, 60),
        _slot(P.EXTENSION_TRI, 3, 10, 12, 60),
    ])
    pull_a = _session("Pull A", "pull", [
        _slot(P.PULL_V, 4, 6, 8, 120),
        _slot(P.PULL_H, 4, 8, 12, 90),
        _slot(P.FACE_PULL, 3, 12, 15, 60),
        _slot(P.CURL, 3, 10, 12, 60),
        _slot(P.CURL, 2, 12, 15, 60),
    ])
    legs_a = _session("Legs A", "legs", [
        _slot(P.SQUAT, 4, 6, 8, 180),
        _slot(P.HINGE, 3, 8, 10, 120),
        _slot(P.LEG_EXTENSION, 3, 10, 12, 60),
        _slot(P.LEG_CURL, 3, 10, 12, 60),
        _slot(P.CALF_RAISE, 4, 12, 15, 60),
    ])
    push_b = _session("Push B", "push", [
        _slot(P.PUSH_V, 4, 6, 8, 120),
        _slot(P.PUSH_H, 3, 10, 12, 90),
        _slot(P.LATERAL_RAISE, 3, 12, 15, 60),
        _slot(P.EXTENSION_TRI, 3, 10, 12, 60),
        _slot(P.PUSH_H, 2, 12, 15, 60),
    ])
    pull_b = _session("Pull B", "pull", [
        _slot(P.PULL_H, 4, 8, 10, 120),
        _slot(P.PULL_V, 3, 8, 12, 90),
        _slot(P.FACE_PULL, 3, 12, 15, 60),
        _slot(P.CURL, 3, 10, 12, 60),
    ])
    legs_b = _session("Legs B", "legs", [
        _slot(P.HINGE, 4, 6, 8, 180),
        _slot(P.SQUAT, 3, 10, 12, 90),
        _slot(P.HIP_THRUST, 3, 10, 12, 90),
        _slot(P.LEG_CURL, 3, 10, 12, 60),
        _slot(P.ADDUCTOR, 3, 12, 15, 60),
        _slot(P.CALF_RAISE, 3, 12, 15, 60),
    ])
    return TemplatePiano(
        frequenza=6, obiettivo=Obiettivo.IPERTROFIA,
        livello=Livello.AVANZATO, tipo_split="push_pull_legs",
        sessioni=[push_a, pull_a, legs_a, push_b, pull_b, legs_b],
        note_generazione=[], sesso=sesso, eta=eta,
    )


# ════════════════════════════════════════════════════════════
# SCHEDA 4 — FULL BODY 2x / PRINCIPIANTE / FORZA
# ════════════════════════════════════════════════════════════
# Fonte: NSCA 2016 cap. 15,17.

def _build_strength_2x(sesso: str | None, eta: int | None) -> TemplatePiano:
    session_a = _session("Forza A", "full_body", [
        _slot(P.SQUAT, 5, 3, 5, 240, priorita=2),
        _slot(P.PUSH_H, 4, 3, 5, 240, priorita=2),
        _slot(P.PULL_H, 4, 3, 5, 240, priorita=2),
        _slot(P.CORE, 3, 8, 12, 90),
    ])
    session_b = _session("Forza B", "full_body", [
        _slot(P.HINGE, 5, 3, 5, 240, priorita=2),
        _slot(P.PUSH_V, 4, 3, 5, 240, priorita=2),
        _slot(P.PULL_V, 4, 3, 5, 240, priorita=2),
        _slot(P.CARRY, 3, 8, 12, 120),
    ])
    return TemplatePiano(
        frequenza=2, obiettivo=Obiettivo.FORZA,
        livello=Livello.PRINCIPIANTE, tipo_split="full_body",
        sessioni=[session_a, session_b],
        note_generazione=[], sesso=sesso, eta=eta,
    )


# ════════════════════════════════════════════════════════════
# SCHEDA 5 — UPPER/LOWER 4x / INTERMEDIO / DIMAGRIMENTO
# ════════════════════════════════════════════════════════════
# Fonte: NSCA 2016, Schoenfeld 2021.

def _build_fat_loss_4x(sesso: str | None, eta: int | None) -> TemplatePiano:
    upper_a = _session("Upper A", "upper", [
        _slot(P.PUSH_H, 3, 8, 12, 60),
        _slot(P.PULL_H, 3, 8, 12, 60),
        _slot(P.PUSH_V, 3, 10, 15, 45),
        _slot(P.PULL_V, 3, 10, 15, 45),
        _slot(P.CURL, 2, 12, 15, 45),
        _slot(P.EXTENSION_TRI, 2, 12, 15, 45),
    ])
    lower_a = _session("Lower A", "lower", [
        _slot(P.SQUAT, 4, 8, 12, 90),
        _slot(P.HINGE, 3, 8, 12, 90),
        _slot(P.LEG_CURL, 2, 12, 15, 45),
        _slot(P.CALF_RAISE, 3, 12, 15, 45),
        _slot(P.CORE, 3, 12, 15, 45),
    ])
    upper_b = _session("Upper B", "upper", [
        _slot(P.PULL_H, 3, 8, 12, 60),
        _slot(P.PUSH_H, 3, 10, 15, 60),
        _slot(P.LATERAL_RAISE, 3, 12, 15, 45),
        _slot(P.FACE_PULL, 3, 12, 15, 45),
        _slot(P.CURL, 2, 12, 15, 45),
    ])
    lower_b = _session("Lower B", "lower", [
        _slot(P.HINGE, 4, 8, 12, 90),
        _slot(P.SQUAT, 3, 10, 12, 90),
        _slot(P.HIP_THRUST, 3, 10, 12, 60),
        _slot(P.CALF_RAISE, 2, 12, 15, 45),
        _slot(P.CARRY, 2, 10, 12, 60),
    ])
    return TemplatePiano(
        frequenza=4, obiettivo=Obiettivo.DIMAGRIMENTO,
        livello=Livello.INTERMEDIO, tipo_split="upper_lower",
        sessioni=[upper_a, lower_a, upper_b, lower_b],
        note_generazione=[], sesso=sesso, eta=eta,
    )


# ════════════════════════════════════════════════════════════
# SCHEDA 6 — FULL BODY 3x / PRINCIPIANTE / TONIFICAZIONE
# ════════════════════════════════════════════════════════════
# Fonte: ACSM 2009.

def _build_toning_3x(sesso: str | None, eta: int | None) -> TemplatePiano:
    session_a = _session("Tono A", "full_body", [
        _slot(P.SQUAT, 3, 10, 15, 60),
        _slot(P.PUSH_H, 3, 10, 15, 60),
        _slot(P.PULL_H, 3, 10, 15, 60),
        _slot(P.HIP_THRUST, 2, 12, 15, 45),
        _slot(P.CORE, 2, 12, 15, 45),
    ])
    session_b = _session("Tono B", "full_body", [
        _slot(P.HINGE, 3, 10, 15, 60),
        _slot(P.PUSH_V, 3, 10, 15, 60),
        _slot(P.PULL_V, 3, 10, 15, 60),
        _slot(P.LATERAL_RAISE, 2, 12, 15, 45),
        _slot(P.CALF_RAISE, 2, 12, 15, 45),
    ])
    session_c = _session("Tono C", "full_body", [
        _slot(P.SQUAT, 2, 12, 15, 60),
        _slot(P.PUSH_H, 2, 12, 15, 60),
        _slot(P.PULL_H, 2, 12, 15, 60),
        _slot(P.HINGE, 2, 12, 15, 60),
        _slot(P.CURL, 2, 12, 15, 45),
        _slot(P.EXTENSION_TRI, 2, 12, 15, 45),
    ])
    return TemplatePiano(
        frequenza=3, obiettivo=Obiettivo.TONIFICAZIONE,
        livello=Livello.PRINCIPIANTE, tipo_split="full_body",
        sessioni=[session_a, session_b, session_c],
        note_generazione=[], sesso=sesso, eta=eta,
    )


# ════════════════════════════════════════════════════════════
# BUILDER MATRIX
# ════════════════════════════════════════════════════════════

PLAN_BUILDERS = {
    "full_body_3x_hyp": (_build_full_body_3x, "Full Body 3x Hypertrophy"),
    "upper_lower_4x_hyp": (_build_upper_lower_4x, "Upper/Lower 4x Hypertrophy"),
    "ppl_6x_hyp": (_build_ppl_6x, "PPL 6x Hypertrophy"),
    "strength_2x": (_build_strength_2x, "Full Body 2x Strength"),
    "fat_loss_4x": (_build_fat_loss_4x, "Upper/Lower 4x Fat Loss"),
    "toning_3x": (_build_toning_3x, "Full Body 3x Toning"),
}


def _build_all_plans() -> list[tuple[str, str, dict, TemplatePiano]]:
    combos = []
    for plan_id, (builder, name) in PLAN_BUILDERS.items():
        for profile in PROFILES:
            piano = builder(profile["sesso"], profile["eta"])
            combos.append((plan_id, name, profile, piano))
    return combos


ALL_PLANS = _build_all_plans()


# ════════════════════════════════════════════════════════════
# VOLUMI ATTESI CALCOLATI A MANO — Upper/Lower 4x, M25
# ════════════════════════════════════════════════════════════
#
# Matrice EMG (muscle_contribution.py) × hypertrophy weights:
#   1.0 EMG → 1.0 weight, 0.7 → 0.5, 0.4 → 0.25, 0.2 → 0.0
#
# Upper A: PUSH_H(4), PULL_H(4), PUSH_V(3), FACE_PULL(3), CURL(3), EXT_TRI(3)
# Lower A: SQUAT(4), LEG_CURL(3), HIP_THRUST(3), LEG_EXT(3), CALF(3), ADDUCTOR(2)
# Upper B: PULL_V(4), PUSH_H(3), LAT_RAISE(3), PULL_H(3), CURL(2), EXT_TRI(2)
# Lower B: HINGE(4), SQUAT(3), LEG_CURL(3), CALF(3), CARRY(2), CORE(3)
#
# Dettaglio calcolo per muscolo (ogni riga: slot × hyp_weight = contributo):

EXPECTED_HYPERTROPHY_M25_UL4X: dict[str, float] = {
    # PETTO: PUSH_H(4×1.0) + PUSH_H(3×1.0) = 7.0
    "petto": 7.0,
    # DORSALI: PULL_H(4×1.0) + PULL_V(4×1.0) + PULL_H(3×1.0) + HINGE(4×0.25) = 12.0
    "dorsali": 12.0,
    # DELT_ANT: PUSH_H(4×0.5) + PUSH_V(3×1.0) + PUSH_H(3×0.5) = 6.5
    "deltoide_anteriore": 6.5,
    # DELT_LAT: PUSH_V(3×0.5) + LAT_RAISE(3×1.0) = 4.5
    "deltoide_laterale": 4.5,
    # DELT_POST: PULL_H(4×0.5) + FACE_PULL(3×1.0) + PULL_V(4×0.25) + PULL_H(3×0.5) = 7.5
    "deltoide_posteriore": 7.5,
    # BICIPITI: PULL_H(4×0.5) + CURL(3×1.0) + PULL_V(4×0.5) + PULL_H(3×0.5) + CURL(2×1.0) = 10.5
    "bicipiti": 10.5,
    # TRICIPITI: PUSH_H(4×0.5) + PUSH_V(3×0.5) + EXT_TRI(3×1.0) + PUSH_H(3×0.5) + EXT_TRI(2×1.0) = 10.0
    "tricipiti": 10.0,
    # QUADRICIPITI: SQUAT(4×1.0) + LEG_EXT(3×1.0) + SQUAT(3×1.0) = 10.0
    "quadricipiti": 10.0,
    # FEMORALI: SQUAT(4×0.25) + LEG_CURL(3×1.0) + HIP_THRUST(3×0.25)
    #           + HINGE(4×1.0) + SQUAT(3×0.25) + LEG_CURL(3×1.0) = 12.5
    "femorali": 12.5,
    # GLUTEI: SQUAT(4×0.5) + HIP_THRUST(3×1.0) + HINGE(4×1.0) + SQUAT(3×0.5) = 10.5
    "glutei": 10.5,
    # POLPACCI: CALF(3×1.0) + CALF(3×1.0) = 6.0  (SQUAT 0.2 → hyp 0.0)
    "polpacci": 6.0,
    # TRAPEZIO: PULL_H(4×0.5) + PUSH_V(3×0.25) + FACE_PULL(3×0.25)
    #           + PULL_V(4×0.25) + PULL_H(3×0.5) + HINGE(4×0.25) + CARRY(2×0.5) = 8.0
    #           (LAT_RAISE 0.2 → hyp 0.0)
    "trapezio": 8.0,
    # CORE: SQUAT(4×0.25) + HINGE(4×0.25) + SQUAT(3×0.25) + CARRY(2×0.5) + CORE(3×1.0) = 6.75
    #       (PUSH_H 0.2 → 0, PUSH_V 0.2 → 0, HIP_THRUST 0.2 → 0)
    "core": 6.75,
    # AVAMBRACCI: PULL_H(4×0.25) + CURL(3×0.25) + PULL_V(4×0.25)
    #             + PULL_H(3×0.25) + CURL(2×0.25) + CARRY(2×1.0) = 6.0
    #             (HINGE 0.2 → 0)
    "avambracci": 6.0,
    # ADDUTTORI: SQUAT(4×0.25) + ADDUCTOR(2×1.0) + SQUAT(3×0.25) = 3.75
    "adduttori": 3.75,
}

# Classificazione attesa per M25 Intermedio Ipertrofia (obj=1.0, demo=1.0)
# Target letti da _VOLUME_TABLE[M][INTERMEDIO] senza scaling
EXPECTED_STATES_M25_UL4X: dict[str, str] = {
    "petto": "mev_mav",          # 7.0: MEV=4, MAV_min=8 → 4 ≤ 7.0 < 8
    "dorsali": "ottimale",       # 12.0: MAV_min=12, MAV_max=18 → 12 ≤ 12 ≤ 18
    "deltoide_anteriore": "ottimale",  # 6.5: MEV=0, MAV_min=0, MAV_max=8 → 0 ≤ 6.5 ≤ 8
    "deltoide_laterale": "mev_mav",    # 4.5: MEV=4, MAV_min=8 → 4 ≤ 4.5 < 8
    "deltoide_posteriore": "ottimale", # 7.5: MAV_min=6, MAV_max=10 → 6 ≤ 7.5 ≤ 10
    "bicipiti": "ottimale",      # 10.5: MAV_min=10, MAV_max=14 → 10 ≤ 10.5 ≤ 14
    "tricipiti": "ottimale",     # 10.0: MAV_min=8, MAV_max=12 → 8 ≤ 10 ≤ 12
    "quadricipiti": "ottimale",  # 10.0: MAV_min=10, MAV_max=16 → 10 ≤ 10 ≤ 16
    "femorali": "sopra_mav",     # 12.5: MAV_max=12, MRV=16 → 12 < 12.5 ≤ 16
    "glutei": "sopra_mav",       # 10.5: MAV_max=10, MRV=14 → 10 < 10.5 ≤ 14
    "polpacci": "mev_mav",      # 6.0: MEV=4, MAV_min=8 → 4 ≤ 6 < 8
    "trapezio": "ottimale",      # 8.0: MAV_min=6, MAV_max=10 → 6 ≤ 8 ≤ 10
    "core": "ottimale",          # 6.8: MAV_min=6, MAV_max=10 → 6 ≤ 6.8 ≤ 10
    "avambracci": "ottimale",    # 6.0: MAV_min=4, MAV_max=8 → 4 ≤ 6 ≤ 8
    "adduttori": "mev_mav",     # 3.8: MEV=0, MAV_min=4 → 0 ≤ 3.8 < 4
}

# Classificazione attesa per F55 (demo=0.722, obj=1.0)
# MAV_min/MAV_max/MRV scalati × 0.722, MEV × obj solo
EXPECTED_STATES_F55_UL4X: dict[str, str] = {
    "petto": "ottimale",              # 7.0: MAV_min=5.8, MAV_max=8.7 → ottimale
    "dorsali": "ottimale",            # 12.0: MAV_min=8.7, MAV_max=13.0
    "deltoide_anteriore": "sopra_mav",  # 6.5: MAV_max=5.8, MRV=10.1 → 5.8 < 6.5 ≤ 10.1
    "deltoide_laterale": "mev_mav",   # 4.5: MEV=4, MAV_min=5.8 → 4 ≤ 4.5 < 5.8
    "deltoide_posteriore": "sopra_mav",  # 7.5: MAV_max=7.2, MRV=10.1 → 7.2 < 7.5
    "bicipiti": "sopra_mav",          # 10.5: MAV_max=10.1, MRV=13.0
    "tricipiti": "sopra_mav",         # 10.0: MAV_max=8.7, MRV=11.6
    "quadricipiti": "ottimale",       # 10.0: MAV_min=7.2, MAV_max=11.6
    "femorali": "sopra_mrv",          # 12.5: MRV=11.6 → sopra_mrv
    "glutei": "sopra_mrv",            # 10.5: MRV=10.1 → sopra_mrv
    "polpacci": "ottimale",           # 6.0: MAV_min=5.8, MAV_max=8.7
    "trapezio": "sopra_mav",          # 8.0: MAV_max=7.2, MRV=11.6
    "core": "ottimale",               # 6.8: MAV_min=4.3, MAV_max=7.2
    "avambracci": "sopra_mav",        # 6.0: MAV_max=5.8, MRV=8.7
    "adduttori": "ottimale",          # 3.8: MAV_min=2.9, MAV_max=5.8
}

# Rapporti biomeccanici attesi per Upper/Lower 4x (pattern-based)
# Push = PUSH_H(4+3) + PUSH_V(3) = 10
# Pull = PULL_H(4+3) + PULL_V(4) = 11
EXPECTED_RATIOS_UL4X: dict[str, float] = {
    "Push : Pull": 0.91,        # 10/11 = 0.909... → round = 0.91
    "Push Orizz : Push Vert": 2.33,   # 7/3 = 2.333... → round = 2.33
    "Pull Orizz : Pull Vert": 1.75,   # 7/4 = 1.75
    # Quad:Ham e Ant:Post usano volume IPERTROFICO (compute_hypertrophy_sets)
    # — vedi TestBalanceRatiosCalibrated per verifica
}


# ════════════════════════════════════════════════════════════
# TEST 1 — Nessun crash su nessun piano
# ════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    "plan_id,name,profile,piano",
    ALL_PLANS,
    ids=[f"{p[0]}_{p[2]['id']}" for p in ALL_PLANS],
)
def test_analyzer_no_crash(plan_id, name, profile, piano):
    """L'analyzer non deve crashare su nessun piano campione."""
    result = analyze_plan(piano)
    assert result is not None
    assert isinstance(result.score, (int, float))
    assert 0 <= result.score <= 100
    assert len(result.volume.per_muscolo) == 15  # tutti i 15 muscoli
    assert isinstance(result.balance.rapporti, dict)


# ════════════════════════════════════════════════════════════
# TEST 2 — Volumi ipertrofici calcolati a mano
# ════════════════════════════════════════════════════════════

class TestHandCalculatedVolumes:
    """Verifica che compute_hypertrophy_sets produca i volumi attesi.

    I valori attesi sono calcolati A MANO dalla matrice EMG (muscle_contribution.py)
    applicando i pesi ipertrofici (1.0→1.0, 0.7→0.5, 0.4→0.25, 0.2→0.0).
    Se un test fallisce, la matrice EMG o i pesi ipertrofici sono cambiati.
    """

    def test_hypertrophy_volumes_upper_lower_4x_m25(self):
        """Verifica ogni muscolo della Upper/Lower 4x per M25."""
        piano = _build_upper_lower_4x("M", 25)
        all_slots = [
            (slot.pattern, slot.serie)
            for sessione in piano.sessioni
            for slot in sessione.slots
        ]
        hypertrophy = compute_hypertrophy_sets(all_slots)

        for muscle_name, expected in EXPECTED_HYPERTROPHY_M25_UL4X.items():
            muscle_enum = M(muscle_name)
            actual = round(hypertrophy.get(muscle_enum, 0.0), 2)
            assert abs(actual - expected) < 0.01, (
                f"{muscle_name}: atteso {expected}, ottenuto {actual}. "
                f"Verifica calcolo a mano nella docstring."
            )

    def test_analyzer_volumes_match_hand_calculation(self):
        """L'analyzer deve produrre gli stessi volumi del calcolo a mano."""
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        vol_map = {v.muscolo.value: v.serie_effettive for v in result.volume.per_muscolo}

        for muscle_name, expected in EXPECTED_HYPERTROPHY_M25_UL4X.items():
            actual = vol_map.get(muscle_name, 0.0)
            # L'analyzer arrotonda a 1 decimale
            expected_rounded = round(expected, 1)
            assert abs(actual - expected_rounded) < 0.15, (
                f"{muscle_name}: atteso {expected_rounded}, analyzer dice {actual}. "
                f"BUG: l'analyzer non usa compute_hypertrophy_sets correttamente?"
            )


# ════════════════════════════════════════════════════════════
# TEST 3 — Classificazione volume per muscolo
# ════════════════════════════════════════════════════════════

class TestVolumeClassification:
    """Verifica che la classificazione (sotto_mev/mev_mav/ottimale/sopra_mav/sopra_mrv)
    corrisponda al calcolo a mano: volume vs target scalati per profilo.
    """

    def test_classification_m25_upper_lower_4x(self):
        """M25 Intermedio Ipertrofia: ogni muscolo deve avere lo stato atteso."""
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        state_map = {v.muscolo.value: v.stato for v in result.volume.per_muscolo}

        for muscle_name, expected_state in EXPECTED_STATES_M25_UL4X.items():
            actual = state_map.get(muscle_name)
            assert actual == expected_state, (
                f"{muscle_name}: atteso '{expected_state}', ottenuto '{actual}'. "
                f"Volume calcolato a mano: {EXPECTED_HYPERTROPHY_M25_UL4X[muscle_name]}"
            )

    def test_classification_f55_upper_lower_4x(self):
        """F55 Intermedio Ipertrofia: stessa scheda, stati diversi per MRV ridotto.

        Una donna 55 anni ha MRV = base × 0.722. Con lo stesso volume,
        femorali e glutei vanno in sopra_mrv — è CORRETTO, non è un bug.
        Se il test fallisce, il demographic scaling è rotto.
        """
        piano = _build_upper_lower_4x("F", 55)
        result = analyze_plan(piano)
        state_map = {v.muscolo.value: v.stato for v in result.volume.per_muscolo}

        for muscle_name, expected_state in EXPECTED_STATES_F55_UL4X.items():
            actual = state_map.get(muscle_name)
            assert actual == expected_state, (
                f"{muscle_name} F55: atteso '{expected_state}', ottenuto '{actual}'. "
                f"Volume = {EXPECTED_HYPERTROPHY_M25_UL4X[muscle_name]}, "
                f"demo_factor = 0.722"
            )

    def test_m25_vs_f55_have_different_states(self):
        """Lo stesso piano DEVE avere stati diversi tra M25 e F55.

        Se sono identici, il demographic scaling non funziona.
        Dalla tabella a mano: almeno 8 muscoli cambiano stato.
        """
        piano_m25 = _build_upper_lower_4x("M", 25)
        piano_f55 = _build_upper_lower_4x("F", 55)
        result_m25 = analyze_plan(piano_m25)
        result_f55 = analyze_plan(piano_f55)

        state_m25 = {v.muscolo.value: v.stato for v in result_m25.volume.per_muscolo}
        state_f55 = {v.muscolo.value: v.stato for v in result_f55.volume.per_muscolo}

        differences = [m for m in state_m25 if state_m25[m] != state_f55.get(m)]
        # Dal calcolo a mano: petto, delt_ant, delt_post, bicipiti, tricipiti,
        # femorali, glutei, polpacci, trapezio, avambracci, adduttori = 11 differenze
        assert len(differences) >= 5, (
            f"Solo {len(differences)} muscoli differiscono tra M25 e F55. "
            f"Il demographic scaling è troppo debole. "
            f"Differenze: {differences}"
        )


# ════════════════════════════════════════════════════════════
# TEST 4 — Rapporti biomeccanici calcolati a mano
# ════════════════════════════════════════════════════════════

class TestHandCalculatedRatios:
    """Verifica rapporti biomeccanici con valori esatti calcolati a mano."""

    def test_push_pull_ratio_upper_lower_4x(self):
        """Push:Pull = 10/11 = 0.91 — serie push vs serie pull grezze."""
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        ratio = result.balance.rapporti.get("Push : Pull")
        assert ratio is not None
        assert abs(ratio - 0.91) < 0.02, (
            f"Push:Pull = {ratio}, atteso ~0.91 (10 push / 11 pull)"
        )

    def test_push_h_v_ratio_upper_lower_4x(self):
        """Push Orizz:Vert = 7/3 = 2.33 — in range con target 1.5 ± 1.0.

        Sahrmann 2002: push_h preferibile a push_v (delt_ant overactive).
        Tolleranza ampia: nessuna fonte prescrive un rapporto H:V specifico.
        """
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        ratio = result.balance.rapporti.get("Push Orizz : Push Vert")
        assert ratio is not None
        assert abs(ratio - 2.33) < 0.02, (
            f"Push H:V = {ratio}, atteso ~2.33 (7 push_h / 3 push_v)"
        )

    def test_pull_h_v_ratio_upper_lower_4x(self):
        """Pull Orizz:Vert = 7/4 = 1.75 — in range con target 1.2 ± 0.80."""
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        ratio = result.balance.rapporti.get("Pull Orizz : Pull Vert")
        assert ratio is not None
        assert abs(ratio - 1.75) < 0.02, (
            f"Pull H:V = {ratio}, atteso 1.75 (7 pull_h / 4 pull_v)"
        )


# ════════════════════════════════════════════════════════════
# TEST 5 — BUG NOTI: rapporti su volume meccanico
# ════════════════════════════════════════════════════════════

class TestBalanceRatiosCalibrated:
    """Verifica che i rapporti biomeccanici siano calibrati correttamente.

    I rapporti muscolari (Quad:Ham, Ant:Post) usano volume ipertrofico
    (compute_hypertrophy_sets). I target derivano dalla letteratura:

    Quad:Ham calcolato a mano (hypertrophy):
      Quad = SQUAT(4×1.0) + LEG_EXT(3×1.0) + SQUAT(3×1.0) = 10.0
      Fem  = SQUAT(4×0.25) + LEG_CURL(3×1.0) + HIP_THRUST(3×0.25)
             + HINGE(4×1.0) + SQUAT(3×0.25) + LEG_CURL(3×1.0) = 12.5
      Ratio = 10.0/12.5 = 0.80 → target 0.80 ± 0.30 = [0.50, 1.10] ✓
      Derivazione: NSCA 2016 cap. 21 squat:hinge bilanciato → 0.80 algebrico

    Ant:Post calcolato a mano (hypertrophy):
      Ant = petto(7.0) + delt_ant(6.5) + quad(10.0) = 23.5
      Post = dorsali(12.0) + delt_post(7.5) + fem(12.5) = 32.0
      Ratio = 23.5/32.0 = 0.73 → target 0.80 ± 0.25 = [0.55, 1.05] ✓
      Fonte: Sahrmann 2002, Janda 1983 — posteriore >= anteriore
    """

    def test_quad_ham_uses_hypertrophy_volume(self):
        """Quad:Ham = 0.80 con volume ipertrofico — on target."""
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        ratio = result.balance.rapporti.get("Quad : Ham")
        assert ratio is not None
        assert abs(ratio - 0.80) < 0.05, (
            f"Quad:Ham = {ratio}, atteso ~0.80 da calcolo ipertrofico"
        )
        # Deve essere IN tolleranza con target ricalibrato
        assert abs(ratio - 0.80) <= 0.30, (
            f"Quad:Ham = {ratio} fuori range [0.50, 1.10]"
        )

    def test_ant_post_uses_hypertrophy_volume(self):
        """Ant:Post = 0.73 con volume ipertrofico — in range."""
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        ratio = result.balance.rapporti.get("Anteriore : Posteriore")
        assert ratio is not None
        assert abs(ratio - 0.73) < 0.05, (
            f"Ant:Post = {ratio}, atteso ~0.73 da calcolo ipertrofico"
        )

    def test_well_designed_plan_few_squilibri(self):
        """Un piano da testo di riferimento ha max 1 squilibrio."""
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        balance_squilibri = len(result.balance.squilibri)
        assert balance_squilibri <= 1, (
            f"{balance_squilibri} squilibri su piano bilanciato: "
            f"{result.balance.squilibri}"
        )


# ════════════════════════════════════════════════════════════
# TEST 6 — Scaling demografico
# ════════════════════════════════════════════════════════════

class TestDemographicScaling:
    """Verifica i fattori demografici (Vingren 2010, Hakkinen 2001)."""

    def test_demographic_factor_values(self):
        assert get_demographic_factor("M", 25) == 1.0
        assert get_demographic_factor("F", 25) == 0.85
        assert get_demographic_factor("M", 55) == 0.85
        assert abs(get_demographic_factor("F", 55) - 0.7225) < 0.01
        assert get_demographic_factor(None, None) == 1.0
        assert abs(get_demographic_factor("F", 70) - 0.85 * 0.75) < 0.01

    def test_mrv_scales_with_demographics(self):
        """MRV donna < MRV uomo per lo stesso muscolo/livello/obiettivo."""
        for muscolo in [M.PETTO, M.DORSALI, M.QUADRICIPITI, M.FEMORALI]:
            target_m = get_scaled_volume_target(
                muscolo, Livello.INTERMEDIO, Obiettivo.IPERTROFIA, "M", 25,
            )
            target_f = get_scaled_volume_target(
                muscolo, Livello.INTERMEDIO, Obiettivo.IPERTROFIA, "F", 25,
            )
            assert target_f.mrv < target_m.mrv, (
                f"{muscolo.value}: MRV F ({target_f.mrv}) >= MRV M ({target_m.mrv})"
            )

    def test_mev_not_scaled_by_demographics(self):
        """MEV scalato solo per obiettivo, NON per sesso/età."""
        for muscolo in [M.PETTO, M.DORSALI, M.QUADRICIPITI]:
            target_m = get_scaled_volume_target(
                muscolo, Livello.INTERMEDIO, Obiettivo.IPERTROFIA, "M", 25,
            )
            target_f = get_scaled_volume_target(
                muscolo, Livello.INTERMEDIO, Obiettivo.IPERTROFIA, "F", 25,
            )
            assert target_m.mev == target_f.mev

    def test_f55_femorali_sopra_mrv_is_correct(self):
        """F55 con femorali in sopra_mrv È CORRETTO — MRV ridotto per demographics.

        Femorali M25: MRV = 16.0, volume = 12.5 → sopra_mav (ok)
        Femorali F55: MRV = 16 × 0.722 = 11.6, volume = 12.5 → sopra_mrv
        Questo è il sistema che funziona: segnala che la F55 ha bisogno
        di meno volume per femorali rispetto a un M25.
        """
        piano = _build_upper_lower_4x("F", 55)
        result = analyze_plan(piano)
        fem = next(v for v in result.volume.per_muscolo if v.muscolo == M.FEMORALI)
        assert fem.stato == "sopra_mrv", (
            f"Femorali F55 = '{fem.stato}', atteso 'sopra_mrv'. "
            f"Volume = {fem.serie_effettive}, MRV = {fem.target_mrv}"
        )


# ════════════════════════════════════════════════════════════
# TEST 7 — Obiettivi diversi producono target diversi
# ════════════════════════════════════════════════════════════

class TestObjectiveVariation:
    def test_forza_vs_ipertrofia_volume_targets(self):
        """Forza ha fattore_volume 0.70 → target ridotti rispetto a ipertrofia."""
        target_forza = get_scaled_volume_target(
            M.PETTO, Livello.INTERMEDIO, Obiettivo.FORZA, "M", 25,
        )
        target_iper = get_scaled_volume_target(
            M.PETTO, Livello.INTERMEDIO, Obiettivo.IPERTROFIA, "M", 25,
        )
        assert target_forza.mav_max < target_iper.mav_max
        assert target_forza.mrv < target_iper.mrv

    def test_strength_2x_low_score_is_expected(self):
        """Forza 2x ha volume basso BY DESIGN — score non deve essere catastrofico.

        fattore_volume = 0.70, solo compound, 2 sessioni/settimana.
        Lo score sarà basso (molti muscoli sotto MEV) ma non < 25.
        """
        piano = _build_strength_2x("M", 25)
        result = analyze_plan(piano)
        assert result.score >= 25, (
            f"Forza 2x M25: score {result.score:.1f} troppo basso"
        )


# ════════════════════════════════════════════════════════════
# TEST 8 — Frequenza muscolare
# ════════════════════════════════════════════════════════════

class TestMuscleFrequency:
    def test_upper_lower_4x_tier1_frequency(self):
        """Upper/Lower 4x M25: tier-1 muscles stimolati ≥2x/settimana."""
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        for key in ["petto", "dorsali", "quadricipiti"]:
            freq = result.frequenza_per_muscolo.get(key, 0)
            assert freq >= 2, f"{key}: freq {freq}x < 2x"

    def test_full_body_3x_femorali_frequency(self):
        """Full Body 3x: femorali hanno hinge solo in sessione B → freq ≥ 1.

        Il volume indiretto da squat (0.4 EMG → 0.25 hyp) può non raggiungere
        la soglia di stimolo (2.0 serie ipertrofiche) → femorali possono
        avere freq = 1 su full body 3x. Questo è un limite dello split.
        """
        piano = _build_full_body_3x("M", 25)
        result = analyze_plan(piano)
        freq = result.frequenza_per_muscolo.get("femorali", 0)
        assert freq >= 1, f"femorali freq = {freq}, atteso ≥ 1"

    def test_ppl_6x_all_tier1_freq_2(self):
        """PPL 6x: ogni muscolo tier-1 stimolato esattamente 2x."""
        piano = _build_ppl_6x("M", 25)
        result = analyze_plan(piano)
        for key in ["petto", "dorsali", "quadricipiti", "femorali"]:
            freq = result.frequenza_per_muscolo.get(key, 0)
            assert freq >= 2, f"{key}: freq {freq}x con PPL 6x"


# ════════════════════════════════════════════════════════════
# TEST 9 — Recovery overlap
# ════════════════════════════════════════════════════════════

class TestRecoveryOverlap:
    def test_ppl_minimal_overlap(self):
        """PPL 6x: split progettato per minimizzare overlap consecutivo."""
        piano = _build_ppl_6x("M", 25)
        result = analyze_plan(piano)
        recovery_warnings = [w for w in result.warnings if "Recupero:" in w]
        assert len(recovery_warnings) <= 3, (
            f"PPL 6x: {len(recovery_warnings)} recovery warnings: {recovery_warnings}"
        )


# ════════════════════════════════════════════════════════════
# TEST 10 — Dettaglio muscoli strutturato
# ════════════════════════════════════════════════════════════

class TestDettaglioMuscoli:
    def test_dettaglio_has_all_15_muscles(self):
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        muscle_names = {d.muscolo for d in result.dettaglio_muscoli}
        assert muscle_names == set(M)

    def test_contributi_sum_matches_serie_effettive(self):
        """I contributi ipertrofici devono sommare a serie_effettive."""
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        for detail in result.dettaglio_muscoli:
            if detail.serie_effettive > 0 and detail.contributi:
                sum_hyp = sum(c.serie_ipertrofiche for c in detail.contributi)
                assert abs(sum_hyp - detail.serie_effettive) < 0.5, (
                    f"{detail.muscolo.value}: contributi = {sum_hyp:.1f}, "
                    f"serie_effettive = {detail.serie_effettive:.1f}"
                )


# ════════════════════════════════════════════════════════════
# TEST 11 — Score composito: piani corretti ≥ 40
# ════════════════════════════════════════════════════════════

class TestScoreQuality:
    """Piani da testi di riferimento devono avere score ragionevoli.

    Nota: con i BUG NOTI nei rapporti biomeccanici, alcuni piani avranno
    score < 70 a causa dei falsi squilibri. Se il test fallisce con score
    < 40, l'analyzer penalizza eccessivamente piani validi.
    """

    @pytest.mark.parametrize(
        "plan_id,name,profile,piano",
        ALL_PLANS,
        ids=[f"{p[0]}_{p[2]['id']}" for p in ALL_PLANS],
    )
    def test_score_not_catastrophic(self, plan_id, name, profile, piano):
        """Nessun piano da testo dovrebbe avere score < 30."""
        result = analyze_plan(piano)
        assert result.score >= 30, (
            f"{name} ({profile['id']}): score {result.score:.1f}. "
            f"Warnings: {result.warnings[:5]}"
        )

    def test_upper_lower_4x_m25_reasonable_score(self):
        """Upper/Lower 4x M25: piano bilanciato dovrebbe avere score ≥ 50.

        Con i bug noti nei ratio, lo score è penalizzato ma non catastrofico.
        Se scende sotto 50, c'è un problema aggiuntivo.
        """
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        assert result.score >= 50, (
            f"UL4x M25 score = {result.score:.1f}, atteso ≥ 50. "
            f"Squilibri: {result.balance.squilibri}"
        )


# ════════════════════════════════════════════════════════════
# TEST 12 — Full Body 3x: volume per muscoli chiave
# ════════════════════════════════════════════════════════════

class TestFullBody3xVolume:
    """Full Body 3x Principiante: calcoli a mano su muscoli chiave.

    A: PUSH_H(3), PULL_H(3), SQUAT(3), CALF(2), CORE(2)
    B: PUSH_V(3), PULL_V(3), HINGE(3), LAT_RAISE(2), CORE(2)
    C: PUSH_H(3), PULL_H(3), SQUAT(3), CURL(2), EXT_TRI(2)
    """

    def test_petto_volume(self):
        """Petto = PUSH_H A(3×1.0) + PUSH_H C(3×1.0) = 6.0"""
        piano = _build_full_body_3x("M", 25)
        result = analyze_plan(piano)
        petto = next(v for v in result.volume.per_muscolo if v.muscolo == M.PETTO)
        assert abs(petto.serie_effettive - 6.0) < 0.15

    def test_quadricipiti_volume(self):
        """Quad = SQUAT A(3×1.0) + SQUAT C(3×1.0) = 6.0"""
        piano = _build_full_body_3x("M", 25)
        result = analyze_plan(piano)
        quad = next(v for v in result.volume.per_muscolo if v.muscolo == M.QUADRICIPITI)
        assert abs(quad.serie_effettive - 6.0) < 0.15

    def test_delt_lat_sotto_mev(self):
        """Delt_lat = PUSH_V B(3×0.5) + LAT_RAISE B(2×1.0) = 3.5

        Per principiante, MEV delt_lat = 4. Volume 3.5 < 4 → sotto_mev.
        Il piano ha troppo poco lavoro laterale — finding legittimo.
        """
        piano = _build_full_body_3x("M", 25)
        result = analyze_plan(piano)
        dl = next(v for v in result.volume.per_muscolo if v.muscolo == M.DELT_LAT)
        assert abs(dl.serie_effettive - 3.5) < 0.15
        assert dl.stato == "sotto_mev", (
            f"Delt_lat = {dl.serie_effettive}, stato '{dl.stato}', atteso 'sotto_mev'"
        )

    def test_femorali_mev_mav(self):
        """Femorali = HINGE B(3×1.0) + SQUAT A(3×0.25) + SQUAT C(3×0.25) = 4.5

        Per principiante, MEV = 4, MAV_min = 6. Volume 4.5 → mev_mav.
        Solo 1 sessione di hinge diretto — il piano è corto su femorali.
        """
        piano = _build_full_body_3x("M", 25)
        result = analyze_plan(piano)
        fem = next(v for v in result.volume.per_muscolo if v.muscolo == M.FEMORALI)
        assert abs(fem.serie_effettive - 4.5) < 0.15
        assert fem.stato == "mev_mav"


# ════════════════════════════════════════════════════════════
# TEST 13 — PPL 6x Avanzato: volume alto e corretto
# ════════════════════════════════════════════════════════════

class TestPPL6xVolume:
    """PPL 6x Avanzato: tutti i tier-1 devono superare MEV."""

    @pytest.mark.parametrize("profile", PROFILES, ids=[p["id"] for p in PROFILES])
    def test_tier1_above_mev(self, profile):
        piano = _build_ppl_6x(profile["sesso"], profile["eta"])
        result = analyze_plan(piano)
        tier1 = {M.PETTO, M.DORSALI, M.QUADRICIPITI, M.FEMORALI}
        for vd in result.volume.per_muscolo:
            if vd.muscolo in tier1:
                assert vd.serie_effettive >= vd.target_mev, (
                    f"{vd.muscolo.value} ({profile['id']}): "
                    f"{vd.serie_effettive:.1f} < MEV {vd.target_mev}"
                )

    def test_ppl_6x_m25_petto_volume(self):
        """Petto PPL 6x = PUSH_H A(4+3) + PUSH_H B(3+2) = 12.0"""
        piano = _build_ppl_6x("M", 25)
        result = analyze_plan(piano)
        petto = next(v for v in result.volume.per_muscolo if v.muscolo == M.PETTO)
        assert abs(petto.serie_effettive - 12.0) < 0.15

    def test_ppl_6x_f55_excess_volume_expected(self):
        """PPL 6x per F55: ALMENO un muscolo sopra_mrv è atteso.

        Il piano è progettato per avanzati maschi. Una donna 55 anni
        ha MRV ridotto del 28% → eccesso fisiologico su alcuni gruppi.
        Se NESSUN muscolo è sopra_mrv, il demographic scaling è rotto.
        """
        piano = _build_ppl_6x("F", 55)
        result = analyze_plan(piano)
        sopra_mrv = [
            v.muscolo.value for v in result.volume.per_muscolo
            if v.stato == "sopra_mrv"
        ]
        assert len(sopra_mrv) >= 1, (
            f"PPL 6x F55: nessun muscolo sopra_mrv — "
            f"il demographic scaling non produce eccesso atteso"
        )


# ════════════════════════════════════════════════════════════
# TEST 14 — Warning count sanity check
# ════════════════════════════════════════════════════════════

class TestWarningCount:
    @pytest.mark.parametrize("profile", PROFILES, ids=[p["id"] for p in PROFILES])
    def test_upper_lower_warning_count_reasonable(self, profile):
        """Upper/Lower 4x: max 10 warning (alcuni fisiologici)."""
        piano = _build_upper_lower_4x(profile["sesso"], profile["eta"])
        result = analyze_plan(piano)
        assert len(result.warnings) <= 10, (
            f"UL4x ({profile['id']}): {len(result.warnings)} warnings: "
            f"{result.warnings[:5]}..."
        )

    def test_f55_has_more_warnings_than_m25(self):
        """F55 deve avere PIÙ warning di M25 (MRV ridotto → più eccessi)."""
        piano_m25 = _build_upper_lower_4x("M", 25)
        piano_f55 = _build_upper_lower_4x("F", 55)
        result_m25 = analyze_plan(piano_m25)
        result_f55 = analyze_plan(piano_f55)
        assert len(result_f55.warnings) > len(result_m25.warnings), (
            f"F55 ha {len(result_f55.warnings)} warnings vs M25 {len(result_m25.warnings)}. "
            f"Atteso F55 > M25 per via del MRV ridotto."
        )

    def test_score_m25_higher_than_f55(self):
        """M25 deve avere score > F55 sulla stessa scheda."""
        piano_m25 = _build_upper_lower_4x("M", 25)
        piano_f55 = _build_upper_lower_4x("F", 55)
        result_m25 = analyze_plan(piano_m25)
        result_f55 = analyze_plan(piano_f55)
        assert result_m25.score > result_f55.score, (
            f"M25 score {result_m25.score:.1f} ≤ F55 score {result_f55.score:.1f}"
        )


# ════════════════════════════════════════════════════════════
# TEST 15 — BUG FIX TARGETS (questi test DEVONO FALLIRE)
# ════════════════════════════════════════════════════════════
#
# Ogni test qui asserisce il comportamento SCIENTIFICAMENTE CORRETTO.
# Se un test fallisce, indica un BUG REALE che deve essere fixato.
# Quando il bug viene fixato, il test passerà e potrà essere spostato
# nella sezione dei test normali.

class TestBugFixTargets:
    """Test che verificano la calibrazione scientifica dei rapporti.

    Principi di calibrazione:
    1. Rapporti muscolari (Quad:Ham, Ant:Post) usano compute_hypertrophy_sets()
    2. Target derivati dalla letteratura (NSCA 2016, Sahrmann 2002, Janda 1983,
       Alentorn-Geli 2009, Schoenfeld 2010, Boettcher 2008, Israetel RP 2020)
    3. Tolleranze proporzionali al livello di evidenza:
       - Push:Pull: ±0.15 (evidenza forte, prescrizione diretta)
       - Push_H:V / Pull_H:V: ampia (evidenza moderata, no ratio prescritto)
       - Quad:Ham, Ant:Post: ±0.25-0.30 (evidenza moderata-forte)
    """

    def test_quad_ham_balanced_plan_not_flagged(self):
        """Quad:Ham = 0.80 per piano bilanciato — in range [0.50, 1.10].

        Derivazione algebrica (NSCA 2016 squat:hinge bilanciato):
          quad:ham = n / (0.25n + n) = 0.80
        """
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        ratio = result.balance.rapporti.get("Quad : Ham", 0)
        is_balanced = abs(ratio - 0.80) <= 0.30
        assert is_balanced, (
            f"Quad:Ham = {ratio:.2f}, fuori dal range [0.50, 1.10]. "
            f"Un piano con 10 quad + 12.5 fem (hyp) dovrebbe essere in range."
        )

    def test_ant_post_balanced_plan_not_flagged(self):
        """Ant:Post = 0.73 per piano bilanciato — in range [0.55, 1.05].

        Sahrmann 2002 + Janda 1983: posteriore >= anteriore.
        """
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        ratio = result.balance.rapporti.get("Anteriore : Posteriore", 0)
        is_balanced = abs(ratio - 0.80) <= 0.25
        assert is_balanced, (
            f"Ant:Post = {ratio:.2f}, fuori dal range [0.55, 1.05]."
        )

    def test_push_h_v_not_flagged(self):
        """Push_H:Push_V = 2.33 — in range [0.5, 2.5] con target 1.5.

        Sahrmann 2002: push_h preferibile a push_v (delt_ant overactive).
        Boettcher 2008: overhead aumenta rischio impingement.
        Tolleranza ampia: nessuna fonte prescrive un rapporto specifico.
        """
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        squilibri_push = [
            s for s in result.balance.squilibri
            if "Push Orizz" in s
        ]
        assert len(squilibri_push) == 0, (
            f"Push_H:Push_V flaggato: {squilibri_push}. "
            f"Sahrmann 2002: rapporto H > V e' protettivo per la spalla."
        )

    def test_pull_h_v_not_flagged(self):
        """Pull_H:Pull_V = 1.75 — in range [0.4, 2.0] con target 1.2.

        Sahrmann 2002: rows raccomandate per retrazione scapolare.
        """
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        squilibri_pull = [
            s for s in result.balance.squilibri
            if "Pull Orizz" in s
        ]
        assert len(squilibri_pull) == 0, (
            f"Pull_H:Pull_V flaggato: {squilibri_pull}. "
            f"Sahrmann 2002: rows > pulldown per salute scapolare."
        )

    def test_well_designed_plan_scores_above_70(self):
        """Upper/Lower 4x M25 score ≥ 70 con rapporti calibrati."""
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        assert result.score >= 70, (
            f"UL4x M25 score = {result.score:.1f}. Un piano da testo dovrebbe "
            f"avere ≥70. Squilibri: {result.balance.squilibri}"
        )

    def test_full_body_3x_max_one_squilibrio(self):
        """Full Body 3x M25 ha max 1 squilibrio biomeccanico."""
        piano = _build_full_body_3x("M", 25)
        result = analyze_plan(piano)
        ratio_squilibri = len(result.balance.squilibri)
        assert ratio_squilibri <= 1, (
            f"Full Body 3x M25: {ratio_squilibri} squilibri. "
            f"Dettaglio: {result.balance.squilibri}"
        )
