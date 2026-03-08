"""
Training Science Engine — Modello di volume MEV/MAV/MRV.

Il volume e' la variabile piu' importante per l'ipertrofia (Schoenfeld 2017)
e deve essere gestito con precisione per ogni gruppo muscolare.

Modello a 3 soglie (Israetel, Renaissance Periodization 2020):
  MEV (Minimum Effective Volume) — sotto questa soglia: zero stimolo
  MAV (Maximum Adaptive Volume) — range ottimale per la crescita
  MRV (Maximum Recoverable Volume) — oltre: overtraining, regresso

I valori cambiano per:
  1. Gruppo muscolare (quadricipiti tollerano piu' volume dei bicipiti)
  2. Livello di esperienza (avanzati necessitano e tollerano piu' volume)
  3. Obiettivo (ipertrofia usa i valori base, altri obiettivi scalano)

Unita': serie dirette effettive per settimana.

Fonti:
  - Israetel — "Scientific Principles of Hypertrophy Training" (2020)
  - Schoenfeld — "Dose-response relationship for RT volume" (2017)
  - Schoenfeld — "Resistance Training Recommendations" (2021)
  - Krieger — "Single vs multiple sets" (2010)
"""

from typing import Optional

from .types import GruppoMuscolare as M, Livello, Obiettivo, VolumeTarget
from .principles import PARAMETRI_CARICO
from .types import PatternMovimento
from .muscle_contribution import compute_effective_sets


# ════════════════════════════════════════════════════════════
# FATTORI DEMOGRAFICI — Scaling per sesso ed eta'
# ════════════════════════════════════════════════════════════
#
# I target di volume base sono calibrati per maschi 18-30 anni
# (popolazione di riferimento nella letteratura Israetel/Schoenfeld).
#
# Le donne hanno livelli di testosterone ~15x inferiori (Vingren 2010),
# il che riduce la capacita' di generare e recuperare da ipertrofia.
# Meta-analysis Schoenfeld (2017): le donne rispondono all'~85% dello
# stimolo maschile a parita' di volume relativo.
#
# L'eta' riduce la capacita' di recupero (Häkkinen 2001) e la risposta
# anabolica (Peterson 2011). La sarcopenia accelera dopo i 45 anni.
#
# Questi fattori scalano solo MAV_min e MAV_max (il range ottimale).
# MEV e MRV restano invariati: sono soglie fisiologiche assolute.

_SEX_FACTOR: dict[str, float] = {
    "M": 1.0,   # Maschio — baseline (riferimento letteratura)
    "F": 0.85,  # Femmina — Schoenfeld 2017, Vingren 2010
}

_AGE_BRACKETS: list[tuple[int, int, float]] = [
    # (eta_min, eta_max, fattore)
    (0, 29, 1.0),    # Under 30 — piena capacita' di recupero
    (30, 44, 0.95),   # 30-44 — lieve riduzione (Häkkinen 2001)
    (45, 59, 0.85),   # 45-59 — riduzione significativa (Peterson 2011)
    (60, 100, 0.75),  # 60+ — recupero rallentato, sarcopenia
]


def get_demographic_factor(
    sesso: Optional[str] = None,
    eta: Optional[int] = None,
) -> float:
    """
    Calcola il fattore di scaling demografico combinato.

    Moltiplica sex_factor × age_factor. Se entrambi sono None, ritorna 1.0.
    Il fattore finale scala MAV_min e MAV_max (non MEV/MRV).

    Esempi:
      Uomo 25 → 1.0 × 1.0 = 1.0
      Donna 25 → 0.85 × 1.0 = 0.85
      Uomo 50 → 1.0 × 0.85 = 0.85
      Donna 50 → 0.85 × 0.85 = 0.72
    """
    sex_f = _SEX_FACTOR.get(sesso, 1.0) if sesso else 1.0

    age_f = 1.0
    if eta is not None:
        for lo, hi, factor in _AGE_BRACKETS:
            if lo <= eta <= hi:
                age_f = factor
                break

    return round(sex_f * age_f, 3)


