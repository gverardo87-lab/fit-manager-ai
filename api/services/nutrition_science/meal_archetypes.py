"""
Archetipi pasto e pool alimentari per il generatore LARN.

Ogni tipo pasto ha una struttura a slot (ruoli funzionali) con grammi default.
I pool alimentari mappano food names → ruoli per la selezione.

Pattern alimentari italiani: colazione dolce/proteica, pranzo completo,
cena leggera, 2 spuntini. Varieta' settimanale: pesce 2-3x, legumi 2-3x,
carne bianca 2x, uova 1x, carne rossa max 1x.
"""

from dataclasses import dataclass, field


@dataclass
class MealSlot:
    """Slot funzionale dentro un pasto."""
    ruolo: str       # es. "protein_animal", "carb_cooked", "vegetable"
    grammi: float    # porzione default
    obbligatorio: bool = True


@dataclass
class MealArchetype:
    """Struttura di un tipo pasto."""
    tipo_pasto: str
    slots: list[MealSlot] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Archetipi pasto (struttura standard italiana)
# ---------------------------------------------------------------------------

ARCHETYPES: dict[str, MealArchetype] = {
    "COLAZIONE": MealArchetype(
        tipo_pasto="COLAZIONE",
        slots=[
            MealSlot("dairy", 170),          # yogurt / latte
            MealSlot("cereal", 50),           # fiocchi avena / pane / fette bisc.
            MealSlot("fruit", 150),           # frutta fresca
            MealSlot("nuts", 20, obbligatorio=False),  # frutta secca
        ],
    ),
    "SPUNTINO_MATTINA": MealArchetype(
        tipo_pasto="SPUNTINO_MATTINA",
        slots=[
            MealSlot("fruit", 200),
        ],
    ),
    "PRANZO": MealArchetype(
        tipo_pasto="PRANZO",
        slots=[
            MealSlot("protein_main", 150),    # carne/pesce/legumi/uova
            MealSlot("carb_cooked", 100),     # pasta/riso/farro cotto (~80g crudo)
            MealSlot("vegetable", 200),       # contorno
            MealSlot("fat", 12),              # olio EVO
            MealSlot("bread", 40, obbligatorio=False),
        ],
    ),
    "SPUNTINO_POMERIGGIO": MealArchetype(
        tipo_pasto="SPUNTINO_POMERIGGIO",
        slots=[
            MealSlot("dairy_light", 150),     # yogurt
            MealSlot("nuts", 20, obbligatorio=False),
        ],
    ),
    "CENA": MealArchetype(
        tipo_pasto="CENA",
        slots=[
            MealSlot("protein_main", 160),    # proteina principale
            MealSlot("vegetable", 250),       # contorno abbondante
            MealSlot("carb_light", 50),       # pane o piccola porzione cereale
            MealSlot("fat", 12),              # olio EVO
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
# ---------------------------------------------------------------------------

FOOD_POOLS: dict[str, list[str]] = {
    "dairy": [
        "Yogurt greco 0% grassi",
        "Yogurt greco intero",
        "Yogurt intero bianco",
        "Latte parzialmente scremato",
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
    "carb_cooked": [
        "Pasta integrale, cotta",
        "Pasta di semola, cotta",
        "Riso integrale, cotto",
        "Farro, cotto",
        "Quinoa, cotta",
        "Cous cous, cotto",
    ],
    "carb_light": [
        "Pane integrale",
        "Pane di segale",
        "Gallette di riso",
    ],
    "bread": [
        "Pane integrale",
        "Pane di segale",
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
    "vegetable": [
        "Spinaci, crudi",
        "Broccoli, cotti",
        "Zucchine",
        "Pomodori, freschi",
        "Carote",
        "Peperoni rossi",
        "Fagiolini, cotti",
        "Finocchio",
        "Lattuga, iceberg",
        "Rucola",
        "Cavolo nero",
        "Bietola",
        "Asparagi",
    ],
    "fat": [
        "Olio di oliva extravergine",
    ],

    # ── Proteine: pool separati per rotazione settimanale ──

    "protein_poultry": [
        "Petto di pollo, crudo",
        "Petto di tacchino, crudo",
    ],
    "protein_fish": [
        "Salmone atlantico, crudo",
        "Merluzzo, filetto crudo",
        "Orata, cruda",
        "Sgombro, crudo",
        "Trota, cruda",
        "Branzino, cotto",
        "Tonno in scatola al naturale",
    ],
    "protein_legume": [
        "Lenticchie, cotte",
        "Ceci, cotti",
        "Fagioli borlotti, cotti",
        "Fagioli bianchi cannellini, cotti",
        "Edamame, cotti",
    ],
    "protein_egg": [
        "Uovo intero, crudo",
    ],
    "protein_red_meat": [
        "Manzo, fesa, cruda",
        "Vitello, scaloppina cruda",
    ],
    "protein_deli": [
        "Bresaola",
        "Prosciutto crudo, magro",
    ],
}

# ---------------------------------------------------------------------------
# Rotazione settimanale proteine (Lun-Dom)
#
# Schema: pesce 3x, pollo/tacchino 2x, legumi 2x, uova 1x,
# carne rossa max 1x. Distribuzione bilanciata ferro/omega3/fibra.
# ---------------------------------------------------------------------------

# (pranzo_pool, cena_pool) per ogni giorno 1-7
WEEKLY_PROTEIN_ROTATION: list[tuple[str, str]] = [
    # Lun: pollo pranzo, pesce cena
    ("protein_poultry", "protein_fish"),
    # Mar: legumi pranzo, pollo cena
    ("protein_legume", "protein_poultry"),
    # Mer: pesce pranzo, uova cena
    ("protein_fish", "protein_egg"),
    # Gio: legumi pranzo, bresaola/crudo cena
    ("protein_legume", "protein_deli"),
    # Ven: pesce pranzo, pollo cena
    ("protein_fish", "protein_poultry"),
    # Sab: carne rossa pranzo, pesce cena
    ("protein_red_meat", "protein_fish"),
    # Dom: uova pranzo, legumi cena
    ("protein_egg", "protein_legume"),
]
