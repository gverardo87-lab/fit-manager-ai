"""Tipi read-only del protocol registry SMART/KineScore."""

from dataclasses import dataclass
from typing import Literal

from api.services.training_science.types import Livello, Obiettivo

ProtocolStatus = Literal[
    "supported",
    "clinical_only",
    "research_only",
    "unsupported_by_policy",
]
ProtocolMode = Literal["general", "performance", "clinical"]
SplitFamily = Literal["full_body", "upper_lower", "push_pull_legs", "hybrid"]


@dataclass(frozen=True)
class ProtocolRecord:
    """Protocollo dichiarato nel registry, senza logica runtime."""

    protocol_id: str
    label: str
    status: ProtocolStatus
    supported_modes: tuple[ProtocolMode, ...]
    scientific_objective: Obiettivo
    scientific_level: Livello
    frequenza_min: int
    frequenza_max: int
    split_family: SplitFamily
    constraint_profile_id: str
    validation_case_ids: tuple[str, ...] = ()
    evidence_usage_ids: tuple[str, ...] = ()
    rationale: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProtocolSelectionResult:
    """Esito deterministico della selezione protocollo."""

    protocol: ProtocolRecord
    exact_match: bool
    registry_version: str
    selection_rationale: tuple[str, ...]
