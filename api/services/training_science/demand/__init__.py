"""Demand layer SMART/KineScore — costo biomeccanico-funzionale degli esercizi."""

from .demand_policy import DemandPolicyResult, check_demand_ceiling
from .demand_registry import (
    DEMAND_REGISTRY_VERSION,
    get_default_demand_vector,
    get_protocol_ceiling,
)
from .demand_types import (
    DEMAND_VERSION,
    DemandCeiling,
    DemandFamily,
    DemandLevel,
    ExerciseDemandVector,
)

__all__ = [
    "DEMAND_REGISTRY_VERSION",
    "DEMAND_VERSION",
    "DemandCeiling",
    "DemandFamily",
    "DemandLevel",
    "DemandPolicyResult",
    "ExerciseDemandVector",
    "check_demand_ceiling",
    "get_default_demand_vector",
    "get_protocol_ceiling",
]
