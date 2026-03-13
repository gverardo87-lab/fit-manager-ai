"""
Modello nutrizione — catalogo alimenti (nutrition.db) + piani alimentari (crm.db).

Architettura dual-DB (estende il pattern catalog.db):
  - nutrition.db: FoodCategory, Food, StandardPortion
    Catalogo globale senza trainer_id — dati CREA 2019 + USDA + custom.
  - crm.db: NutritionPlan, PlanMeal, MealComponent
    Trainer-owned, Bouncer Pattern + Deep IDOR.

Cross-DB reference: MealComponent.alimento_id → Food.id in nutrition.db.
Nessun FK constraint DB-level (stesso pattern di esercizi_muscoli.id_esercizio).
Integrità gestita a livello applicativo nel router.

Valori macro su alimenti: sempre riferiti a 100g di prodotto.
"""

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


# ---------------------------------------------------------------------------
# nutrition.db — catalogo globale, no trainer_id
# ---------------------------------------------------------------------------


class FoodType(str, Enum):
    """Tipo di alimento nel catalogo.

    - ingrediente: singolo alimento (uovo, pollo, riso)
    - pietanza: piatto composto con ricetta (frittata, pasta al pomodoro)
    - bevanda: bevande (latte, succo, integratore)
    """
    INGREDIENTE = "ingrediente"
    PIETANZA = "pietanza"
    BEVANDA = "bevanda"


class FoodCategory(SQLModel, table=True):
    """
    Categorie alimentari (CREA 2019: 20 categorie).

    Esempio: "Cereali e derivati" / "Cereals and derivatives"
    """
    __tablename__ = "categorie_alimenti"

    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True)        # Italiano: "Cereali e derivati"
    nome_en: str                          # Inglese: "Cereals and derivatives"
    icona: Optional[str] = None          # Emoji o slug: "🌾", "grain"


class Food(SQLModel, table=True):
    """
    Alimento con macro e micronutrienti per 100g.

    Fonte: CREA 2019 (Tabelle di Composizione degli Alimenti, IV ed.)
    integrato con USDA FoodData Central per alimenti senza equivalente CREA.

    Tutti i valori nutrizionali riferiti a 100g di prodotto edibile.
    I campi opzionali possono essere NULL se il dato non e' disponibile nella fonte.
    """
    __tablename__ = "alimenti"

    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True)                          # "Pasta di semola, secca"
    nome_en: Optional[str] = None                          # "Dry semolina pasta"
    categoria_id: int = Field(
        foreign_key="categorie_alimenti.id", index=True
    )

    # Macronutrienti (per 100g) — obbligatori
    energia_kcal: float                                    # 353.0
    proteine_g: float                                      # 12.9
    carboidrati_g: float                                   # 72.2
    grassi_g: float                                        # 1.5

    # Macronutrienti (per 100g) — opzionali
    di_cui_zuccheri_g: Optional[float] = None             # 2.1
    di_cui_saturi_g: Optional[float] = None               # 0.3
    fibra_g: Optional[float] = None                        # 2.7
    sodio_mg: Optional[float] = None                       # 5.0
    acqua_g: Optional[float] = None                        # 11.8
    colesterolo_mg: Optional[float] = None                 # 0.0

    # Minerali (per 100g) — opzionali
    calcio_mg: Optional[float] = None                      # 15.0
    ferro_mg: Optional[float] = None                       # 1.4
    zinco_mg: Optional[float] = None                       # 1.2
    magnesio_mg: Optional[float] = None                    # 40.0
    fosforo_mg: Optional[float] = None                     # 190.0
    potassio_mg: Optional[float] = None                    # 200.0
    selenio_ug: Optional[float] = None                     # 30.0

    # Vitamine (per 100g) — opzionali
    vitamina_a_ug: Optional[float] = None                  # retinolo equivalenti
    vitamina_d_ug: Optional[float] = None                  # colecalciferolo
    vitamina_e_mg: Optional[float] = None                  # alfa-tocoferolo
    vitamina_c_mg: Optional[float] = None                  # acido ascorbico
    vitamina_b1_mg: Optional[float] = None                 # tiamina
    vitamina_b2_mg: Optional[float] = None                 # riboflavina
    vitamina_b3_mg: Optional[float] = None                 # niacina
    vitamina_b6_mg: Optional[float] = None                 # piridossina
    vitamina_b9_ug: Optional[float] = None                 # folato
    vitamina_b12_ug: Optional[float] = None                # cobalamina

    note: Optional[str] = None                             # "Valore medio CREA 2019"
    source: str = Field(default="crea")                   # "crea" | "usda" | "custom"
    food_type: str = Field(default="ingrediente")          # "ingrediente" | "pietanza" | "bevanda"
    is_active: bool = Field(default=True)