# ════════════════════════════════════════════════════════════
# TABELLA MEV/MAV/MRV — Valori per IPERTROFIA (base)
# ════════════════════════════════════════════════════════════
#
# Formato: (MEV, MAV_min, MAV_max, MRV, note)
# Livello PRINCIPIANTE: MAV basso, necessario meno stimolo
# Livello INTERMEDIO: MAV medio, adattamento consolidato
# Livello AVANZATO: MAV alto, serve piu' volume per progredire
#
# Fonte primaria: Israetel (RP), cross-validato con Schoenfeld 2017.

# ── NOTA CALIBRAZIONE ──
# I target sono calibrati per i pesi ipertrofici corretti:
#   primario (1.0 EMG) = 1.0 set, sinergista (0.7) = 0.5 set,
#   sinergista minore (0.4) = 0.25 set, stabilizzatore (0.2) = 0.0.
# Israetel RP 2020: "count indirect volume as roughly half a set".
# I valori riflettono il volume EFFETTIVO contato da compute_hypertrophy_sets().
#
# Muscoli con solo volume primario (petto, quadricipiti, polpacci):
#   target dipende dal numero di slot diretti nel piano.
# Muscoli con forte volume indiretto (trapezio, core, avambracci, delt_ant):
#   MEV=0, target piu' bassi perche' il peso 0.5 riduce il conteggio.

