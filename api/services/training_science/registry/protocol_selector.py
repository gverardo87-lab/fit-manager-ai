"""Selettore puro e deterministico del protocollo SMART/KineScore."""

from api.schemas.training_science import TSScientificProfileResolved

from .protocol_registry import PROTOCOL_REGISTRY, PROTOCOL_REGISTRY_VERSION
from .protocol_types import ProtocolRecord, ProtocolSelectionResult

_STATUS_SCORE = {
    "supported": 3,
    "clinical_only": 2,
    "research_only": 1,
    "unsupported_by_policy": 0,
}


def _frequency_distance(protocol: ProtocolRecord, frequenza: int) -> int:
    if protocol.frequenza_min <= frequenza <= protocol.frequenza_max:
        return 0
    if frequenza < protocol.frequenza_min:
        return protocol.frequenza_min - frequenza
    return frequenza - protocol.frequenza_max


def _selection_key(
    protocol: ProtocolRecord,
    *,
    profile: TSScientificProfileResolved,
    frequenza: int,
) -> tuple[int, int, int, int, int, int, str]:
    return (
        1 if profile.mode in protocol.supported_modes else 0,
        1 if protocol.scientific_objective == profile.obiettivo_scientifico else 0,
        1 if protocol.scientific_level == profile.livello_scientifico else 0,
        1 if protocol.frequenza_min <= frequenza <= protocol.frequenza_max else 0,
        _STATUS_SCORE[protocol.status],
        -_frequency_distance(protocol, frequenza),
        protocol.protocol_id,
    )


def select_protocol(
    *,
    profile: TSScientificProfileResolved,
    frequenza: int,
) -> ProtocolSelectionResult:
    """Risolve il protocollo piu' vicino al contesto senza toccare il planner."""
    ranked = sorted(
        PROTOCOL_REGISTRY.values(),
        key=lambda protocol: _selection_key(protocol, profile=profile, frequenza=frequenza),
        reverse=True,
    )
    selected = ranked[0]
    exact_match = (
        profile.mode in selected.supported_modes
        and selected.scientific_objective == profile.obiettivo_scientifico
        and selected.scientific_level == profile.livello_scientifico
        and selected.frequenza_min <= frequenza <= selected.frequenza_max
    )

    selection_rationale: list[str] = []
    if exact_match:
        selection_rationale.append("Protocollo risolto con match esatto su mode, obiettivo, livello e frequenza.")
    else:
        selection_rationale.append("Protocollo risolto con fallback deterministico del registry.")
        if profile.mode not in selected.supported_modes:
            selection_rationale.append(
                f"Mode '{profile.mode}' fuori dal perimetro del protocollo scelto: uso adattamento read-only."
            )
        if selected.scientific_objective != profile.obiettivo_scientifico:
            selection_rationale.append("Nessun protocollo con obiettivo esatto: uso il protocollo piu' vicino dichiarato.")
        if selected.scientific_level != profile.livello_scientifico:
            selection_rationale.append("Nessun protocollo con livello esatto: uso il livello piu' vicino nel registry.")
        if not (selected.frequenza_min <= frequenza <= selected.frequenza_max):
            selection_rationale.append(
                f"Frequenza {frequenza}x fuori range del protocollo scelto "
                f"({selected.frequenza_min}-{selected.frequenza_max}x): planner legacy resta adattatore temporaneo."
            )

    selection_rationale.extend(selected.rationale)
    return ProtocolSelectionResult(
        protocol=selected,
        exact_match=exact_match,
        registry_version=PROTOCOL_REGISTRY_VERSION,
        selection_rationale=tuple(dict.fromkeys(selection_rationale)),
    )
