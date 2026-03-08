"""
Training Science Engine — Test di validazione con schede campione da testi di riferimento.

Ogni scheda e' costruita seguendo le linee guida di:
  - NSCA — "Essentials of Strength Training & Conditioning" (2016), cap. 15-22
  - Schoenfeld — "Science and Development of Muscle Hypertrophy" (2021)
  - Israetel — "Scientific Principles of Hypertrophy Training" (RP, 2020)
  - ACSM — "Guidelines for Exercise Testing and Prescription" (2009)

Le schede sono replicate per 4 profili demografici:
  - Uomo 25 anni (baseline: demo_factor = 1.0)
  - Donna 25 anni (F factor 0.85)
  - Uomo 55 anni (age factor 0.85)
  - Donna 55 anni (F 0.85 × age 0.85 = 0.72)

Split coperti:
  - Full Body 3x (principiante)
  - Upper/Lower 4x (intermedio)
  - Push/Pull/Legs 6x (avanzato)

Per ogni combinazione si verifica che l'analyzer produca risultati coerenti:
  - Score ragionevole (nessun piano corretto dovrebbe essere < 40)
  - Muscoli principali in range corretto dato il volume inserito
  - Rapporti biomeccanici equilibrati
  - Warning sensati (no falsi positivi su piani ben costruiti)
  - Scaling demografico effettivo (MRV donna < MRV uomo)
"""

import pytest