_VOLUME_TABLE: dict[M, dict[Livello, tuple[float, float, float, float, str]]] = {
    M.PETTO: {
        # Solo push_h (1.0). Piano 4x: 2 upper × 5set = 10 diretto.
        Livello.PRINCIPIANTE: (4, 6, 8, 12, ""),
        Livello.INTERMEDIO: (4, 8, 12, 16, ""),
        Livello.AVANZATO: (6, 12, 16, 20, ""),
    },
    M.DORSALI: {
        # pull_h(1.0) + pull_v(1.0) + hinge(0.25). Hub muscle: 2 pattern primari.
        # Piano 4x: 2×(4+3) + 2×3×0.25 = 15.5.
        # MRV alto: dorsali tollerano volume elevato (Israetel RP 2020).
        # MAV rialzato +2 per riflettere il doppio pattern primario.
        Livello.PRINCIPIANTE: (4, 8, 12, 18, "Include lat + romboidi"),
        Livello.INTERMEDIO: (4, 12, 18, 25, ""),
        Livello.AVANZATO: (6, 16, 22, 28, ""),
    },
    M.DELT_ANT: {
        # push_v(1.0) + push_h(0.5). Volume indiretto dominante.
        Livello.PRINCIPIANTE: (0, 0, 4, 8, "Volume indiretto da push sufficiente"),
        Livello.INTERMEDIO: (0, 0, 8, 14, "Riceve push_h(0.5) + push_v(1.0)"),
        Livello.AVANZATO: (0, 0, 10, 16, ""),
    },
    M.DELT_LAT: {
        # lateral_raise(1.0) + push_v(0.5). Piano 4x: 2×3 + 2×3×0.5 = 9.
        Livello.PRINCIPIANTE: (4, 6, 8, 12, "Richiede isolamento diretto"),
        Livello.INTERMEDIO: (4, 8, 12, 16, ""),
        Livello.AVANZATO: (6, 10, 16, 20, ""),
    },
    M.DELT_POST: {
        # face_pull(1.0) + pull_h(0.5) + pull_v(0.25) + rotation(0.25).
        Livello.PRINCIPIANTE: (0, 4, 6, 10, "Volume indiretto da pull"),
        Livello.INTERMEDIO: (0, 6, 10, 14, ""),
        Livello.AVANZATO: (0, 8, 14, 18, ""),
    },
    M.BICIPITI: {
        # curl(1.0) + pull_h(0.5) + pull_v(0.5). Hub muscle: volume indiretto
        # da ogni pull. MAV rialzato +2 per riflettere il doppio contributo indiretto.
        Livello.PRINCIPIANTE: (4, 6, 10, 14, ""),
        Livello.INTERMEDIO: (4, 10, 14, 18, ""),
        Livello.AVANZATO: (4, 12, 18, 22, ""),
    },
    M.TRICIPITI: {
        # extension(1.0) + push_h(0.5) + push_v(0.5). Hub muscle: volume indiretto
        # da ogni push. MAV rialzato +2 per riflettere il doppio contributo indiretto.
        Livello.PRINCIPIANTE: (2, 6, 8, 12, "Volume indiretto da push significativo"),
        Livello.INTERMEDIO: (2, 8, 12, 16, ""),
        Livello.AVANZATO: (4, 10, 16, 20, ""),
    },
    M.QUADRICIPITI: {
        # squat(1.0) + leg_extension(1.0) + leg_press(1.0). Hub muscle: riceve
        # volume diretto da 2-3 esercizi in schede standard. Piano 4x: 2×4 + 3 + 3 = 14.
        # MAV rialzato +2 per intermedio/avanzato per evitare falsi "eccesso".
        Livello.PRINCIPIANTE: (4, 6, 10, 14, ""),
        Livello.INTERMEDIO: (4, 10, 16, 20, ""),
        Livello.AVANZATO: (6, 14, 20, 24, ""),
    },
    M.FEMORALI: {
        # hinge(1.0) + leg_curl(1.0) + squat(0.25). Piano 4x: 2×3 + 2 + 2×4×0.25 = 10.
        Livello.PRINCIPIANTE: (4, 6, 8, 12, ""),
        Livello.INTERMEDIO: (4, 8, 12, 16, ""),
        Livello.AVANZATO: (4, 10, 16, 20, ""),
    },
    M.GLUTEI: {
        # hinge(1.0) + squat(0.5) + hip_thrust(1.0). Volume indiretto forte.
        Livello.PRINCIPIANTE: (0, 4, 6, 10, "Volume indiretto da squat/hinge"),
        Livello.INTERMEDIO: (0, 6, 10, 14, ""),
        Livello.AVANZATO: (0, 8, 14, 18, ""),
    },
    M.POLPACCI: {
        # calf_raise(1.0) solo. Piano 4x: 2×(3-6) = 6-12.
        Livello.PRINCIPIANTE: (4, 6, 8, 12, "Richiedono alta frequenza e rep"),
        Livello.INTERMEDIO: (4, 8, 12, 16, ""),
        Livello.AVANZATO: (6, 10, 14, 18, ""),
    },
    M.TRAPEZIO: {
        # pull_h(0.5) + carry(0.5) + push_v/pull_v/hinge(0.25). Hub muscle.
        Livello.PRINCIPIANTE: (0, 4, 6, 10, "Volume indiretto da pull/hinge/carry"),
        Livello.INTERMEDIO: (0, 6, 10, 16, ""),
        Livello.AVANZATO: (0, 8, 14, 20, ""),
    },
    M.CORE: {
        # rotation(0.5) + carry(0.5) + squat/hinge(0.25). Hub muscle.
        Livello.PRINCIPIANTE: (0, 4, 6, 10, "Volume indiretto da compound"),
        Livello.INTERMEDIO: (0, 6, 10, 14, ""),
        Livello.AVANZATO: (0, 8, 14, 18, ""),
    },
    M.AVAMBRACCI: {
        # carry(1.0) + pull_h/pull_v/curl(0.25). Carry = primario.
        # MRV piu' alto: avambracci hanno alta densita' fibre lente,
        # recuperano piu' velocemente (Israetel RP 2020).
        Livello.PRINCIPIANTE: (0, 2, 4, 10, "Volume indiretto da pull/carry"),
        Livello.INTERMEDIO: (0, 4, 8, 12, "Carry conta come volume primario (Israetel RP 2020)"),
        Livello.AVANZATO: (0, 6, 10, 14, "Carry conta come volume primario (Israetel RP 2020)"),
    },
    M.ADDUTTORI: {
        # adductor(1.0) + squat(0.25). Volume indiretto minimo.
        Livello.PRINCIPIANTE: (0, 2, 4, 8, "Volume indiretto da squat"),
        Livello.INTERMEDIO: (0, 4, 8, 10, ""),
        Livello.AVANZATO: (0, 6, 10, 12, ""),
    },
}


def get_volume_target(muscolo: M, livello: Livello) -> VolumeTarget:
    """
    Ritorna il volume target (MEV/MAV/MRV) per un muscolo ad un dato livello.
    Questi sono i valori BASE per ipertrofia. Per altri obiettivi, usare
    get_scaled_volume_target() che applica il fattore_volume dell'obiettivo.
    """
    mev, mav_min, mav_max, mrv, note = _VOLUME_TABLE[muscolo][livello]
    return VolumeTarget(
        muscolo=muscolo,
        mev=mev,
        mav_min=mav_min,
        mav_max=mav_max,
        mrv=mrv,
        note=note,
    )


