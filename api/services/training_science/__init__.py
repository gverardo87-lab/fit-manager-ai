"""
Training Science Engine — Motore scientifico per la programmazione dell'allenamento.

Architettura a 10 moduli indipendenti (Phase 1 + Phase 2 + Phase 3):

  Phase 1 — Fondamenta scientifiche:
    types.py               — Enum e modelli Pydantic (vocabolario del dominio)
    principles.py          — Parametri di carico per obiettivo (NSCA/ACSM/Schoenfeld)
    muscle_contribution.py — Matrice contribuzione EMG + volume ipertrofico pesato
    volume_model.py        — MEV/MAV/MRV per muscolo x livello + classificazione
    balance_ratios.py      — Rapporti biomeccanici push:pull, quad:ham, ant:post

  Phase 2 — Generazione piani:
    split_logic.py         — Frequenza -> split ottimale + struttura sessioni
    session_order.py       — Ordinamento fisiologico (SNC-demanding first)
    plan_builder.py        — Generatore volume-driven a 4 fasi con feedback loop
    plan_analyzer.py       — Analisi 4D (volume, balance, frequenza, recupero)

  Phase 3 — Periodizzazione:
    periodization.py       — Mesociclo (progressione volume + deload)

Ogni modulo ha UNA responsabilita', e' testabile in isolamento,
e i numeri hanno fonti bibliografiche nel docstring.

Uso tipico:
    from api.services.training_science import (
        Obiettivo, Livello, PatternMovimento,
        build_plan, analyze_plan, build_mesocycle,
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
    AnalisiTonnellaggio,
    TonnellaggioSlotAnalisi,
    RapportoBiomeccanico,
    ContributoEsercizio,
    DettaglioMuscolo,
    DettaglioRapporto,
    DettaglioRecovery,
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
    compute_hypertrophy_sets,
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
    clamp_frequenza,
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
from .periodization import (
    build_mesocycle,
    get_mesocycle_duration,
    get_weekly_config,
    Mesociclo,
    SettimanaConfig,
)
from .load_model import (
    IntensityPrescription,
    compute_tonnage,
    get_intensity_for_reps,
    get_intensity_prescription,
    classify_intensity_zone,
    rpe_to_rir,
    rir_to_rpe,
)

__all__ = [
    # Types (core)
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
    "ContributoEsercizio",
    "DettaglioMuscolo",
    "DettaglioRapporto",
    "DettaglioRecovery",
    # Types (volume-load)
    "AnalisiTonnellaggio",
    "TonnellaggioSlotAnalisi",
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
    "compute_hypertrophy_sets",
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
    "clamp_frequenza",
    # Session Order
    "get_priority",
    "order_patterns",
    "validate_order",
    # Plan Builder
    "build_plan",
    # Plan Analyzer
    "analyze_plan",
    # Periodization
    "build_mesocycle",
    "get_mesocycle_duration",
    "get_weekly_config",
    "Mesociclo",
    "SettimanaConfig",
    # Load Model
    "IntensityPrescription",
    "compute_tonnage",
    "get_intensity_for_reps",
    "get_intensity_prescription",
    "classify_intensity_zone",
    "rpe_to_rir",
    "rir_to_rpe",
]
