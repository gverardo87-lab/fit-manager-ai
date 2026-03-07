"""Demand Registry v1 — vettori default per pattern e ceiling per protocollo.

Contiene:
1. Vettori demand di default per pattern_movimento × difficolta'
2. Ceiling per protocollo (PRT-001..006)

I vettori sono *default* ragionevoli: il mapping reale per-esercizio
sara' raffinato in un Catalog Mapping futuro.

Fonte: NSCA-2016, Sahrmann-2002, Alentorn-Geli-2009 (sezione 15 di UPG-59).
"""

from api.services.training_science.types import PatternMovimento

from .demand_types import DemandCeiling, DemandLevel, ExerciseDemandVector

DEMAND_REGISTRY_VERSION = "smart-demand-registry-v1"

# ──────────────────────────────────────────────────────────────────────
# 1. Pattern Default Vectors
#    Chiave: (pattern, difficulty) → ExerciseDemandVector
#    difficulty: "beginner" | "intermediate" | "advanced"
# ──────────────────────────────────────────────────────────────────────

_V = ExerciseDemandVector  # alias compatto


def _vec(
    sk: DemandLevel,
    co: DemandLevel,
    st: DemandLevel,
    ba: DemandLevel,
    im: DemandLevel,
    ax: DemandLevel,
    sh: DemandLevel,
    lu: DemandLevel,
    gr: DemandLevel,
    me: DemandLevel,
) -> ExerciseDemandVector:
    return _V(
        skill_demand=sk,
        coordination_demand=co,
        stability_demand=st,
        ballistic_demand=ba,
        impact_demand=im,
        axial_load_demand=ax,
        shoulder_complex_demand=sh,
        lumbar_load_demand=lu,
        grip_demand=gr,
        metabolic_demand=me,
        evidence_class="B_biomechanical_inference",
        source_anchors=("NSCA-2016", "SAHRMANN-2002"),
    )


