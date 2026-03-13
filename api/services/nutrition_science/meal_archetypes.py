"""
Archetipi pasto e pool alimentari per il generatore LARN v2.

Architettura dish-based: PRANZO e CENA usano pietanze composte,
COLAZIONE e spuntini usano ingredienti singoli.

Pattern alimentari italiani:
  - PRANZO: primo piatto (pietanza) + contorno + olio
  - CENA: secondo piatto (pietanza, protein-rotated) + contorno + pane + olio
  - COLAZIONE: yogurt/latte + cereali + frutta + frutta secca
  - SPUNTINI: frutta, yogurt, frutta secca

Porzioni default allineate a LARN 2014:
  - Primo piatto: ~200g (peso finito, include condimento)
  - Secondo piatto: ~160g (peso finito, include condimento)
  - Contorno: 200g | Pane: 50g | Frutta: 150g | Olio: 10g
  - Yogurt/latte: 125g | Frutta secca: 30g

Frequenze allineate a CREA 2018 Direttive 1-13.
"""

from dataclasses import dataclass, field


@dataclass
class MealSlot:
    """Slot funzionale dentro un pasto."""
    ruolo: str       # es. "primo_piatto", "secondo_poultry", "vegetable"
    grammi: float    # porzione default
    obbligatorio: bool = True


@dataclass
class MealArchetype:
    """Struttura di un tipo pasto."""
    tipo_pasto: str
    slots: list[MealSlot] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Archetipi pasto (struttura standard italiana v2 — dish-based)
# ---------------------------------------------------------------------------

ARCHETYPES: dict[str, MealArchetype] = {
    "COLAZIONE": MealArchetype(
        tipo_pasto="COLAZIONE",
        slots=[
            MealSlot("dairy", 125),           # yogurt/latte (LARN: 125g)
            MealSlot("cereal", 30),            # fiocchi/fette bisc. (LARN: 30g)
            MealSlot("fruit", 150),            # frutta fresca (LARN: 150g)
            MealSlot("nuts", 30, obbligatorio=False),  # frutta secca (LARN: 30g)
        ],
    ),
    "SPUNTINO_MATTINA": MealArchetype(
        tipo_pasto="SPUNTINO_MATTINA",
        slots=[
            MealSlot("fruit", 150),            # frutta fresca (LARN: 150g)
        ],
    ),
    "PRANZO": MealArchetype(
        tipo_pasto="PRANZO",
        slots=[
            # Primo piatto pietanza (peso finito: pasta cotta + sugo + condimento)
            MealSlot("primo_piatto", 200),
            # Contorno: pietanza composta o verdura cruda
            MealSlot("contorno", 200),
            # Olio extra per il contorno (se contorno non composto)
            MealSlot("fat", 5),
        ],
    ),
    "SPUNTINO_POMERIGGIO": MealArchetype(
        tipo_pasto="SPUNTINO_POMERIGGIO",
        slots=[
            MealSlot("dairy_light", 125),      # yogurt (LARN: 125g)
            MealSlot("nuts", 30, obbligatorio=False),  # frutta secca (LARN: 30g)
        ],
    ),
    "CENA": MealArchetype(
        tipo_pasto="CENA",
        slots=[
            # Secondo piatto pietanza (proteina-rotated settimanalmente)
            MealSlot("secondo_piatto", 160),
            # Contorno
            MealSlot("contorno", 200),
            # Pane
            MealSlot("carb_light", 50),        # pane (LARN: 50g)
            # Olio extra
            MealSlot("fat", 5),
        ],
    ),
}

# Ordine pasti nella giornata
MEAL_ORDER = ["COLAZIONE", "SPUNTINO_MATTINA", "PRANZO", "SPUNTINO_POMERIGGIO", "CENA"]

# ---------------------------------------------------------------------------
# Pool alimentari: ruolo → lista di nomi alimento da nutrition.db
#
# I nomi devono corrispondere ESATTAMENTE ai nomi in nutrition.db.
# Il generatore risolve nome → id a runtime.
#
# Pool pietanze (food_type='pietanza') per pasti principali.
# Pool ingredienti (food_type='ingrediente') per colazione/spuntini.
# ---------------------------------------------------------------------------

