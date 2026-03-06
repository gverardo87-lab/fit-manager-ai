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

from .types import GruppoMuscolare as M, Livello, Obiettivo, VolumeTarget
from .principles import PARAMETRI_CARICO
from .types import PatternMovimento
from .muscle_contribution import compute_effective_sets


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

_VOLUME_TABLE: dict[M, dict[Livello, tuple[float, float, float, float, str]]] = {
    M.PETTO: {
        Livello.PRINCIPIANTE: (6, 8, 10, 14, ""),
        Livello.INTERMEDIO: (6, 12, 16, 20, ""),
        Livello.AVANZATO: (6, 16, 22, 22, ""),
    },
    M.DORSALI: {
        Livello.PRINCIPIANTE: (6, 8, 10, 16, "Include lat + romboidi"),
        Livello.INTERMEDIO: (6, 14, 18, 22, ""),
        Livello.AVANZATO: (6, 18, 24, 25, ""),
    },
    M.DELT_ANT: {
        Livello.PRINCIPIANTE: (0, 0, 4, 8, "Volume indiretto da push sufficiente"),
        Livello.INTERMEDIO: (0, 0, 6, 14, "MRV alto: muscolo piccolo, recupero rapido (Israetel RP 2020)"),
        Livello.AVANZATO: (0, 0, 8, 16, "MRV alto: muscolo piccolo, recupero rapido (Israetel RP 2020)"),
    },
    M.DELT_LAT: {
        Livello.PRINCIPIANTE: (6, 8, 10, 16, "Richiede isolamento diretto"),
        Livello.INTERMEDIO: (6, 14, 18, 22, ""),
        Livello.AVANZATO: (6, 18, 24, 26, "Tollerano molto volume"),
    },
    M.DELT_POST: {
        Livello.PRINCIPIANTE: (0, 6, 8, 14, "Volume indiretto da pull"),
        Livello.INTERMEDIO: (0, 10, 14, 18, ""),
        Livello.AVANZATO: (0, 14, 18, 22, ""),
    },
    M.BICIPITI: {
        Livello.PRINCIPIANTE: (4, 6, 8, 14, ""),
        Livello.INTERMEDIO: (4, 10, 14, 20, ""),
        Livello.AVANZATO: (4, 14, 20, 26, "Tollerano molto volume"),
    },
    M.TRICIPITI: {
        Livello.PRINCIPIANTE: (4, 4, 6, 10, "Volume indiretto da push significativo"),
        Livello.INTERMEDIO: (4, 8, 12, 14, ""),
        Livello.AVANZATO: (4, 10, 16, 18, ""),
    },
    M.QUADRICIPITI: {
        Livello.PRINCIPIANTE: (6, 8, 10, 14, ""),
        Livello.INTERMEDIO: (6, 12, 16, 18, ""),
        Livello.AVANZATO: (6, 16, 22, 24, "MRV alto: avanzati tollerano volume elevato (Israetel RP 2020)"),
    },
    M.FEMORALI: {
        Livello.PRINCIPIANTE: (4, 6, 8, 12, ""),
        Livello.INTERMEDIO: (4, 10, 14, 16, ""),
        Livello.AVANZATO: (4, 12, 18, 20, "MRV = MAV_max + 2 (buffer standard Israetel RP 2020)"),
    },
    M.GLUTEI: {
        Livello.PRINCIPIANTE: (0, 4, 6, 10, "Volume indiretto da squat/hinge"),
        Livello.INTERMEDIO: (0, 6, 10, 14, ""),
        Livello.AVANZATO: (0, 8, 14, 16, ""),
    },
    M.POLPACCI: {
        Livello.PRINCIPIANTE: (6, 8, 10, 14, "Richiedono alta frequenza e rep"),
        Livello.INTERMEDIO: (6, 10, 14, 16, ""),
        Livello.AVANZATO: (6, 12, 16, 16, ""),
    },
    M.TRAPEZIO: {
        Livello.PRINCIPIANTE: (0, 4, 6, 14, "Volume indiretto da pull/hinge"),
        Livello.INTERMEDIO: (0, 8, 12, 20, ""),
        Livello.AVANZATO: (0, 12, 18, 26, "Tollerano molto volume"),
    },
    M.CORE: {
        Livello.PRINCIPIANTE: (0, 4, 8, 14, "Volume indiretto da compound"),
        Livello.INTERMEDIO: (0, 8, 12, 16, ""),
        Livello.AVANZATO: (0, 10, 16, 20, ""),
    },
    M.AVAMBRACCI: {
        Livello.PRINCIPIANTE: (0, 2, 4, 8, "Volume indiretto da pull/carry"),
        Livello.INTERMEDIO: (0, 4, 6, 10, ""),
        Livello.AVANZATO: (0, 4, 8, 12, ""),
    },
    M.ADDUTTORI: {
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
    muscolo: M, livello: Livello, obiettivo: Obiettivo
) -> VolumeTarget:
    """
    Ritorna il volume target scalato per l'obiettivo.

    Il fattore_volume scala il range MAV:
    - Ipertrofia: 1.0 (valori base)
    - Forza: 0.7 (meno volume, piu' intensita')
    - Dimagrimento: 0.8 (volume moderato per preservare)
    - Tonificazione: 0.7
    - Resistenza: 0.6 (meno serie, piu' rep)

    MEV e MRV rimangono invariati (sono soglie fisiologiche assolute).
    """
    base = get_volume_target(muscolo, livello)
    factor = PARAMETRI_CARICO[obiettivo].fattore_volume
    return VolumeTarget(
        muscolo=muscolo,
        mev=base.mev,
        mav_min=round(base.mav_min * factor, 1),
        mav_max=round(base.mav_max * factor, 1),
        mrv=base.mrv,
        note=base.note,
    )


def get_all_volume_targets(
    livello: Livello, obiettivo: Obiettivo
) -> dict[M, VolumeTarget]:
    """Ritorna i volume target per tutti i gruppi muscolari."""
    return {m: get_scaled_volume_target(m, livello, obiettivo) for m in M}


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
