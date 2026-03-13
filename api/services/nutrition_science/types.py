"""
Tipi per il Nutrition Science Engine.

Profilo cliente, livelli LARN, risultati validazione.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Sex(str, Enum):
    M = "M"
    F = "F"


class LarnLevel(str, Enum):
    """Livelli di riferimento LARN 2014 (SINU)."""
    AR = "AR"    # Average Requirement (fabbisogno medio)
    PRI = "PRI"  # Population Reference Intake (assunzione raccomandata)
    AI = "AI"    # Adequate Intake (assunzione adeguata)
    UL = "UL"    # Tolerable Upper Intake Level (livello max tollerabile)


class ComplianceStatus(str, Enum):
    """Stato compliance di un nutriente."""
    OTTIMALE = "ottimale"          # entro PRI/AI e sotto UL
    SUFFICIENTE = "sufficiente"    # sopra AR ma sotto PRI
    CARENTE = "carente"            # sotto AR
    ECCESSO = "eccesso"            # sopra UL
    NON_VALUTABILE = "non_valutabile"  # dati insufficienti


@dataclass
class ClientProfile:
    """Profilo del cliente per la valutazione LARN."""
    eta: int           # anni
    sesso: Sex
    peso_kg: Optional[float] = None
    altezza_cm: Optional[float] = None
    gravidanza: bool = False
    allattamento: bool = False


@dataclass
class NutrientReference:
    """Valori di riferimento LARN per un singolo nutriente."""
    nutriente: str
    unita: str
    ar: Optional[float] = None    # Average Requirement
    pri: Optional[float] = None   # Population Reference Intake
    ai: Optional[float] = None    # Adequate Intake
    ul: Optional[float] = None    # Upper Level
    fonte: str = "LARN 2014"


@dataclass
class NutrientAssessment:
    """Valutazione di un singolo nutriente vs LARN."""
    nutriente: str
    unita: str
    apporto_die: Optional[float]     # quanto il piano fornisce /die
    riferimento: NutrientReference
    status: ComplianceStatus
    percentuale_pri: Optional[float] = None  # apporto / PRI × 100
    nota: Optional[str] = None


@dataclass
class MacroDistribution:
    """Distribuzione macro in % delle calorie totali."""
    proteine_pct: float
    carboidrati_pct: float
    grassi_pct: float
    # LARN range raccomandati
    proteine_range: tuple[float, float] = (12.0, 20.0)   # % kcal
    carboidrati_range: tuple[float, float] = (45.0, 60.0)
    grassi_range: tuple[float, float] = (20.0, 35.0)


@dataclass
class PlanValidationResult:
    """Risultato completo della validazione LARN di un piano."""
    profilo: ClientProfile
    kcal_die: float
    macro: MacroDistribution
    nutrienti: list[NutrientAssessment] = field(default_factory=list)
    score: int = 0              # 0-100 compliance complessiva
    warnings: list[str] = field(default_factory=list)
    note_metodologiche: str = ""