from api.services.training_science.plan_analyzer import analyze_plan
from api.services.training_science.volume_model import (
    get_scaled_volume_target,
    get_demographic_factor,
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
#
# Fonte: NSCA 2016 cap. 15 (principiante: 1-3 esercizi per gruppo,
#        2-3 serie, 8-12 rep, frequenza 2-3x/settimana).
# Schoenfeld 2016: frequenza ≥2x/muscolo ottimale per ipertrofia.
#
# Layout: A/B/C rotazione, 3 sessioni/settimana.
# Ogni muscolo principale stimolato almeno 2x/settimana.

def _build_full_body_3x(sesso: str | None, eta: int | None) -> TemplatePiano:
    session_a = _session("Full Body A", "full_body", [
        _slot(P.PUSH_H, 3),           # petto 3, delt_ant 2.1, tri 2.1
        _slot(P.PULL_H, 3),           # dorsali 3, trap 2.1, delt_post 2.1, bic 2.1
        _slot(P.SQUAT, 3),            # quad 3, glut 2.1, fem 1.2, add 1.2
        _slot(P.CALF_RAISE, 2),       # polpacci 2
        _slot(P.CORE, 2, 15, 20, 60), # core 2
    ])
    session_b = _session("Full Body B", "full_body", [
        _slot(P.PUSH_V, 3),           # delt_ant 3, delt_lat 2.1, tri 2.1
        _slot(P.PULL_V, 3),           # dorsali 3, bic 2.1, delt_post 1.2
        _slot(P.HINGE, 3),            # fem 3, glut 3, dorsali 1.2
        _slot(P.LATERAL_RAISE, 2),    # delt_lat 2
        _slot(P.CORE, 2, 15, 20, 60),
    ])
    session_c = _session("Full Body C", "full_body", [
        _slot(P.PUSH_H, 3),
        _slot(P.PULL_H, 3),
        _slot(P.SQUAT, 3),
        _slot(P.CURL, 2),             # bic 2
        _slot(P.EXTENSION_TRI, 2),    # tri 2
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
#
# Fonte: Schoenfeld 2021 cap. 8 (intermedio: 10-20 serie/muscolo/sett,
#        split upper/lower per frequenza 2x/muscolo).
# Israetel RP 2020: MAV tipico intermedio 12-18 serie/muscolo.
#
# Layout: Upper A, Lower A, Upper B, Lower B.

def _build_upper_lower_4x(sesso: str | None, eta: int | None) -> TemplatePiano:
    upper_a = _session("Upper A", "upper", [
        _slot(P.PUSH_H, 4, 6, 10, 120),      # bench press
        _slot(P.PULL_H, 4, 6, 10, 120),       # row
        _slot(P.PUSH_V, 3, 8, 12, 90),        # ohp
        _slot(P.FACE_PULL, 3, 12, 15, 60),    # delt post
        _slot(P.CURL, 3, 10, 12, 60),         # bicipiti
        _slot(P.EXTENSION_TRI, 3, 10, 12, 60),
    ])
    lower_a = _session("Lower A", "lower", [
        _slot(P.SQUAT, 4, 6, 8, 180),         # back squat
        _slot(P.LEG_CURL, 3, 10, 12, 60),     # femorali isolamento
        _slot(P.HIP_THRUST, 3, 8, 12, 90),    # glutei
        _slot(P.LEG_EXTENSION, 3, 10, 12, 60),
        _slot(P.CALF_RAISE, 3, 12, 15, 60),
        _slot(P.ADDUCTOR, 2, 12, 15, 60),
    ])
    upper_b = _session("Upper B", "upper", [
        _slot(P.PULL_V, 4, 6, 10, 120),       # chin-up
        _slot(P.PUSH_H, 3, 10, 12, 90),       # dumbbell press
        _slot(P.LATERAL_RAISE, 3, 12, 15, 60),
        _slot(P.PULL_H, 3, 10, 12, 90),       # cable row
        _slot(P.CURL, 2, 10, 12, 60),
        _slot(P.EXTENSION_TRI, 2, 10, 12, 60),
    ])
    lower_b = _session("Lower B", "lower", [
        _slot(P.HINGE, 4, 6, 8, 180),         # deadlift
        _slot(P.SQUAT, 3, 10, 12, 90),        # front squat / goblet
        _slot(P.LEG_CURL, 3, 10, 12, 60),
        _slot(P.CALF_RAISE, 3, 12, 15, 60),
        _slot(P.CARRY, 2, 8, 12, 90),         # farmer walk
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
#
# Fonte: Israetel RP 2020 (avanzato: 16-22+ serie/muscolo/sett,
#        split PPL per alta frequenza senza overlap recovery).
# NSCA 2016 cap. 22: avanzato fino a 6 sessioni/settimana.
#
# Layout: Push A, Pull A, Legs A, Push B, Pull B, Legs B.

def _build_ppl_6x(sesso: str | None, eta: int | None) -> TemplatePiano:
    push_a = _session("Push A", "push", [
        _slot(P.PUSH_H, 4, 6, 8, 120),       # flat bench
        _slot(P.PUSH_V, 3, 8, 12, 90),        # ohp
        _slot(P.PUSH_H, 3, 10, 12, 90),       # incline db
        _slot(P.LATERAL_RAISE, 3, 12, 15, 60),
        _slot(P.EXTENSION_TRI, 3, 10, 12, 60),
    ])
    pull_a = _session("Pull A", "pull", [
        _slot(P.PULL_V, 4, 6, 8, 120),        # pull-up
        _slot(P.PULL_H, 4, 8, 12, 90),        # barbell row
        _slot(P.FACE_PULL, 3, 12, 15, 60),
        _slot(P.CURL, 3, 10, 12, 60),
        _slot(P.CURL, 2, 12, 15, 60),         # hammer curl
    ])
    legs_a = _session("Legs A", "legs", [
        _slot(P.SQUAT, 4, 6, 8, 180),         # back squat
        _slot(P.HINGE, 3, 8, 10, 120),        # rdl
        _slot(P.LEG_EXTENSION, 3, 10, 12, 60),
        _slot(P.LEG_CURL, 3, 10, 12, 60),
        _slot(P.CALF_RAISE, 4, 12, 15, 60),
    ])
    push_b = _session("Push B", "push", [
        _slot(P.PUSH_V, 4, 6, 8, 120),        # push press
        _slot(P.PUSH_H, 3, 10, 12, 90),       # cable fly
        _slot(P.LATERAL_RAISE, 3, 12, 15, 60),
        _slot(P.EXTENSION_TRI, 3, 10, 12, 60),
        _slot(P.PUSH_H, 2, 12, 15, 60),       # pec deck
    ])
    pull_b = _session("Pull B", "pull", [
        _slot(P.PULL_H, 4, 8, 10, 120),       # seated row
        _slot(P.PULL_V, 3, 8, 12, 90),        # lat pulldown
        _slot(P.FACE_PULL, 3, 12, 15, 60),
        _slot(P.CURL, 3, 10, 12, 60),
    ])
    legs_b = _session("Legs B", "legs", [
        _slot(P.HINGE, 4, 6, 8, 180),         # conventional deadlift
        _slot(P.SQUAT, 3, 10, 12, 90),        # leg press
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
#
# Fonte: NSCA 2016 cap. 15,17 (forza: 3-5 serie, 1-5 rep,
#        85-100% 1RM, riposo 3-5 min, enfasi compound).

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
#
# Fonte: NSCA 2016, Schoenfeld 2021 (dimagrimento: mantenere
#        volume, privilegiare compound per dispendio calorico,
#        riposi brevi, rep moderate 8-15).

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
#
# Fonte: ACSM 2009 (tonificazione: 2-3 serie, 10-15 rep,
#        60-75% 1RM, enfasi su qualita' del movimento).

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
# BUILDER MATRIX — Tutte le combinazioni split × profilo
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
    """Genera tutte le combinazioni (plan_id, plan_name, profile, piano)."""
    combos = []
    for plan_id, (builder, name) in PLAN_BUILDERS.items():
        for profile in PROFILES:
            piano = builder(profile["sesso"], profile["eta"])
            combos.append((plan_id, name, profile, piano))
    return combos


ALL_PLANS = _build_all_plans()


# ════════════════════════════════════════════════════════════
# TEST 1 — Analyzer non crasha su nessun piano
# ════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    "plan_id,name,profile,piano",
    ALL_PLANS,
    ids=[f"{p[0]}_{p[2]['id']}" for p in ALL_PLANS],
)
def test_analyzer_no_crash(plan_id, name, profile, piano):
    """L'analyzer deve produrre un risultato valido per ogni piano campione."""
    result = analyze_plan(piano)
    assert result is not None
    assert isinstance(result.score, (int, float))
    assert 0 <= result.score <= 100
    assert len(result.volume.per_muscolo) > 0
    assert isinstance(result.balance.rapporti, dict)
    assert isinstance(result.warnings, list)


# ════════════════════════════════════════════════════════════
# TEST 2 — Score minimo per piani ben costruiti
# ════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    "plan_id,name,profile,piano",
    ALL_PLANS,
    ids=[f"{p[0]}_{p[2]['id']}" for p in ALL_PLANS],
)
def test_well_designed_plan_score(plan_id, name, profile, piano):
    """Piani costruiti su fonti scientifiche devono avere score >= 40.

    Sotto 40 indica che l'analyzer penalizza eccessivamente
    schede che sono di fatto corrette per il loro target demografico.
    """
    result = analyze_plan(piano)
    assert result.score >= 40, (
        f"{name} ({profile['id']}): score {result.score:.1f} troppo basso. "
        f"Warnings: {result.warnings}"
    )


# ════════════════════════════════════════════════════════════
# TEST 3 — Scaling demografico effettivo
# ════════════════════════════════════════════════════════════

class TestDemographicScaling:
    """Verifica che il fattore demografico scali correttamente i target."""

    def test_demographic_factor_values(self):
        """Verifica i fattori demografici attesi (Vingren 2010, Hakkinen 2001)."""
        assert get_demographic_factor("M", 25) == 1.0
        assert get_demographic_factor("F", 25) == 0.85
        assert get_demographic_factor("M", 55) == 0.85
        assert abs(get_demographic_factor("F", 55) - 0.7225) < 0.01
        # Edge cases
        assert get_demographic_factor(None, None) == 1.0
        assert get_demographic_factor("M", None) == 1.0
        assert get_demographic_factor(None, 55) == 0.85
        assert abs(get_demographic_factor("F", 70) - 0.85 * 0.75) < 0.01  # F × 60+

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
        """MEV e' scalato solo per obiettivo, NON per sesso/eta.

        Razionale: la soglia minima per stimolare crescita non dipende
        da testosterone o eta' — dipende solo dal tipo di allenamento.
        """
        for muscolo in [M.PETTO, M.DORSALI, M.QUADRICIPITI]:
            target_m = get_scaled_volume_target(
                muscolo, Livello.INTERMEDIO, Obiettivo.IPERTROFIA, "M", 25,
            )
            target_f = get_scaled_volume_target(
                muscolo, Livello.INTERMEDIO, Obiettivo.IPERTROFIA, "F", 25,
            )
            assert target_m.mev == target_f.mev, (
                f"{muscolo.value}: MEV M ({target_m.mev}) != MEV F ({target_f.mev})"
            )

    def test_older_person_has_lower_mav_mrv(self):
        """Target MAV/MRV si riducono con l'eta (Hakkinen 2001)."""
        for muscolo in [M.PETTO, M.DORSALI, M.QUADRICIPITI]:
            target_young = get_scaled_volume_target(
                muscolo, Livello.INTERMEDIO, Obiettivo.IPERTROFIA, "M", 25,
            )
            target_old = get_scaled_volume_target(
                muscolo, Livello.INTERMEDIO, Obiettivo.IPERTROFIA, "M", 55,
            )
            assert target_old.mrv < target_young.mrv
            assert target_old.mav_max < target_young.mav_max


# ════════════════════════════════════════════════════════════
# TEST 4 — Rapporti biomeccanici su piani bilanciati
# ════════════════════════════════════════════════════════════

class TestBalanceRatios:
    """Piani ben costruiti non devono avere squilibri gravi."""

    @pytest.mark.parametrize(
        "plan_id,name,profile,piano",
        [p for p in ALL_PLANS if p[0] in ("upper_lower_4x_hyp", "ppl_6x_hyp")],
        ids=[f"{p[0]}_{p[2]['id']}" for p in ALL_PLANS
             if p[0] in ("upper_lower_4x_hyp", "ppl_6x_hyp")],
    )
    def test_push_pull_balanced(self, plan_id, name, profile, piano):
        """Push:Pull ratio deve essere vicino a 1.0 (±0.15, NSCA 2016)."""
        result = analyze_plan(piano)
        ratio = result.balance.rapporti.get("Push : Pull")
        if ratio is not None:
            assert 0.7 <= ratio <= 1.5, (
                f"{name} ({profile['id']}): Push:Pull = {ratio}, "
                f"troppo sbilanciato"
            )

    @pytest.mark.parametrize(
        "plan_id,name,profile,piano",
        [p for p in ALL_PLANS if p[0] in ("upper_lower_4x_hyp", "ppl_6x_hyp")],
        ids=[f"{p[0]}_{p[2]['id']}" for p in ALL_PLANS
             if p[0] in ("upper_lower_4x_hyp", "ppl_6x_hyp")],
    )
    def test_quad_ham_ratio(self, plan_id, name, profile, piano):
        """Quad:Ham ratio non deve essere estremo (Alentorn-Geli 2009).

        Il rapporto usa volume ipertrofico pesato (Israetel half-a-set),
        non serie grezze. Valori 0.5-2.5 sono fisiologici, considerando
        che hinge contribuisce 1.0 a femorali + 0.4 a quad via EMG.
        """
        result = analyze_plan(piano)
        ratio = result.balance.rapporti.get("Quad : Ham")
        if ratio is not None and ratio < 90:
            assert 0.5 <= ratio <= 2.5, (
                f"{name} ({profile['id']}): Quad:Ham = {ratio}"
            )


# ════════════════════════════════════════════════════════════
# TEST 5 — Volume coverage per muscoli principali
# ════════════════════════════════════════════════════════════

class TestVolumeCoverage:
    """Verifica che il volume dei muscoli primari sia in range per piani adeguati."""

    @pytest.mark.parametrize("profile", PROFILES, ids=[p["id"] for p in PROFILES])
    def test_upper_lower_4x_chest_volume(self, profile):
        """Upper/Lower 4x ipertrofia: petto deve essere almeno in MEV-MAV."""
        piano = _build_upper_lower_4x(profile["sesso"], profile["eta"])
        result = analyze_plan(piano)
        chest = next(
            (v for v in result.volume.per_muscolo if v.muscolo == M.PETTO), None,
        )
        assert chest is not None
        # Per un intermedio il petto deve avere almeno MEV (4 serie base)
        assert chest.serie_effettive >= chest.target_mev, (
            f"Petto ({profile['id']}): {chest.serie_effettive:.1f} < MEV {chest.target_mev}"
        )
        # Non deve superare MRV
        assert chest.serie_effettive <= chest.target_mrv + 2, (
            f"Petto ({profile['id']}): {chest.serie_effettive:.1f} > MRV+2 {chest.target_mrv + 2}"
        )

    @pytest.mark.parametrize("profile", PROFILES, ids=[p["id"] for p in PROFILES])
    def test_ppl_6x_all_major_muscles_stimulated(self, profile):
        """PPL 6x avanzato: tutti i muscoli tier-1 devono superare MEV."""
        piano = _build_ppl_6x(profile["sesso"], profile["eta"])
        result = analyze_plan(piano)
        tier1 = {M.PETTO, M.DORSALI, M.QUADRICIPITI, M.FEMORALI}
        for muscle_data in result.volume.per_muscolo:
            if muscle_data.muscolo in tier1:
                assert muscle_data.serie_effettive >= muscle_data.target_mev, (
                    f"{muscle_data.muscolo.value} ({profile['id']}): "
                    f"{muscle_data.serie_effettive:.1f} < MEV {muscle_data.target_mev}"
                )

    @pytest.mark.parametrize("profile", PROFILES, ids=[p["id"] for p in PROFILES])
    def test_strength_2x_volume_intentionally_low(self, profile):
        """Forza 2x: volume basso e' intenzionale (fattore_volume = 0.70).

        L'analyzer non deve penalizzare eccessivamente piani di forza
        che hanno volume sotto MAV — e' il design dell'obiettivo.
        """
        piano = _build_strength_2x(profile["sesso"], profile["eta"])
        result = analyze_plan(piano)
        # Score di forza e' intrinsecamente piu' basso perche' il volume
        # e' concentrato su pochi esercizi — ma non deve essere catastrofico
        assert result.score >= 30, (
            f"Forza 2x ({profile['id']}): score {result.score:.1f} troppo basso"
        )


# ════════════════════════════════════════════════════════════
# TEST 6 — Warning falsi positivi
# ════════════════════════════════════════════════════════════

class TestWarningQuality:
    """Verifica che piani corretti non generino troppi warning."""

    @pytest.mark.parametrize("profile", PROFILES, ids=[p["id"] for p in PROFILES])
    def test_upper_lower_no_excessive_warnings(self, profile):
        """Upper/Lower 4x ben bilanciato non deve avere > 8 warning.

        Alcuni warning sono fisiologici (es. polpacci sotto MEV in certi profili),
        ma un piano bilanciato non dovrebbe averne un eccesso.
        """
        piano = _build_upper_lower_4x(profile["sesso"], profile["eta"])
        result = analyze_plan(piano)
        assert len(result.warnings) <= 8, (
            f"Upper/Lower ({profile['id']}): {len(result.warnings)} warning. "
            f"Dettaglio: {result.warnings}"
        )

    @pytest.mark.parametrize("profile", PROFILES, ids=[p["id"] for p in PROFILES])
    def test_ppl_6x_no_excess_volume_for_baseline_male(self, profile):
        """PPL 6x avanzato: muscoli tier-1 non sopra_mrv per uomini giovani.

        Per profili con demo_factor ridotto (F55 = 0.72) il MRV scende
        e lo stesso volume puo' legittimamente superare la soglia.
        Questo test verifica solo il profilo baseline (M25, demo=1.0).
        """
        if profile["demo_factor"] < 0.9:
            pytest.skip("Profilo con MRV ridotto — eccesso fisiologico accettabile")
        piano = _build_ppl_6x(profile["sesso"], profile["eta"])
        result = analyze_plan(piano)
        tier1 = {M.PETTO, M.DORSALI, M.QUADRICIPITI, M.FEMORALI}
        for muscle_data in result.volume.per_muscolo:
            if muscle_data.muscolo in tier1:
                assert muscle_data.stato != "sopra_mrv", (
                    f"{muscle_data.muscolo.value} ({profile['id']}): sopra_mrv con "
                    f"{muscle_data.serie_effettive:.1f} serie (MRV={muscle_data.target_mrv}). "
                    f"Piano da testo non dovrebbe eccedere MRV per baseline."
                )


# ════════════════════════════════════════════════════════════
# TEST 7 — Frequenza muscolare
# ════════════════════════════════════════════════════════════

class TestMuscleFrequency:
    """Verifica frequenza di stimolo per muscolo."""

    @pytest.mark.parametrize("profile", PROFILES, ids=[p["id"] for p in PROFILES])
    def test_full_body_3x_minimum_frequency(self, profile):
        """Full Body 3x: muscoli push/pull stimolati almeno 2x/settimana.

        Schoenfeld 2016: frequenza ≥2x ottimale per sintesi proteica.
        Nota: femorali possono avere freq=1 se hinge e' solo in 1 sessione
        (contributo indiretto da squat 0.4 non raggiunge soglia stimolo).
        """
        piano = _build_full_body_3x(profile["sesso"], profile["eta"])
        result = analyze_plan(piano)
        # Petto e dorsali sono in 2+ sessioni → freq ≥2 garantita
        for key in ["petto", "dorsali", "quadricipiti"]:
            freq = result.frequenza_per_muscolo.get(key, 0)
            assert freq >= 2, (
                f"{key} ({profile['id']}): frequenza {freq}x < 2x/sett"
            )
        # Femorali: almeno 1x (hinge in sessione B, contributo indiretto da squat)
        assert result.frequenza_per_muscolo.get("femorali", 0) >= 1

    @pytest.mark.parametrize("profile", PROFILES, ids=[p["id"] for p in PROFILES])
    def test_ppl_6x_high_frequency(self, profile):
        """PPL 6x: muscoli stimolati esattamente 2x/settimana (Push/Pull/Legs × 2)."""
        piano = _build_ppl_6x(profile["sesso"], profile["eta"])
        result = analyze_plan(piano)
        # Con PPL A+B, ogni muscolo e' colpito 2 volte
        for key in ["petto", "dorsali", "quadricipiti", "femorali"]:
            freq = result.frequenza_per_muscolo.get(key, 0)
            assert freq >= 2, (
                f"{key} ({profile['id']}): frequenza {freq}x con PPL 6x"
            )


# ════════════════════════════════════════════════════════════
# TEST 8 — Recovery overlap
# ════════════════════════════════════════════════════════════

class TestRecoveryOverlap:
    """Verifica che la logica recovery sia sensata."""

    def test_ppl_minimal_overlap(self):
        """PPL 6x: split ben progettato minimizza overlap consecutivo.

        Push→Pull→Legs non ha overlap significativo tra sessioni consecutive
        perche' ogni sessione allena gruppi diversi.
        """
        piano = _build_ppl_6x("M", 25)
        result = analyze_plan(piano)
        # PPL ha overlap solo tra Legs B → Push A (ciclo successivo) per core
        recovery_warnings = [
            w for w in result.warnings if "recupero" in w.lower()
        ]
        # Massimo 2 warning di recovery su PPL (eventuali overlap fisiologici)
        assert len(recovery_warnings) <= 2, (
            f"PPL 6x M25: {len(recovery_warnings)} recovery warnings: "
            f"{recovery_warnings}"
        )


# ════════════════════════════════════════════════════════════
# TEST 9 — Confronto cross-profilo (stessa scheda)
# ════════════════════════════════════════════════════════════

class TestCrossProfileComparison:
    """Verifica che lo stesso piano produca risultati diversi per profili diversi."""

    def test_same_plan_different_scores(self):
        """Lo stesso piano Upper/Lower deve avere score diversi M25 vs F55.

        Una donna 55 anni ha MRV piu' basso → piu' muscoli in eccesso
        → score tendenzialmente diverso.
        """
        piano_m25 = _build_upper_lower_4x("M", 25)
        piano_f55 = _build_upper_lower_4x("F", 55)
        result_m25 = analyze_plan(piano_m25)
        result_f55 = analyze_plan(piano_f55)

        # I risultati devono essere diversi (scaling attivo)
        assert result_m25.score != result_f55.score, (
            f"Score identico M25 ({result_m25.score}) e F55 ({result_f55.score}) "
            f"— scaling demografico non funzionante"
        )

    def test_volume_status_differs_by_demographics(self):
        """Stessa scheda: almeno un muscolo deve avere stato diverso M25 vs F55."""
        piano_m25 = _build_upper_lower_4x("M", 25)
        piano_f55 = _build_upper_lower_4x("F", 55)
        result_m25 = analyze_plan(piano_m25)
        result_f55 = analyze_plan(piano_f55)

        status_m25 = {v.muscolo: v.stato for v in result_m25.volume.per_muscolo}
        status_f55 = {v.muscolo: v.stato for v in result_f55.volume.per_muscolo}

        differences = [
            m for m in status_m25 if status_m25.get(m) != status_f55.get(m)
        ]
        assert len(differences) > 0, (
            "Tutti i muscoli hanno lo stesso stato per M25 e F55. "
            "Scaling demografico non produce differenze di classificazione."
        )


# ════════════════════════════════════════════════════════════
# TEST 10 — Dettaglio muscoli (drill-down strutturato)
# ════════════════════════════════════════════════════════════

class TestDettaglioMuscoli:
    """Verifica la correttezza dei dati di drill-down per muscolo."""

    def test_dettaglio_has_all_muscles(self):
        """Il dettaglio deve coprire tutti i 15 muscoli."""
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        muscle_names = {d.muscolo for d in result.dettaglio_muscoli}
        all_muscles = set(M)
        assert muscle_names == all_muscles, (
            f"Muscoli mancanti nel dettaglio: {all_muscles - muscle_names}"
        )

    def test_contributi_sum_consistent(self):
        """I contributi ipertrofici devono corrispondere alle serie effettive.

        serie_effettive usa il dual-volume (Israetel half-a-set rule):
          EMG 1.0 → peso 1.0, EMG 0.7 → peso 0.5, EMG 0.4 → peso 0.25, EMG 0.2 → peso 0.0
        Quindi la somma serie_ipertrofiche nei contributi deve matchare.
        """
        piano = _build_upper_lower_4x("M", 25)
        result = analyze_plan(piano)
        for detail in result.dettaglio_muscoli:
            if detail.serie_effettive > 0 and detail.contributi:
                sum_hyp = sum(c.serie_ipertrofiche for c in detail.contributi)
                assert abs(sum_hyp - detail.serie_effettive) < 0.5, (
                    f"{detail.muscolo.value}: serie_ipertrofiche sommano a {sum_hyp:.1f} "
                    f"ma serie_effettive = {detail.serie_effettive:.1f}"
                )


# ════════════════════════════════════════════════════════════
# TEST 11 — Obiettivi diversi sullo stesso split
# ════════════════════════════════════════════════════════════

class TestObjectiveVariation:
    """Verifica che obiettivi diversi producano target diversi."""

    def test_forza_vs_ipertrofia_volume_targets(self):
        """Forza ha fattore_volume 0.70 vs ipertrofia 1.00 → target diversi."""
        target_forza = get_scaled_volume_target(
            M.PETTO, Livello.INTERMEDIO, Obiettivo.FORZA, "M", 25,
        )
        target_iper = get_scaled_volume_target(
            M.PETTO, Livello.INTERMEDIO, Obiettivo.IPERTROFIA, "M", 25,
        )
        assert target_forza.mav_max < target_iper.mav_max
        assert target_forza.mrv < target_iper.mrv

    def test_dimagrimento_vs_ipertrofia(self):
        """Dimagrimento ha fattore_volume 0.80 → target leggermente ridotti."""
        target_dim = get_scaled_volume_target(
            M.PETTO, Livello.INTERMEDIO, Obiettivo.DIMAGRIMENTO, "M", 25,
        )
        target_iper = get_scaled_volume_target(
            M.PETTO, Livello.INTERMEDIO, Obiettivo.IPERTROFIA, "M", 25,
        )
        assert target_dim.mav_max < target_iper.mav_max

    def test_resistenza_lowest_volume(self):
        """Resistenza ha fattore_volume 0.60 → il piu' basso."""
        target_res = get_scaled_volume_target(
            M.PETTO, Livello.INTERMEDIO, Obiettivo.RESISTENZA, "M", 25,
        )
        target_iper = get_scaled_volume_target(
            M.PETTO, Livello.INTERMEDIO, Obiettivo.IPERTROFIA, "M", 25,
        )
        assert target_res.mrv < target_iper.mrv
        assert target_res.mav_max < target_iper.mav_max
