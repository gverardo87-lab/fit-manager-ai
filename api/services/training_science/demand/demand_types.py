"""Tipi del Demand Vector SMART/KineScore v1.

Il Demand Vector descrive il *costo* biomeccanico-funzionale di un esercizio
su 10 dimensioni ordinali (0..4). Separa:
- pattern → cosa allena
- muscle contribution → quanto stimola
- demand vector → quanto costa eseguirlo

Fonte concettuale: NSCA-2016, ACSM-2009, Sahrmann-2002, Alentorn-Geli-2009.
"""

from dataclasses import dataclass
from typing import Literal

DemandLevel = Literal[0, 1, 2, 3, 4]
"""Scala ordinale 0..4: none/minimal, low, moderate, high, very_high."""

EvidenceClass = Literal[
    "A_direct_repo_anchor",
    "B_biomechanical_inference",
    "C_provisional_expert_model",
]

DemandFamily = Literal[
    "low_skill_general",
    "high_skill_upper",
    "ballistic_lower",
    "high_axial_loading",
    "shoulder_overhead_heavy",
    "lumbar_bracing_heavy",
    "grip_limited",
    "metabolic_dense",
]

DEMAND_VERSION = "smart-demand-v1"


@dataclass(frozen=True)
class ExerciseDemandVector:
    """Vettore biomeccanico-funzionale a 10 dimensioni per un esercizio.

    Ogni dimensione e' ordinale (0..4):
    - 0 = none/minimal
    - 1 = low
    - 2 = moderate
    - 3 = high
    - 4 = very_high
    """

    skill_demand: DemandLevel
    coordination_demand: DemandLevel
    stability_demand: DemandLevel
    ballistic_demand: DemandLevel
    impact_demand: DemandLevel
    axial_load_demand: DemandLevel
    shoulder_complex_demand: DemandLevel
    lumbar_load_demand: DemandLevel
    grip_demand: DemandLevel
    metabolic_demand: DemandLevel
    demand_families: tuple[DemandFamily, ...] = ()
    evidence_class: EvidenceClass = "C_provisional_expert_model"
    rationale_tags: tuple[str, ...] = ()
    source_anchors: tuple[str, ...] = ()

    def exceeds_any(self, ceiling: "DemandCeiling") -> list[str]:
        """Restituisce le dimensioni che superano il ceiling dato."""
        violations: list[str] = []
        for dim_name in _CEILING_DIMENSIONS:
            max_val = getattr(ceiling, f"max_{dim_name}", None)
            if max_val is not None and getattr(self, dim_name) > max_val:
                violations.append(dim_name)
        return violations


_CEILING_DIMENSIONS = (
    "skill_demand",
    "coordination_demand",
    "stability_demand",
    "ballistic_demand",
    "impact_demand",
    "axial_load_demand",
    "shoulder_complex_demand",
    "lumbar_load_demand",
    "grip_demand",
    "metabolic_demand",
)


@dataclass(frozen=True)
class DemandCeiling:
    """Limiti massimi per dimensione, dichiarati dal protocollo.

    None = nessun limite su quella dimensione.
    """

    max_skill_demand: DemandLevel | None = None
    max_coordination_demand: DemandLevel | None = None
    max_stability_demand: DemandLevel | None = None
    max_ballistic_demand: DemandLevel | None = None
    max_impact_demand: DemandLevel | None = None
    max_axial_load_demand: DemandLevel | None = None
    max_shoulder_complex_demand: DemandLevel | None = None
    max_lumbar_load_demand: DemandLevel | None = None
    max_grip_demand: DemandLevel | None = None
    max_metabolic_demand: DemandLevel | None = None
    discouraged_families: tuple[DemandFamily, ...] = ()
    excluded_families: tuple[DemandFamily, ...] = ()
