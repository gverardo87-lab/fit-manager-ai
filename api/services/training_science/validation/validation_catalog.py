"""Validation Catalog v1 — benchmark cases, client fixtures, request fixtures.

Definisce i 6 casi benchmark (VM-001..VM-006) della Validation Matrix v1.
Ogni caso specifica:
- quale protocollo viene testato (PRT-001..006)
- quale client fixture usa (CFG-A..E)
- quale request fixture usa (RFX-001..006)
- invariant, snapshot e tolerance checks attesi
- warning policy (required, allowed, forbidden)
- score band minimo

Fonte spec: UPG-2026-03-07-60 (SMART Validation Matrix v1).
"""

from dataclasses import dataclass, field
from typing import Literal

from api.services.training_science.types import Livello, Obiettivo

VALIDATION_CATALOG_VERSION = "smart-validation-catalog-v1"

# ──────────────────────────────────────────────────────────────────────
# 1. Client Fixture — profili cliente tipizzati (CFG-A..E)
# ──────────────────────────────────────────────────────────────────────

ClientFixtureId = Literal["CFG-A", "CFG-B", "CFG-C", "CFG-D", "CFG-E"]


@dataclass(frozen=True)
class ClientFixture:
    """Profilo cliente tipizzato per benchmark."""

    fixture_id: ClientFixtureId
    label: str
    livello: Livello
    obiettivo: Obiettivo
    has_structured_anamnesis: bool
    clinical_flags: tuple[str, ...] = ()
    description: str = ""


CLIENT_FIXTURES: dict[str, ClientFixture] = {
    "CFG-A": ClientFixture(
        fixture_id="CFG-A",
        label="Minimal beginner",
        livello=Livello.PRINCIPIANTE,
        obiettivo=Obiettivo.TONIFICAZIONE,
        has_structured_anamnesis=False,
        description="Anamnesi legacy, dati parziali, nessuna specializzazione.",
    ),
    "CFG-B": ClientFixture(
        fixture_id="CFG-B",
        label="Beginner clinical low-skill",
        livello=Livello.PRINCIPIANTE,
        obiettivo=Obiettivo.TONIFICAZIONE,
        has_structured_anamnesis=True,
        clinical_flags=("shoulder_sensitivity", "lumbar_sensitivity"),
        description="Anamnesi strutturata, sensibilita' spalla/lombare, candidabile PRT-006.",
    ),
    "CFG-C": ClientFixture(
        fixture_id="CFG-C",
        label="Intermediate general",
        livello=Livello.INTERMEDIO,
        obiettivo=Obiettivo.IPERTROFIA,
        has_structured_anamnesis=True,
        description="Dati sufficienti, buona tolleranza carico, nessun vincolo clinical.",
    ),
    "CFG-D": ClientFixture(
        fixture_id="CFG-D",
        label="Intermediate performance",
        livello=Livello.INTERMEDIO,
        obiettivo=Obiettivo.FORZA,
        has_structured_anamnesis=True,
        description="Forza relativa, obiettivo esplicito performance, readiness adeguata.",
    ),
    "CFG-E": ClientFixture(
        fixture_id="CFG-E",
        label="Advanced hypertrophy",
        livello=Livello.AVANZATO,
        obiettivo=Obiettivo.IPERTROFIA,
        has_structured_anamnesis=True,
        description="Alta tolleranza volume, contesto performance, nessun gate beginner.",
    ),
}


# ──────────────────────────────────────────────────────────────────────
# 2. Request Fixture — envelope di richiesta (RFX-001..006)
# ──────────────────────────────────────────────────────────────────────

RequestFixtureId = Literal["RFX-001", "RFX-002", "RFX-003", "RFX-004", "RFX-005", "RFX-006"]