class StandardPortion(SQLModel, table=True):
    """
    Porzioni standard per alimento (es. "1 fetta di pane = 30g").

    Un alimento puo' avere piu' porzioni standard (es. pane: fetta, panino, pagnotta).
    Usate come shortcut nel piano alimentare per non dover inserire i grammi manualmente.
    """
    __tablename__ = "porzioni_standard"

    id: Optional[int] = Field(default=None, primary_key=True)
    alimento_id: int = Field(foreign_key="alimenti.id", index=True)
    nome: str                             # "1 fetta", "1 cucchiaio", "1 porzione tipica"
    grammi: float                         # 30.0, 15.0, 80.0


class DishRecipe(SQLModel, table=True):
    """
    Composizione di una pietanza: quali ingredienti e in che quantita'.

    Una pietanza (food_type='pietanza') e' composta da N ingredienti
    (food_type='ingrediente'). Questa tabella mappa la ricetta.

    I valori nutrizionali della pietanza in Food sono per 100g di piatto finito
    (calcolati dalla composizione o misurati sperimentalmente come fa il CREA).
    La ricetta qui serve per:
      - Mostrare al trainer la composizione del piatto
      - Permettere sostituzioni intelligenti di ingredienti
      - Drill-down nutrizionale per ingrediente

    Esempio: "Frittata di spinaci" (pietanza_id=200)
      → ingrediente_id=118 (Uovo intero), quantita_g=120, note="2 uova"
      → ingrediente_id=144 (Spinaci, crudi), quantita_g=80
      → ingrediente_id=159 (Olio EVO), quantita_g=10, note="1 cucchiaio"
    """
    __tablename__ = "ricette_pietanze"

    id: Optional[int] = Field(default=None, primary_key=True)
    pietanza_id: int = Field(foreign_key="alimenti.id", index=True)
    ingrediente_id: int = Field(foreign_key="alimenti.id", index=True)
    quantita_g: float                     # grammi ingrediente per 1 porzione
    note: Optional[str] = None            # "a crudo", "scolato", "2 uova"


class PlanTemplate(SQLModel, table=True):
    """
    Template piano alimentare con dieta settimanale completa.

    Dati catalogo read-only in nutrition.db (no deleted_at).
    I template popolati contengono pasti e componenti per 7 giorni.
    """
    __tablename__ = "plan_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)   # "donna_under30_attiva"
    nome: str
    descrizione: str
    tags: str                                      # JSON: '["donna","under30","attiva"]'
    obiettivo_calorico: int
    proteine_g_target: int
    carboidrati_g_target: int
    grassi_g_target: int
    note_cliniche: str
    is_active: bool = Field(default=True)


class TemplatePlanMeal(SQLModel, table=True):
    """Pasto di un template piano (giorno × tipo_pasto)."""
    __tablename__ = "template_plan_meals"

    id: Optional[int] = Field(default=None, primary_key=True)
    template_id: int = Field(foreign_key="plan_templates.id", index=True)
    giorno_settimana: int    # 1-7 (lun-dom)
    tipo_pasto: str          # COLAZIONE, PRANZO, etc.
    ordine: int = Field(default=0)
    nome: Optional[str] = None
    note: Optional[str] = None


class TemplatePlanComponent(SQLModel, table=True):
    """Componente (alimento × grammi) di un pasto template."""
    __tablename__ = "template_plan_components"

    id: Optional[int] = Field(default=None, primary_key=True)
    meal_id: int = Field(foreign_key="template_plan_meals.id", index=True)
    alimento_id: int = Field(foreign_key="alimenti.id", index=True)
    quantita_g: float
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# crm.db — trainer-owned, Bouncer Pattern + Deep IDOR
# ---------------------------------------------------------------------------