def get_scaled_volume_target(
    muscolo: M,
    livello: Livello,
    obiettivo: Obiettivo,
    sesso: Optional[str] = None,
    eta: Optional[int] = None,
) -> VolumeTarget:
    """
    Ritorna il volume target scalato per obiettivo + profilo demografico.

    Scaling a 2 livelli (moltiplicativi):
    1. fattore_volume (obiettivo): Ipertrofia=1.0, Forza=0.7, Resistenza=0.6
    2. fattore_demografico (sesso × eta'): Donna 50y → 0.85 × 0.85 = 0.72

    Il fattore composto scala MAV_min e MAV_max (il range dove "devi stare").
    MEV e MRV rimangono invariati (sono soglie fisiologiche assolute):
    - MEV: sotto questa soglia zero stimolo, indipendente dal sesso/eta'
    - MRV: oltre questa soglia overtraining, limite fisiologico universale

    Fonti: Israetel RP 2020, Schoenfeld 2017, Vingren 2010,
           Häkkinen 2001, Peterson 2011.
    """
    base = get_volume_target(muscolo, livello)
    obj_factor = PARAMETRI_CARICO[obiettivo].fattore_volume
    demo_factor = get_demographic_factor(sesso, eta)
    combined = obj_factor * demo_factor

    return VolumeTarget(
        muscolo=muscolo,
        mev=base.mev,
        mav_min=round(base.mav_min * combined, 1),
        mav_max=round(base.mav_max * combined, 1),
        mrv=base.mrv,
        note=base.note,
    )


def get_all_volume_targets(
    livello: Livello,
    obiettivo: Obiettivo,
    sesso: Optional[str] = None,
    eta: Optional[int] = None,
) -> dict[M, VolumeTarget]:
    """Ritorna i volume target per tutti i gruppi muscolari."""
    return {
        m: get_scaled_volume_target(m, livello, obiettivo, sesso, eta)
        for m in M
    }


def classify_volume(serie_effettive: float, target: VolumeTarget) -> str:
    """
    Classifica il volume effettivo rispetto al target.

    Ritorna:
      "sotto_mev"  — insufficiente, nessuno stimolo
      "mev_mav"    — sopra MEV ma sotto MAV ottimale
      "ottimale"   — nel range MAV (zona ideale)
      "sopra_mav"  — sopra MAV ma sotto MRV (volume alto ma recuperabile)
      "sopra_mrv"  — overtraining, recupero compromesso
    """
    if serie_effettive < target.mev:
        return "sotto_mev"
    if serie_effettive < target.mav_min:
        return "mev_mav"
    if serie_effettive <= target.mav_max:
        return "ottimale"
    if serie_effettive <= target.mrv:
        return "sopra_mav"
    return "sopra_mrv"


def analyze_volume(
    slots: list[tuple[PatternMovimento, int]],
    livello: Livello,
    obiettivo: Obiettivo,
) -> dict[M, dict]:
    """
    Analisi completa del volume di un piano di allenamento.

    Input: lista di (pattern, serie) per l'intera settimana.
    Output: per ogni muscolo → serie effettive + target + classificazione.

    Esempio:
        slots = [
            (P.PUSH_H, 4), (P.PUSH_V, 3),  # Upper A
            (P.PULL_H, 4), (P.PULL_V, 3),   # Upper B
            (P.SQUAT, 4), (P.HINGE, 3),     # Lower
        ]
        result = analyze_volume(slots, Livello.INTERMEDIO, Obiettivo.IPERTROFIA)
        # result[M.PETTO] = {
        #     "serie_effettive": 4.0,
        #     "target": VolumeTarget(...),
        #     "stato": "sotto_mev",
        # }
    """
    effective = compute_effective_sets(slots)
    targets = get_all_volume_targets(livello, obiettivo)

    result: dict[M, dict] = {}
    for muscolo in M:
        serie = round(effective.get(muscolo, 0.0), 1)
        target = targets[muscolo]
        result[muscolo] = {
            "serie_effettive": serie,
            "target": target,
            "stato": classify_volume(serie, target),
        }
    return result