FOOD_POOLS: dict[str, list[str]] = {
    # ── Colazione e spuntini (ingredienti singoli) ──

    "dairy": [
        "Yogurt greco 0% grassi",
        "Yogurt greco intero",
        "Yogurt intero bianco",
        "Latte parzialmente scremato",
        "Latte intero, fresco",
        "Ricotta di vaccino",
    ],
    "dairy_light": [
        "Yogurt greco 0% grassi",
        "Yogurt greco intero",
        "Yogurt intero bianco",
        "Fiocchi di latte (cottage cheese)",
    ],
    "cereal": [
        "Avena, fiocchi",
        "Fette biscottate integrali",
        "Pane integrale",
        "Gallette di riso",
    ],
    "carb_light": [
        "Pane integrale",
        "Pane di segale",
        "Gallette di riso",
    ],
    "fruit": [
        "Mela, fresca",
        "Banana, fresca",
        "Arancia, fresca",
        "Pera, fresca",
        "Kiwi",
        "Fragole, fresche",
        "Pesca, fresca",
        "Mirtilli, freschi",
        "Ananas, fresco",
    ],
    "nuts": [
        "Mandorle",
        "Noci",
        "Nocciole",
        "Semi di zucca",
        "Semi di chia",
    ],
    "fat": [
        "Olio di oliva extravergine",
    ],

    # ── Primi piatti (pietanze — PRANZO) ──

    "primo_piatto": [
        "Pasta al pomodoro",
        "Pasta integrale al pomodoro",
        "Pasta e fagioli",
        "Pasta e lenticchie",
        "Pasta e ceci",
        "Pasta con tonno e pomodoro",
        "Pasta con salmone e zucchine",
        "Risotto ai funghi",
        "Cous cous con verdure",
        "Farro con verdure",
    ],

    # ── Secondi piatti (pietanze — CENA, protein-rotated) ──

    "secondo_poultry": [
        "Petto di pollo alla griglia",
        "Pollo con verdure",
        "Hamburger di tacchino",
    ],
    "secondo_fish": [
        "Salmone al forno con limone",
        "Merluzzo al forno con pomodorini",
        "Branzino al forno",
        "Gamberi saltati in padella",
    ],
    "secondo_legume": [
        "Tofu saltato con verdure",
        "Tempeh con verdure",
        # Legumi puri come fallback (l'optimizer puo' aggiustarli)
        "Lenticchie, cotte",
        "Ceci, cotti",
        "Fagioli borlotti, cotti",
    ],
    "secondo_egg": [
        "Frittata di spinaci",
        "Frittata di zucchine",
    ],
    "secondo_red_meat": [
        "Scaloppine di vitello",
        "Lonza di maiale al forno",
        "Polpette di manzo al pomodoro",
    ],
    "secondo_deli": [
        "Bresaola",
        "Prosciutto crudo, magro",
    ],

    # ── Contorni (mix pietanze + ingredienti) ──

    "contorno": [
        # Contorni composti (pietanze)
        "Insalata mista",
        "Verdure grigliate miste",
        "Spinaci saltati",
        "Broccoli al vapore con olio",
        "Caponata di verdure",
        "Insalata di finocchi e arance",
        "Patate al forno",
        # Verdure singole (ingredienti — l'olio viene dallo slot fat)
        "Broccoli, cotti",
        "Zucchine",
        "Pomodori, freschi",
        "Carote",
        "Peperoni rossi",
        "Fagiolini, cotti",
        "Finocchio",
        "Asparagi",
    ],
}

# ---------------------------------------------------------------------------
# Rotazione settimanale proteine (Lun-Dom)
#
# Allineata a CREA 2018 Dir. 9:
#   Pesce 2-3x, Carne bianca 1-3x, Legumi 2-4x, Uova 2-4x,
#   Carne rossa max 1-2x, Affettati max 1x.
#
# Il primo piatto a PRANZO ha proteine integrate (pasta e fagioli,
# pasta con tonno, ecc.). La rotazione proteica si applica al
# SECONDO piatto a CENA.
#
# Totale cena: pesce 2x, pollo 2x, legumi 2x, uova 1x = 7 cene
# + primi pranzo con proteine (tonno 1x, legumi 3x = dentro range CREA)
# ---------------------------------------------------------------------------

# Secondo piatto per CENA di ogni giorno 1-7
#
# Allineato a CREA 2018 Dir. 9 sub-frequenze:
#   Pesce 2-3x, Pollo 1-3x, Legumi 2-4x, Uova 2-4x,
#   Carne rossa max 1-2x, Affettati max 1x.
#
# Totale: pesce 2x, pollo 1x, legumi 2x, uova 2x = 7 cene
WEEKLY_SECONDO_ROTATION: list[str] = [
    "secondo_poultry",     # Lun: pollo/tacchino
    "secondo_fish",        # Mar: pesce
    "secondo_legume",      # Mer: legumi/tofu
    "secondo_egg",         # Gio: uova (frittata)
    "secondo_fish",        # Ven: pesce
    "secondo_legume",      # Sab: legumi/tofu
    "secondo_egg",         # Dom: uova (frittata)
]

# Mapping secondo_* → ruolo proteico per il frequency_validator
SECONDO_TO_PROTEIN_ROLE: dict[str, str] = {
    "secondo_poultry": "protein_poultry",
    "secondo_fish": "protein_fish",
    "secondo_legume": "protein_legume",
    "secondo_egg": "protein_egg",
    "secondo_red_meat": "protein_red_meat",
    "secondo_deli": "protein_deli",
}