@dataclass(frozen=True)
class RequestFixture:
    """Envelope di richiesta per benchmark."""

    fixture_id: RequestFixtureId
    frequenza: int
    obiettivo: Obiettivo
    livello: Livello
    mode: Literal["general", "performance", "clinical"]
    description: str = ""


REQUEST_FIXTURES: dict[str, RequestFixture] = {
    "RFX-001": RequestFixture(
        fixture_id="RFX-001",
        frequenza=3,
        obiettivo=Obiettivo.TONIFICAZIONE,
        livello=Livello.PRINCIPIANTE,
        mode="general",
        description="Beginner general 3x full body tonificazione.",
    ),
    "RFX-002": RequestFixture(
        fixture_id="RFX-002",
        frequenza=3,
        obiettivo=Obiettivo.TONIFICAZIONE,
        livello=Livello.INTERMEDIO,
        mode="general",
        description="Intermediate general 3x full body tonificazione.",
    ),
    "RFX-003": RequestFixture(
        fixture_id="RFX-003",
        frequenza=4,
        obiettivo=Obiettivo.IPERTROFIA,
        livello=Livello.INTERMEDIO,
        mode="general",
        description="Intermediate ipertrofia 4x upper/lower.",
    ),
    "RFX-004": RequestFixture(
        fixture_id="RFX-004",
        frequenza=4,
        obiettivo=Obiettivo.FORZA,
        livello=Livello.INTERMEDIO,
        mode="performance",
        description="Intermediate forza 4x upper/lower.",
    ),
    "RFX-005": RequestFixture(
        fixture_id="RFX-005",
        frequenza=5,
        obiettivo=Obiettivo.IPERTROFIA,
        livello=Livello.AVANZATO,
        mode="performance",
        description="Advanced ipertrofia 5x push/pull/legs.",
    ),
    "RFX-006": RequestFixture(
        fixture_id="RFX-006",
        frequenza=3,
        obiettivo=Obiettivo.TONIFICAZIONE,
        livello=Livello.PRINCIPIANTE,
        mode="clinical",
        description="Beginner clinical 3x full body conservative.",
    ),
}


# ──────────────────────────────────────────────────────────────────────
# 3. Validation Case — 6 benchmark (VM-001..006)
# ──────────────────────────────────────────────────────────────────────

FailureClass = Literal[
    "protocol_selection_regression",
    "constraint_violation",
    "draft_suitability_regression",
    "analysis_regression",
    "clinical_overlay_regression",
    "score_regression",
]


@dataclass(frozen=True)
class ScoreBand:
    """Banda di score accettabile per un benchmark."""

    minimum: int
    description: str = ""


@dataclass(frozen=True)
class WarningPolicy:
    """Policy sui warning attesi per un benchmark."""

    required: tuple[str, ...] = ()
    allowed: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationCase:
    """Singolo caso benchmark della Validation Matrix v1."""

    case_id: str
    protocol_id: str
    registry_id: str
    client_fixture_id: ClientFixtureId
    request_fixture_id: RequestFixtureId
    expected_split_family: str
    invariant_checks: tuple[str, ...] = ()
    snapshot_checks: tuple[str, ...] = ()
    tolerance_checks: tuple[str, ...] = ()
    warning_policy: WarningPolicy = field(default_factory=WarningPolicy)
    score_band: ScoreBand = field(default_factory=lambda: ScoreBand(minimum=70))
    focus: tuple[str, ...] = ()
    notes: str = ""


# ──────────────────────────────────────────────────────────────────────
# 4. Validation Matrix v1 — i 6 casi
# ──────────────────────────────────────────────────────────────────────