#                                          sk co st ba im ax sh lu gr me
_PATTERN_DEFAULTS: dict[tuple[PatternMovimento, str], ExerciseDemandVector] = {
    # ── Squat ──
    (PatternMovimento.SQUAT, "beginner"):     _vec(1, 1, 1, 0, 0, 1, 0, 1, 0, 1),
    (PatternMovimento.SQUAT, "intermediate"): _vec(2, 2, 2, 0, 0, 2, 0, 2, 1, 2),
    (PatternMovimento.SQUAT, "advanced"):     _vec(2, 2, 2, 0, 0, 3, 1, 3, 1, 2),
    # ── Hinge ──
    (PatternMovimento.HINGE, "beginner"):     _vec(1, 1, 1, 0, 0, 1, 0, 2, 1, 1),
    (PatternMovimento.HINGE, "intermediate"): _vec(2, 2, 2, 0, 0, 2, 0, 3, 2, 2),
    (PatternMovimento.HINGE, "advanced"):     _vec(2, 2, 2, 0, 0, 3, 0, 3, 2, 2),
    # ── Push H ──
    (PatternMovimento.PUSH_H, "beginner"):     _vec(1, 1, 1, 0, 0, 0, 2, 0, 0, 1),
    (PatternMovimento.PUSH_H, "intermediate"): _vec(1, 1, 2, 0, 0, 0, 2, 1, 1, 1),
    (PatternMovimento.PUSH_H, "advanced"):     _vec(2, 2, 2, 0, 0, 0, 3, 1, 1, 1),
    # ── Push V ──
    (PatternMovimento.PUSH_V, "beginner"):     _vec(1, 1, 1, 0, 0, 1, 2, 1, 0, 1),
    (PatternMovimento.PUSH_V, "intermediate"): _vec(2, 2, 2, 0, 0, 1, 3, 1, 1, 1),
    (PatternMovimento.PUSH_V, "advanced"):     _vec(2, 2, 2, 0, 0, 2, 3, 1, 1, 1),
    # ── Pull H ──
    (PatternMovimento.PULL_H, "beginner"):     _vec(1, 1, 1, 0, 0, 0, 1, 1, 1, 1),
    (PatternMovimento.PULL_H, "intermediate"): _vec(1, 1, 1, 0, 0, 0, 1, 1, 2, 1),
    (PatternMovimento.PULL_H, "advanced"):     _vec(2, 2, 2, 0, 0, 0, 2, 1, 2, 1),
    # ── Pull V ──
    (PatternMovimento.PULL_V, "beginner"):     _vec(1, 1, 1, 0, 0, 0, 2, 0, 2, 1),
    (PatternMovimento.PULL_V, "intermediate"): _vec(2, 2, 2, 0, 0, 0, 2, 0, 2, 1),
    (PatternMovimento.PULL_V, "advanced"):     _vec(3, 3, 2, 0, 0, 0, 3, 0, 3, 2),
    # ── Core ──
    (PatternMovimento.CORE, "beginner"):     _vec(1, 1, 2, 0, 0, 0, 0, 1, 0, 1),
    (PatternMovimento.CORE, "intermediate"): _vec(1, 1, 2, 0, 0, 0, 0, 2, 0, 1),
    (PatternMovimento.CORE, "advanced"):     _vec(2, 2, 3, 0, 0, 1, 0, 2, 0, 1),
    # ── Rotation ──
    (PatternMovimento.ROTATION, "beginner"):     _vec(1, 2, 2, 0, 0, 0, 1, 1, 0, 1),
    (PatternMovimento.ROTATION, "intermediate"): _vec(2, 2, 2, 0, 0, 0, 1, 2, 1, 1),
    (PatternMovimento.ROTATION, "advanced"):     _vec(2, 3, 3, 0, 0, 1, 1, 2, 1, 1),
    # ── Carry ──
    (PatternMovimento.CARRY, "beginner"):     _vec(1, 1, 2, 0, 0, 2, 1, 2, 3, 2),
    (PatternMovimento.CARRY, "intermediate"): _vec(1, 1, 2, 0, 0, 3, 1, 2, 3, 2),
    (PatternMovimento.CARRY, "advanced"):     _vec(1, 1, 2, 0, 0, 4, 1, 3, 4, 3),
    # ── Isolation: Hip Thrust ──
    (PatternMovimento.HIP_THRUST, "beginner"):     _vec(1, 1, 1, 0, 0, 0, 0, 1, 0, 1),
    (PatternMovimento.HIP_THRUST, "intermediate"): _vec(1, 1, 1, 0, 0, 0, 0, 1, 0, 1),
    (PatternMovimento.HIP_THRUST, "advanced"):     _vec(1, 1, 1, 0, 0, 1, 0, 1, 0, 1),
    # ── Isolation: Curl ──
    (PatternMovimento.CURL, "beginner"):     _vec(0, 0, 0, 0, 0, 0, 0, 0, 1, 0),
    (PatternMovimento.CURL, "intermediate"): _vec(0, 0, 1, 0, 0, 0, 0, 0, 1, 0),
    (PatternMovimento.CURL, "advanced"):     _vec(1, 1, 1, 0, 0, 0, 0, 0, 2, 0),
    # ── Isolation: Extension Tri ──
    (PatternMovimento.EXTENSION_TRI, "beginner"):     _vec(0, 0, 0, 0, 0, 0, 1, 0, 0, 0),
    (PatternMovimento.EXTENSION_TRI, "intermediate"): _vec(0, 0, 1, 0, 0, 0, 1, 0, 0, 0),
    (PatternMovimento.EXTENSION_TRI, "advanced"):     _vec(1, 1, 1, 0, 0, 0, 1, 0, 1, 0),
    # ── Isolation: Lateral Raise ──
    (PatternMovimento.LATERAL_RAISE, "beginner"):     _vec(0, 0, 0, 0, 0, 0, 1, 0, 0, 0),
    (PatternMovimento.LATERAL_RAISE, "intermediate"): _vec(0, 1, 1, 0, 0, 0, 2, 0, 0, 0),
    (PatternMovimento.LATERAL_RAISE, "advanced"):     _vec(1, 1, 1, 0, 0, 0, 2, 0, 0, 0),
    # ── Isolation: Face Pull ──
    (PatternMovimento.FACE_PULL, "beginner"):     _vec(0, 1, 1, 0, 0, 0, 1, 0, 1, 0),
    (PatternMovimento.FACE_PULL, "intermediate"): _vec(0, 1, 1, 0, 0, 0, 1, 0, 1, 0),
    (PatternMovimento.FACE_PULL, "advanced"):     _vec(1, 1, 1, 0, 0, 0, 2, 0, 1, 0),
    # ── Isolation: Calf Raise ──
    (PatternMovimento.CALF_RAISE, "beginner"):     _vec(0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (PatternMovimento.CALF_RAISE, "intermediate"): _vec(0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (PatternMovimento.CALF_RAISE, "advanced"):     _vec(0, 0, 1, 0, 0, 1, 0, 0, 0, 0),
    # ── Isolation: Leg Curl ──
    (PatternMovimento.LEG_CURL, "beginner"):     _vec(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (PatternMovimento.LEG_CURL, "intermediate"): _vec(0, 0, 0, 0, 0, 0, 0, 0, 0, 1),
    (PatternMovimento.LEG_CURL, "advanced"):     _vec(0, 0, 0, 0, 0, 0, 0, 0, 0, 1),
    # ── Isolation: Leg Extension ──
    (PatternMovimento.LEG_EXTENSION, "beginner"):     _vec(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (PatternMovimento.LEG_EXTENSION, "intermediate"): _vec(0, 0, 0, 0, 0, 0, 0, 0, 0, 1),
    (PatternMovimento.LEG_EXTENSION, "advanced"):     _vec(0, 0, 0, 0, 0, 0, 0, 0, 0, 1),
    # ── Isolation: Adductor ──
    (PatternMovimento.ADDUCTOR, "beginner"):     _vec(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (PatternMovimento.ADDUCTOR, "intermediate"): _vec(0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    (PatternMovimento.ADDUCTOR, "advanced"):     _vec(0, 1, 1, 0, 0, 0, 0, 0, 0, 0),
}


_FALLBACK_VECTOR = _vec(1, 1, 1, 0, 0, 1, 1, 1, 1, 1)


def get_default_demand_vector(
    pattern: PatternMovimento,
    difficulty: str,
) -> ExerciseDemandVector:
    """Restituisce il vettore demand di default per pattern × difficolta'.

    Fallback a vettore conservativo se la combinazione non e' mappata.
    """
    return _PATTERN_DEFAULTS.get((pattern, difficulty), _FALLBACK_VECTOR)


# ──────────────────────────────────────────────────────────────────────
# 2. Protocol Ceiling Registry
#    Chiave: protocol_id → DemandCeiling
# ──────────────────────────────────────────────────────────────────────

PROTOCOL_CEILINGS: dict[str, DemandCeiling] = {
    # PRT-001: Beginner General 3x Full Body
    "PRT-001": DemandCeiling(
        max_skill_demand=2,
        max_coordination_demand=2,
        max_ballistic_demand=1,
        max_impact_demand=1,
        max_axial_load_demand=2,
        max_shoulder_complex_demand=2,
        max_lumbar_load_demand=2,
        discouraged_families=("high_axial_loading", "grip_limited"),
        excluded_families=("high_skill_upper", "ballistic_lower"),
    ),
    # PRT-002: Intermediate General 3x Full Body
    "PRT-002": DemandCeiling(
        max_skill_demand=3,
        max_coordination_demand=3,
        max_ballistic_demand=2,
        max_impact_demand=2,
        max_axial_load_demand=3,
        max_shoulder_complex_demand=3,
        max_lumbar_load_demand=3,
        discouraged_families=("high_skill_upper",),
        excluded_families=(),
    ),
    # PRT-003: Intermediate Hypertrophy 4x Upper Lower
    "PRT-003": DemandCeiling(
        max_skill_demand=3,
        max_coordination_demand=3,
        max_ballistic_demand=1,
        max_impact_demand=1,
        max_axial_load_demand=3,
        max_shoulder_complex_demand=3,
        max_lumbar_load_demand=3,
        discouraged_families=("ballistic_lower", "metabolic_dense"),
        excluded_families=(),
    ),
    # PRT-004: Intermediate Strength 4x Upper Lower
    "PRT-004": DemandCeiling(
        max_skill_demand=3,
        max_coordination_demand=3,
        max_ballistic_demand=2,
        max_impact_demand=2,
        max_axial_load_demand=4,
        max_shoulder_complex_demand=3,
        max_lumbar_load_demand=3,
        discouraged_families=("metabolic_dense",),
        excluded_families=(),
    ),
    # PRT-005: Advanced Hypertrophy 5-6x Push Pull Legs (research_only)
    "PRT-005": DemandCeiling(
        max_skill_demand=4,
        max_coordination_demand=4,
        max_ballistic_demand=2,
        max_impact_demand=2,
        max_axial_load_demand=4,
        max_shoulder_complex_demand=4,
        max_lumbar_load_demand=4,
        max_grip_demand=4,
        max_metabolic_demand=4,
        discouraged_families=(),
        excluded_families=(),
    ),
    # PRT-006: Clinical General 2-3x Full Body Conservative
    "PRT-006": DemandCeiling(
        max_skill_demand=1,
        max_coordination_demand=1,
        max_stability_demand=2,
        max_ballistic_demand=0,
        max_impact_demand=0,
        max_axial_load_demand=2,
        max_shoulder_complex_demand=2,
        max_lumbar_load_demand=2,
        max_grip_demand=2,
        max_metabolic_demand=2,
        discouraged_families=("high_axial_loading", "lumbar_bracing_heavy", "grip_limited"),
        excluded_families=(
            "high_skill_upper",
            "ballistic_lower",
            "shoulder_overhead_heavy",
            "metabolic_dense",
        ),
    ),
}


def get_protocol_ceiling(protocol_id: str) -> DemandCeiling | None:
    """Restituisce il ceiling per un protocollo, None se non mappato."""
    return PROTOCOL_CEILINGS.get(protocol_id)
