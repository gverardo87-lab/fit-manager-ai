"""Validation Metadata — tracciabilita' completa del plan-package.

Raccoglie le versioni di ogni sottosistema che ha contribuito all'output,
i riferimenti ai benchmark case applicabili e il timestamp di generazione.

Questo modulo rende ogni plan-package auditabile: dato un output,
e' possibile ricostruire esattamente quali regole, registri e motori
lo hanno prodotto.
"""

from datetime import datetime, timezone
from dataclasses import dataclass

from api.services.training_science.constraints.constraint_engine import CONSTRAINT_ENGINE_VERSION
from api.services.training_science.registry.evidence_types import EVIDENCE_REGISTRY_VERSION
from api.services.training_science.registry.protocol_registry import PROTOCOL_REGISTRY_VERSION
from .feasibility_engine import FEASIBILITY_ENGINE_VERSION

VALIDATION_METADATA_VERSION = "smart-validation-meta-v1"


@dataclass(frozen=True)
class ValidationMetadata:
    """Envelope di tracciabilita' per un singolo plan-package."""

    protocol_id: str
    protocol_registry_version: str
    constraint_profile_id: str
    constraint_engine_version: str
    evidence_registry_version: str
    feasibility_engine_version: str
    validation_case_refs: tuple[str, ...] = ()
    generated_at: str = ""

    @staticmethod
    def build(
        *,
        protocol_id: str,
        constraint_profile_id: str,
        validation_case_ids: tuple[str, ...] | list[str] = (),
    ) -> "ValidationMetadata":
        """Costruisce i metadata con le versioni correnti di tutti i sottosistemi."""
        return ValidationMetadata(
            protocol_id=protocol_id,
            protocol_registry_version=PROTOCOL_REGISTRY_VERSION,
            constraint_profile_id=constraint_profile_id,
            constraint_engine_version=CONSTRAINT_ENGINE_VERSION,
            evidence_registry_version=EVIDENCE_REGISTRY_VERSION,
            feasibility_engine_version=FEASIBILITY_ENGINE_VERSION,
            validation_case_refs=tuple(validation_case_ids),
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
