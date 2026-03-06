"""
Training Science Engine — Rapporti biomeccanici e equilibrio posturale.

Squilibri tra catene muscolari sono la causa principale di infortuni
e problemi posturali. Questo modulo definisce i rapporti target e
analizza l'equilibrio di un piano di allenamento.

Fonti:
  - Sahrmann — "Movement System Impairment Syndromes" (2002)
  - Janda — "Muscles: Testing and Function" (1983)
  - NSCA — "Essentials of Strength Training" (2016) cap. 21
  - Alentorn-Geli — "Prevention of ACL injuries" (2009)
"""

from .types import (
    GruppoMuscolare as M,
    PatternMovimento as P,
    RapportoBiomeccanico,
    AnalisiBalance,
)
from .muscle_contribution import compute_effective_sets


# ════════════════════════════════════════════════════════════
# RAPPORTI TARGET
# ════════════════════════════════════════════════════════════

BALANCE_RATIOS: list[RapportoBiomeccanico] = [
    RapportoBiomeccanico(
        nome="Push : Pull",
        numeratore=["push_h", "push_v"],
        denominatore=["pull_h", "pull_v"],
        target=1.0,
        tolleranza=0.15,
        fonte="NSCA 2016, Sahrmann 2002 — equilibrio articolazione spalla",
    ),
    RapportoBiomeccanico(
        nome="Push Orizz : Push Vert",
        numeratore=["push_h"],
        denominatore=["push_v"],
        target=1.5,
        tolleranza=0.30,
        fonte="Pratica clinica — petto e spalle bilanciati",
    ),
    RapportoBiomeccanico(
        nome="Pull Orizz : Pull Vert",
        numeratore=["pull_h"],
        denominatore=["pull_v"],
        target=1.0,
        tolleranza=0.35,
        fonte="NSCA — dorsali: spessore (row) + larghezza (pulldown). "
        "Tolleranza ampia: pull_h recluta piu' massa muscolare (trapezio 0.7 vs 0.4), "
        "squilibrio lieve e' fisiologico (Sahrmann 2002)",
    ),
    RapportoBiomeccanico(
        nome="Quad : Ham",
        numeratore=["quadricipiti"],
        denominatore=["femorali"],
        target=1.25,
        tolleranza=0.30,
        fonte="Alentorn-Geli 2009 — stabilita' ginocchio, prevenzione ACL. "
        "Range 1.0-1.5 accettabile (NSCA 2016: rapporto altamente individuale)",
    ),
    RapportoBiomeccanico(
        nome="Anteriore : Posteriore",
        numeratore=["petto", "deltoide_anteriore", "quadricipiti"],
        denominatore=["dorsali", "deltoide_posteriore", "femorali"],
        target=0.85,
        tolleranza=0.15,
        fonte="Sahrmann 2002, Janda 1983 — prevenzione upper/lower cross syndrome",
    ),
]


# ════════════════════════════════════════════════════════════
# PATTERN → CATENA per il calcolo rapporti
# ════════════════════════════════════════════════════════════

# Quali pattern contano come "push" e "pull" nel rapporto volume
_PUSH_PATTERNS = {P.PUSH_H, P.PUSH_V}
_PULL_PATTERNS = {P.PULL_H, P.PULL_V}


def _sum_pattern_sets(
    slots: list[tuple[P, int]], patterns: set[P]
) -> float:
    """Somma le serie per un gruppo di pattern."""
    return sum(s for p, s in slots if p in patterns)


def _sum_muscle_sets(
    effective: dict[M, float], muscle_names: list[str]
) -> float:
    """Somma le serie effettive per una lista di nomi muscolo."""
    total = 0.0
    for name in muscle_names:
        for m in M:
            if m.value == name:
                total += effective.get(m, 0.0)
                break
    return total


def analyze_balance(
    slots: list[tuple[P, int]],
) -> AnalisiBalance:
    """
    Analizza i rapporti biomeccanici di un piano settimanale.

    Input: lista di (pattern, serie) per l'intera settimana.
    Output: rapporti calcolati vs target, con lista squilibri.
    """
    effective = compute_effective_sets(slots)
    rapporti: dict[str, float] = {}
    target: dict[str, float] = {}
    squilibri: list[str] = []

    for ratio in BALANCE_RATIOS:
        # Determina se il rapporto e' su pattern o muscoli
        is_pattern_ratio = ratio.numeratore[0] in {p.value for p in P}

        if is_pattern_ratio:
            num_patterns = {P(v) for v in ratio.numeratore if v in {p.value for p in P}}
            den_patterns = {P(v) for v in ratio.denominatore if v in {p.value for p in P}}
            num_val = _sum_pattern_sets(slots, num_patterns)
            den_val = _sum_pattern_sets(slots, den_patterns)
        else:
            num_val = _sum_muscle_sets(effective, ratio.numeratore)
            den_val = _sum_muscle_sets(effective, ratio.denominatore)

        if den_val > 0:
            computed = round(num_val / den_val, 2)
        elif num_val > 0:
            computed = 99.0  # denominatore zero con numeratore presente = squilibrio totale
        else:
            computed = ratio.target  # entrambi zero = neutro

        rapporti[ratio.nome] = computed
        target[ratio.nome] = ratio.target

        if abs(computed - ratio.target) > ratio.tolleranza:
            direction = "alto" if computed > ratio.target else "basso"
            squilibri.append(
                f"{ratio.nome}: {computed:.2f} (target {ratio.target:.2f}, troppo {direction})"
            )

    return AnalisiBalance(
        rapporti=rapporti,
        target=target,
        squilibri=squilibri,
    )
