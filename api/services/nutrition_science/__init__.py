"""
Nutrition Science Engine — validazione piani alimentari vs LARN 2014 + CREA 2018.

Moduli:
  - types: dataclass e enum per profili, nutrienti, risultati
  - larn_tables: tabelle di riferimento SINU/LARN 2014 (AR/PRI/AI/UL)
  - larn_portions: porzioni standard LARN 2014 + gruppi alimentari + frequenze CREA 2018
  - plan_validator: validazione piano alimentare vs target LARN (score v2 3-assi)
  - frequency_validator: validazione frequenze settimanali vs CREA 2018
  - food_selector: selezione alimenti con rotazione proteica
  - meal_archetypes: archetipi pasto + pool alimentari
  - portion_optimizer: ottimizzazione porzioni (allineate LARN)
  - plan_generator: orchestratore pipeline completa
"""

from api.services.nutrition_science.plan_validator import validate_plan  # noqa: F401
from api.services.nutrition_science.frequency_validator import validate_frequencies  # noqa: F401
from api.services.nutrition_science.types import (  # noqa: F401
    ClientProfile,
    LarnLevel,
    NutrientAssessment,
    PlanValidationResult,
)
