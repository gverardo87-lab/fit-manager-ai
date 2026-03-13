"""
Pydantic schemas — modulo nutrizione.

Schemi separati per:
  - Catalogo alimenti (nutrition.db): FoodCategory, Food, StandardPortion
  - Piani alimentari (crm.db): NutritionPlan, PlanMeal, MealComponent

Convenzioni:
  - Create/Update: mai trainer_id (iniettato dal JWT), mai id
  - Response: sempre model_config con from_attributes=True
  - extra="forbid" su tutti i Create (Mass Assignment Prevention)
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, model_validator


# ---------------------------------------------------------------------------
# Catalogo alimenti (nutrition.db) — read-only via API
# ---------------------------------------------------------------------------


class FoodCategoryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nome: str
    nome_en: str
    icona: Optional[str] = None


class FoodResponse(BaseModel):
    """Alimento con macro per 100g. Esposto via GET /nutrition/foods."""
    model_config = {"from_attributes": True}

    id: int
    nome: str
    nome_en: Optional[str] = None
    categoria_id: int
    categoria_nome: Optional[str] = None   # join-enriched nel router

    # Macro per 100g — obbligatori
    energia_kcal: float
    proteine_g: float
    carboidrati_g: float
    grassi_g: float

    # Macro per 100g — opzionali
    di_cui_zuccheri_g: Optional[float] = None
    di_cui_saturi_g: Optional[float] = None
    fibra_g: Optional[float] = None
    sodio_mg: Optional[float] = None
    acqua_g: Optional[float] = None
    colesterolo_mg: Optional[float] = None

    note: Optional[str] = None
    source: str
    is_active: bool


class FoodDetailResponse(FoodResponse):
    """Alimento + porzioni standard."""
    porzioni: list["StandardPortionResponse"] = []


class StandardPortionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    alimento_id: int
    nome: str
    grammi: float


class FoodMacroCalc(BaseModel):
    """Macro calcolati per una quantita' specifica (usato internamente)."""
    alimento_id: int
    nome: str
    quantita_g: float
    energia_kcal: float
    proteine_g: float
    carboidrati_g: float
    grassi_g: float
    fibra_g: Optional[float] = None


# ---------------------------------------------------------------------------
# Piani alimentari (crm.db) — trainer-owned
# ---------------------------------------------------------------------------


class NutritionPlanCreate(BaseModel):
    model_config = {"extra": "forbid"}

    id_cliente: int
    nome: str
    obiettivo_calorico: Optional[int] = None
    proteine_g_target: Optional[int] = None
    carboidrati_g_target: Optional[int] = None
    grassi_g_target: Optional[int] = None
    note_cliniche: Optional[str] = None
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    attivo: bool = True


class NutritionPlanUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    nome: Optional[str] = None
    obiettivo_calorico: Optional[int] = None
    proteine_g_target: Optional[int] = None
    carboidrati_g_target: Optional[int] = None
    grassi_g_target: Optional[int] = None
    note_cliniche: Optional[str] = None
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    attivo: Optional[bool] = None


class NutritionPlanResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    trainer_id: int
    id_cliente: int
    nome: str
    obiettivo_calorico: Optional[int] = None
    proteine_g_target: Optional[int] = None
    carboidrati_g_target: Optional[int] = None
    grassi_g_target: Optional[int] = None
    note_cliniche: Optional[str] = None
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    attivo: bool
    created_at: datetime
    # Arricchito con dati cliente (solo nell'endpoint cross-client)
    client_nome: Optional[str] = None
    client_cognome: Optional[str] = None
    # Conteggio pasti (opzionale, arricchito nella lista)
    num_pasti: Optional[int] = None


class NutritionPlanDetail(NutritionPlanResponse):
    """Piano con pasti e componenti (risposta GET /plans/{id})."""
    pasti: list["PlanMealDetail"] = []
    # Totali calcolati su tutti i pasti (media giornaliera se piano settimanale)
    totale_kcal: Optional[float] = None
    totale_proteine_g: Optional[float] = None
    totale_carboidrati_g: Optional[float] = None
    totale_grassi_g: Optional[float] = None


# ---------------------------------------------------------------------------
# Pasti piano
# ---------------------------------------------------------------------------


TIPO_PASTO_LABELS = {
    "COLAZIONE": "Colazione",
    "SPUNTINO_MATTINA": "Spuntino mattina",
    "PRANZO": "Pranzo",
    "SPUNTINO_POMERIGGIO": "Spuntino pomeriggio",
    "CENA": "Cena",
    "PRE_WORKOUT": "Pre-workout",
    "POST_WORKOUT": "Post-workout",
}

GIORNO_LABELS = {
    0: "Ogni giorno",
    1: "Lunedì",
    2: "Martedì",
    3: "Mercoledì",
    4: "Giovedì",
    5: "Venerdì",
    6: "Sabato",
    7: "Domenica",
}


