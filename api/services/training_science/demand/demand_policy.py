"""Demand Policy v1 — ceiling check tra demand vector e protocollo.

Dato un esercizio (con il suo demand vector) e un protocollo (con il suo ceiling),
produce un verdetto deterministico per-dimensione:
- pass: sotto il ceiling
- fail: sopra il ceiling (hard gate)
- family_discouraged: demand family sconsigliata
- family_excluded: demand family esclusa (hard gate)

Il policy engine non decide il ranking: informa il feasibility engine
e il ranker su quali candidati rispettano i limiti del protocollo.
"""

from dataclasses import dataclass
from typing import Literal

from .demand_types import DemandCeiling, DemandFamily, ExerciseDemandVector

DemandCheckVerdict = Literal["pass", "ceiling_exceeded", "family_discouraged", "family_excluded"]

DEMAND_POLICY_VERSION = "smart-demand-policy-v1"


@dataclass(frozen=True)
class DimensionFinding:
    """Singolo finding per una dimensione del demand vector."""

    dimension: str
    exercise_value: int
    ceiling_value: int
    verdict: Literal["pass", "ceiling_exceeded"]


@dataclass(frozen=True)
class FamilyFinding:
    """Finding per una demand family dell'esercizio."""

    family: DemandFamily
    verdict: Literal["family_discouraged", "family_excluded"]


@dataclass(frozen=True)
class DemandPolicyResult:
    """Risultato completo del ceiling check per un singolo esercizio."""

    overall_verdict: DemandCheckVerdict
    dimension_findings: tuple[DimensionFinding, ...]
    family_findings: tuple[FamilyFinding, ...]
    violations_count: int
    discouraged_count: int

    @property
    def is_hard_fail(self) -> bool:
        return self.overall_verdict in ("ceiling_exceeded", "family_excluded")


_CEILING_FIELDS = (
    ("skill_demand", "max_skill_demand"),
    ("coordination_demand", "max_coordination_demand"),
    ("stability_demand", "max_stability_demand"),
    ("ballistic_demand", "max_ballistic_demand"),
    ("impact_demand", "max_impact_demand"),
    ("axial_load_demand", "max_axial_load_demand"),
    ("shoulder_complex_demand", "max_shoulder_complex_demand"),
    ("lumbar_load_demand", "max_lumbar_load_demand"),
    ("grip_demand", "max_grip_demand"),
    ("metabolic_demand", "max_metabolic_demand"),
)


def check_demand_ceiling(
    vector: ExerciseDemandVector,
    ceiling: DemandCeiling,
) -> DemandPolicyResult:
    """Verifica un demand vector contro un ceiling di protocollo.

    Puro e deterministico. Nessun side-effect.
    """
    dimension_findings: list[DimensionFinding] = []
    violations_count = 0

    for dim_name, ceil_name in _CEILING_FIELDS:
        max_val = getattr(ceiling, ceil_name)
        if max_val is None:
            continue
        ex_val = getattr(vector, dim_name)
        if ex_val > max_val:
            dimension_findings.append(
                DimensionFinding(
                    dimension=dim_name,
                    exercise_value=ex_val,
                    ceiling_value=max_val,
                    verdict="ceiling_exceeded",
                )
            )
            violations_count += 1
        else:
            dimension_findings.append(
                DimensionFinding(
                    dimension=dim_name,
                    exercise_value=ex_val,
                    ceiling_value=max_val,
                    verdict="pass",
                )
            )

    family_findings: list[FamilyFinding] = []
    discouraged_count = 0
    has_excluded = False

    for family in vector.demand_families:
        if family in ceiling.excluded_families:
            family_findings.append(FamilyFinding(family=family, verdict="family_excluded"))
            has_excluded = True
        elif family in ceiling.discouraged_families:
            family_findings.append(FamilyFinding(family=family, verdict="family_discouraged"))
            discouraged_count += 1

    if has_excluded:
        overall = "family_excluded"
    elif violations_count > 0:
        overall = "ceiling_exceeded"
    elif discouraged_count > 0:
        overall = "family_discouraged"
    else:
        overall = "pass"

    return DemandPolicyResult(
        overall_verdict=overall,
        dimension_findings=tuple(dimension_findings),
        family_findings=tuple(family_findings),
        violations_count=violations_count,
        discouraged_count=discouraged_count,
    )
