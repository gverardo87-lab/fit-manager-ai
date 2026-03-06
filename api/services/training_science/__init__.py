"""
Training Science Engine — Motore scientifico per la programmazione dell'allenamento.

Architettura a 4 moduli indipendenti:
  types.py               — Enum e modelli Pydantic (vocabolario del dominio)
  principles.py          — Parametri di carico per obiettivo (NSCA/ACSM/Schoenfeld)
  muscle_contribution.py — Matrice contribuzione EMG pattern → muscoli
  volume_model.py        — MEV/MAV/MRV per muscolo × livello + volume effettivo
  balance_ratios.py      — Rapporti biomeccanici push:pull, quad:ham, ant:post

Ogni modulo ha UNA responsabilita', e' testabile in isolamento,
e i numeri hanno fonti bibliografiche nel docstring.

Uso tipico:
    from api.services.training_science import (
        Obiettivo, Livello, PatternMovimento,
        get_parametri, get_contribution, analyze_volume, analyze_balance,
    )
"""

from .types import (
    Obiettivo,
    Livello,
    GruppoMuscolare,
    PatternMovimento,
    TipoSplit,
    RuoloSessione,
    OrdinePriorita,
    ParametriCarico,
    VolumeTarget,
    SlotSessione,
    TemplateSessione,
    TemplatePiano,
    VolumeEffettivo,
    AnalisiVolume,
    AnalisiBalance,
    AnalisiPiano,
    RapportoBiomeccanico,
)
from .principles import (
    get_parametri,
    get_serie_per_slot,
    get_rep_range,
    get_riposo,
)
from .muscle_contribution import (
    get_contribution,
    get_muscle_contribution,
    get_primary_muscles,
    get_all_muscles,
    is_compound,
    compute_effective_sets,
    resolve_pattern,
)
from .volume_model import (
    get_volume_target,
    get_scaled_volume_target,
    get_all_volume_targets,
    classify_volume,
    analyze_volume,
)
from .balance_ratios import (
    analyze_balance,
    BALANCE_RATIOS,
)
from .split_logic import (
    get_split,
    get_session_roles,
    get_patterns_for_role,
    get_muscles_for_role,
    compute_frequency_per_muscle,
    identify_underhit_muscles,
)
from .session_order import (
    get_priority,
    order_patterns,
    validate_order,
)
from .plan_builder import (
    build_plan,
)
from .plan_analyzer import (
    analyze_plan,
)

__all__ = [
    # Types
    "Obiettivo",
    "Livello",
    "GruppoMuscolare",
    "PatternMovimento",
    "TipoSplit",
    "RuoloSessione",
    "OrdinePriorita",
    "ParametriCarico",
    "VolumeTarget",
    "SlotSessione",
    "TemplateSessione",
    "TemplatePiano",
    "VolumeEffettivo",
    "AnalisiVolume",
    "AnalisiBalance",
    "AnalisiPiano",
    "RapportoBiomeccanico",
    # Principles
    "get_parametri",
    "get_serie_per_slot",
    "get_rep_range",
    "get_riposo",
    # Muscle Contribution
    "get_contribution",
    "get_muscle_contribution",
    "get_primary_muscles",
    "get_all_muscles",
    "is_compound",
    "compute_effective_sets",
    "resolve_pattern",
    # Volume Model
    "get_volume_target",
    "get_scaled_volume_target",
    "get_all_volume_targets",
    "classify_volume",
    "analyze_volume",
    # Balance
    "analyze_balance",
    "BALANCE_RATIOS",
    # Split Logic
    "get_split",
    "get_session_roles",
    "get_patterns_for_role",
    "get_muscles_for_role",
    "compute_frequency_per_muscle",
    "identify_underhit_muscles",
    # Session Order
    "get_priority",
    "order_patterns",
    "validate_order",
    # Plan Builder
    "build_plan",
    # Plan Analyzer
    "analyze_plan",
]