class PlanMealCreate(BaseModel):
    model_config = {"extra": "forbid"}

    giorno_settimana: int = 0   # 0-7
    tipo_pasto: str             # COLAZIONE | PRANZO | ecc.
    ordine: int = 0
    nome: Optional[str] = None
    note: Optional[str] = None

    @model_validator(mode="after")
    def validate_giorno(self) -> "PlanMealCreate":
        if self.giorno_settimana not in range(8):
            raise ValueError("giorno_settimana deve essere 0-7 (0=ogni giorno)")
        valid_tipi = set(TIPO_PASTO_LABELS.keys())
        if self.tipo_pasto not in valid_tipi:
            raise ValueError(f"tipo_pasto non valido. Valori: {sorted(valid_tipi)}")
        return self


class PlanMealUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    giorno_settimana: Optional[int] = None
    tipo_pasto: Optional[str] = None
    ordine: Optional[int] = None
    nome: Optional[str] = None
    note: Optional[str] = None


class PlanMealResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    piano_id: int
    giorno_settimana: int
    giorno_label: Optional[str] = None    # enriched
    tipo_pasto: str
    tipo_pasto_label: Optional[str] = None  # enriched
    ordine: int
    nome: Optional[str] = None
    note: Optional[str] = None


class PlanMealDetail(PlanMealResponse):
    """Pasto con componenti e totale macro."""
    componenti: list["MealComponentDetail"] = []
    totale_kcal: float = 0.0
    totale_proteine_g: float = 0.0
    totale_carboidrati_g: float = 0.0
    totale_grassi_g: float = 0.0


# ---------------------------------------------------------------------------
# Componenti pasto
# ---------------------------------------------------------------------------


class MealComponentCreate(BaseModel):
    model_config = {"extra": "forbid"}

    alimento_id: int
    quantita_g: float
    note: Optional[str] = None


class MealComponentUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    quantita_g: Optional[float] = None
    note: Optional[str] = None


class MealComponentDetail(BaseModel):
    """Componente arricchito con dati alimento (join cross-DB)."""
    model_config = {"from_attributes": True}

    id: int
    pasto_id: int
    alimento_id: int
    alimento_nome: Optional[str] = None       # da nutrition.db
    alimento_categoria: Optional[str] = None  # da nutrition.db
    quantita_g: float
    note: Optional[str] = None

    # Macro calcolati per la quantita' specificata (non per 100g)
    energia_kcal: float = 0.0
    proteine_g: float = 0.0
    carboidrati_g: float = 0.0
    grassi_g: float = 0.0
    fibra_g: Optional[float] = None


# ---------------------------------------------------------------------------
# Nutrition summary (profilo cliente)
# ---------------------------------------------------------------------------


class NutritionSummary(BaseModel):
    """
    Snapshot nutrizionale del cliente per il tab Nutrizione nel profilo.

    Esposto via GET /clients/{id}/nutrition/summary.
    """
    ha_piano_attivo: bool
    piano_attivo: Optional[NutritionPlanResponse] = None
    totale_piani: int = 0

    # Macro del piano attivo (media giornaliera)
    media_kcal_die: Optional[float] = None
    media_proteine_g_die: Optional[float] = None
    media_carboidrati_g_die: Optional[float] = None
    media_grassi_g_die: Optional[float] = None

    # Confronto target vs reale
    obiettivo_calorico: Optional[int] = None
    delta_kcal: Optional[float] = None   # reale - target (negativo = deficit)


class CopyDayInput(BaseModel):
    """Input per copiare tutti i pasti di un giorno su un altro."""
    source_giorno: int   # 0-7
    target_giorno: int   # 0-7


class CopyDayResult(BaseModel):
    pasti_copiati: int
    componenti_copiati: int


# ---------------------------------------------------------------------------
# Template pasti
# ---------------------------------------------------------------------------


class MealTemplateCreate(BaseModel):
    model_config = {"extra": "forbid"}

    nome: str
    tipo_pasto: Optional[str] = None


class SaveAsTemplateInput(BaseModel):
    model_config = {"extra": "forbid"}

    nome: str                  # nome del nuovo template
    tipo_pasto: Optional[str] = None


class ApplyTemplateResult(BaseModel):
    componenti_aggiunti: int


class TemplateComponentDetail(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    template_id: int
    alimento_id: int
    alimento_nome: Optional[str] = None
    quantita_g: float
    note: Optional[str] = None
    energia_kcal: float = 0.0
    proteine_g: float = 0.0
    carboidrati_g: float = 0.0
    grassi_g: float = 0.0
    fibra_g: Optional[float] = None


class MealTemplateDetail(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    trainer_id: int
    nome: str
    tipo_pasto: Optional[str] = None
    created_at: datetime
    componenti: list[TemplateComponentDetail] = []
    totale_kcal: float = 0.0
    totale_proteine_g: float = 0.0
    totale_carboidrati_g: float = 0.0
    totale_grassi_g: float = 0.0


# ---------------------------------------------------------------------------
# Piano template statici
# ---------------------------------------------------------------------------


class PlanTemplateItem(BaseModel):
    id: str
    nome: str
    descrizione: str
    tags: list[str]
    obiettivo_calorico: int
    proteine_g_target: int
    carboidrati_g_target: int
    grassi_g_target: int
    note_cliniche: str


class CreateFromTemplateInput(BaseModel):
    model_config = {"extra": "forbid"}

    template_id: str
    id_cliente: int
    nome: str
    data_inizio: Optional[date] = None
    attivo: bool = True