VALIDATION_MATRIX: dict[str, ValidationCase] = {
    "VM-001": ValidationCase(
        case_id="VM-001",
        protocol_id="PRT-001",
        registry_id="beginner_general_3x_tonificazione_full_body_v1",
        client_fixture_id="CFG-A",
        request_fixture_id="RFX-001",
        expected_split_family="full_body",
        invariant_checks=(
            "protocol_selection_correct",
            "split_family_correct",
            "no_advanced_draft_exercise",
            "no_ceiling_exceeded",
            "no_hard_constraint_fail",
        ),
        snapshot_checks=(
            "session_count_matches_frequenza",
            "session_roles_full_body",
        ),
        tolerance_checks=(
            "score_above_band",
            "volume_in_low_mav",
        ),
        warning_policy=WarningPolicy(
            forbidden=(
                "advanced_draft_exercise",
                "ballistic_beginner_draft",
                "extreme_push_pull_imbalance",
            ),
        ),
        score_band=ScoreBand(minimum=70, description="Beginner general 3x"),
        focus=(
            "Selezione protocollo base beginner 3x.",
            "Assenza di esercizi advanced.",
            "Volume in low_mav.",
            "Nessun ballistic/impact fuori policy.",
        ),
    ),
    "VM-002": ValidationCase(
        case_id="VM-002",
        protocol_id="PRT-002",
        registry_id="beginner_general_3x_tonificazione_full_body_v1",
        client_fixture_id="CFG-A",
        request_fixture_id="RFX-002",
        expected_split_family="full_body",
        invariant_checks=(
            "protocol_selection_correct",
            "split_family_correct",
            "no_advanced_draft_exercise",
            "no_ceiling_exceeded",
            "no_hard_constraint_fail",
        ),
        snapshot_checks=(
            "session_count_matches_frequenza",
            "session_roles_full_body",
            "pattern_exposure_balanced",
        ),
        tolerance_checks=(
            "score_above_band",
            "recovery_overlap_below_threshold",
        ),
        warning_policy=WarningPolicy(
            allowed=(
                "quad_ham_low",
                "recovery_overlap_posterior",
            ),
            forbidden=(
                "advanced_draft_exercise",
                "extreme_push_pull_imbalance",
                "ballistic_beginner_draft",
            ),
        ),
        score_band=ScoreBand(minimum=72, description="Intermediate general 3x"),
        focus=(
            "Rotazione full_body ABC.",
            "Controllo frequenza piccoli distretti.",
            "No muscle-up, no box jump nel draft.",
            "Recovery overlap sotto soglia.",
        ),
    ),
    "VM-003": ValidationCase(
        case_id="VM-003",
        protocol_id="PRT-003",
        registry_id="intermediate_general_4x_ipertrofia_upper_lower_v1",
        client_fixture_id="CFG-C",
        request_fixture_id="RFX-003",
        expected_split_family="upper_lower",
        invariant_checks=(
            "protocol_selection_correct",
            "split_family_correct",
            "no_ceiling_exceeded",
            "no_hard_constraint_fail",
        ),
        snapshot_checks=(
            "session_count_matches_frequenza",
            "session_roles_upper_lower",
            "pattern_exposure_balanced",
        ),
        tolerance_checks=(
            "score_above_band",
            "push_pull_ratio_in_band",
            "volume_in_mid_high_mav",
        ),
        warning_policy=WarningPolicy(
            allowed=(
                "quad_ham_low",
                "recovery_overlap_posterior",
            ),
            forbidden=(
                "extreme_push_pull_imbalance",
            ),
        ),
        score_band=ScoreBand(minimum=78, description="Intermediate ipertrofia 4x"),
        focus=(
            "Split upper_lower.",
            "Volume mid/high MAV.",
            "Ratio push/pull dentro banda.",
            "Suitability non beginner-gated.",
        ),
    ),
    "VM-004": ValidationCase(
        case_id="VM-004",
        protocol_id="PRT-004",
        registry_id="intermediate_performance_3x_forza_full_body_v1",
        client_fixture_id="CFG-D",
        request_fixture_id="RFX-004",
        expected_split_family="upper_lower",
        invariant_checks=(
            "protocol_selection_correct",
            "split_family_correct",
            "no_ceiling_exceeded",
            "no_hard_constraint_fail",
        ),
        snapshot_checks=(
            "session_count_matches_frequenza",
            "compound_priority_high",
        ),
        tolerance_checks=(
            "score_above_band",
            "strength_bias_present",
        ),
        warning_policy=WarningPolicy(
            allowed=(
                "recovery_overlap_posterior",
            ),
            forbidden=(
                "advanced_draft_exercise",
                "extreme_push_pull_imbalance",
            ),
        ),
        score_band=ScoreBand(minimum=78, description="Intermediate forza 4x"),
        focus=(
            "Strength bias reale.",
            "Compound priority.",
            "Intensita' tecnico-neuromuscolare alta.",
            "Demand ceilings performance ma non advanced.",
        ),
    ),
    "VM-005": ValidationCase(
        case_id="VM-005",
        protocol_id="PRT-005",
        registry_id="advanced_performance_5x_ipertrofia_upper_lower_plus_v1",
        client_fixture_id="CFG-E",
        request_fixture_id="RFX-005",
        expected_split_family="push_pull_legs",
        invariant_checks=(
            "protocol_selection_correct",
            "split_family_correct",
            "no_ceiling_exceeded",
            "no_hard_constraint_fail",
        ),
        snapshot_checks=(
            "session_count_matches_frequenza",
            "advanced_suitability_allowed",
        ),
        tolerance_checks=(
            "score_above_band",
            "volume_high_controlled",
        ),
        warning_policy=WarningPolicy(
            allowed=(
                "recovery_overlap_posterior",
                "quad_ham_low",
            ),
        ),
        score_band=ScoreBand(minimum=80, description="Advanced ipertrofia 5x"),
        focus=(
            "Volume alto controllato.",
            "Densita' avanzata.",
            "Suitability advanced ammessa.",
            "Recovery budgets piu' permissivi.",
        ),
        notes="Protocollo research_only — benchmark stabilisce baseline futura.",
    ),
    "VM-006": ValidationCase(
        case_id="VM-006",
        protocol_id="PRT-006",
        registry_id="beginner_clinical_3x_tonificazione_full_body_low_skill_v1",
        client_fixture_id="CFG-B",
        request_fixture_id="RFX-006",
        expected_split_family="full_body",
        invariant_checks=(
            "protocol_selection_correct",
            "split_family_correct",
            "no_advanced_draft_exercise",
            "no_ceiling_exceeded",
            "no_hard_constraint_fail",
            "no_ballistic_impact_draft",
            "demand_shoulder_lumbar_contained",
        ),
        snapshot_checks=(
            "session_count_matches_frequenza",
            "session_roles_full_body",
            "clinical_overlay_dominant",
        ),
        tolerance_checks=(
            "score_above_band",
            "volume_conservative",
        ),
        warning_policy=WarningPolicy(
            required=(
                "clinical_mode_active",
            ),
            forbidden=(
                "advanced_draft_exercise",
                "ballistic_beginner_draft",
                "extreme_push_pull_imbalance",
            ),
        ),
        score_band=ScoreBand(minimum=75, description="Beginner clinical 3x"),
        focus=(
            "Low-skill hard gating.",
            "Low-impact / low-ballistic.",
            "Clinical overlay dominante.",
            "Costo scapolo-omerale/lombare contenuto.",
        ),
    ),
}


def get_validation_case(case_id: str) -> ValidationCase | None:
    """Restituisce un caso benchmark, None se non trovato."""
    return VALIDATION_MATRIX.get(case_id)


def get_client_fixture(fixture_id: str) -> ClientFixture | None:
    """Restituisce un client fixture, None se non trovato."""
    return CLIENT_FIXTURES.get(fixture_id)


def get_request_fixture(fixture_id: str) -> RequestFixture | None:
    """Restituisce un request fixture, None se non trovato."""
    return REQUEST_FIXTURES.get(fixture_id)