class NutritionPlan(SQLModel, table=True):
    """
    Piano alimentare assegnato da trainer a cliente.

    Un cliente puo' avere piu' piani (es. cutting + mantenimento) ma
    solo uno attivo alla volta (attivo=True).
    I target macro sono indicativi — calcolati in base al profilo cliente.
    """
    __tablename__ = "piani_alimentari"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    id_cliente: int = Field(foreign_key="clienti.id", index=True)
    nome: str                                              # "Piano ipocalorico estate 2026"

    # Target macro giornalieri — opzionali (se non specificati = no target)
    obiettivo_calorico: Optional[int] = None              # 1800 kcal/die
    proteine_g_target: Optional[int] = None               # 140g
    carboidrati_g_target: Optional[int] = None            # 180g
    grassi_g_target: Optional[int] = None                 # 60g

    note_cliniche: Optional[str] = None                   # Note visibili solo al trainer
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    attivo: bool = Field(default=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    deleted_at: Optional[datetime] = None


class PlanMeal(SQLModel, table=True):
    """
    Pasto all'interno di un piano alimentare.

    giorno_settimana: 0 = ogni giorno, 1 = lunedi, 2 = martedi, ..., 7 = domenica.
    tipo_pasto: enum string (COLAZIONE, SPUNTINO_MATTINA, PRANZO, ecc.)
    ordine: determina l'ordine di visualizzazione nella giornata.
    """
    __tablename__ = "pasti_piano"

    id: Optional[int] = Field(default=None, primary_key=True)
    piano_id: int = Field(foreign_key="piani_alimentari.id", index=True)

    giorno_settimana: int = Field(default=0)   # 0=ogni giorno, 1..7 = lun..dom
    tipo_pasto: str                             # "COLAZIONE" | "PRANZO" | ecc.
    ordine: int = Field(default=0)             # ordine visualizzazione nella giornata
    nome: Optional[str] = None                 # override (default: label tipo_pasto)
    note: Optional[str] = None

    deleted_at: Optional[datetime] = None


class MealComponent(SQLModel, table=True):
    """
    Componente (alimento × grammi) di un pasto.

    alimento_id e' una cross-DB reference verso nutrition.db.
    Nessun FK constraint a livello DB — integrità applicativa nel router.
    Il router verifica che l'alimento esista in nutrition.db prima del salvataggio.
    """
    __tablename__ = "componenti_pasto"

    id: Optional[int] = Field(default=None, primary_key=True)
    pasto_id: int = Field(foreign_key="pasti_piano.id", index=True)

    # Cross-DB ref → nutrition.db alimenti.id (no FK constraint, come esercizi_muscoli)
    alimento_id: int = Field(index=True)
    quantita_g: float                          # grammi (es. 80.0 per porzione pasta)
    note: Optional[str] = None

    deleted_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# crm.db — template pasti riutilizzabili (trainer-owned)
# ---------------------------------------------------------------------------


class MealTemplate(SQLModel, table=True):
    """
    Template pasto riutilizzabile creato dal trainer.

    Permette di salvare una combinazione di alimenti (es. "Colazione proteica")
    e riapplicarla rapidamente a qualsiasi pasto di qualsiasi piano.
    """
    __tablename__ = "meal_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    nome: str                              # "Colazione proteica", "Pranzo fit"
    tipo_pasto: Optional[str] = None       # suggerimento default (nullable)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    deleted_at: Optional[datetime] = None


class TemplateComponent(SQLModel, table=True):
    """
    Componente di un template pasto.

    Stessa struttura di MealComponent ma legato a MealTemplate.
    alimento_id e' cross-DB reference verso nutrition.db (no FK constraint).
    """
    __tablename__ = "template_components"

    id: Optional[int] = Field(default=None, primary_key=True)
    template_id: int = Field(foreign_key="meal_templates.id", index=True)
    alimento_id: int = Field(index=True)   # cross-DB ref → nutrition.db
    quantita_g: float
    note: Optional[str] = None
    deleted_at: Optional[datetime] = None
