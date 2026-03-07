"""Tipi read-only minimi del registry evidenze SMART/KineScore."""

from dataclasses import dataclass

EVIDENCE_REGISTRY_VERSION = "smart-evidence-v1"


@dataclass(frozen=True)
class EvidenceReference:
    """Riferimento minimale a claim/usage nel registry evidenze."""

    usage_id: str
    claim_id: str
    parameter_ids: tuple[str, ...] = ()
