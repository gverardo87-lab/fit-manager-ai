"""
Nutrition Science Engine — validazione piani alimentari vs LARN 2014.

Moduli:
  - types: dataclass e enum per profili, nutrienti, risultati
  - larn_tables: tabelle di riferimento SINU/LARN 2014 (AR/PRI/AI/UL)
  - plan_validator: validazione piano alimentare vs target LARN
"""

from api.services.nutrition_science.plan_validator import validate_plan  # noqa: F401
from api.services.nutrition_science.types import (  # noqa: F401
    ClientProfile,
    LarnLevel,
    NutrientAssessment,
    PlanValidationResult,
)
