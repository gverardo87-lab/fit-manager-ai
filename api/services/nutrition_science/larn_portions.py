"""
Porzioni Standard LARN 2014 e Gruppi Alimentari.

Fonte: SINU — Societa' Italiana di Nutrizione Umana, LARN IV Revisione (2014),
       Capitolo "Standard Quantitativi delle Porzioni".
       Linee Guida per una Sana Alimentazione — CREA 2018 (frequenze).

Architettura:
  - LARN_STANDARD_PORTIONS: porzione in grammi per sotto-gruppo (dato ufficiale SINU)
  - LARN_FOOD_GROUPS: mapping 5 gruppi LARN → categorie nutrition.db
  - LARN_WEEKLY_FREQUENCIES: porzioni/settimana raccomandate per sotto-gruppo (CREA 2018)
  - count_weekly_portions(): conta porzioni standard consumate da un piano
  - assess_frequencies(): valuta compliance frequenze vs target CREA
"""


# ---------------------------------------------------------------------------
# Porzioni standard LARN 2014 (grammi per porzione)
#
# Fonte: SINU, "Standard Quantitativi delle Porzioni", LARN 2014 Tab. 1
# Ogni voce: sotto-gruppo → grammi porzione standard
# ---------------------------------------------------------------------------

LARN_STANDARD_PORTIONS: dict[str, float] = {
    # Cereali e tuberi
    "pane": 50,
    "pasta_secca": 80,
    "pasta_fresca": 100,
    "pasta_ripiena": 125,
    "riso": 80,
    "cereali_colazione": 30,
    "fette_biscottate": 30,       # ~3 fette
    "crackers": 30,
    "prodotti_forno_dolci": 50,    # brioche, croissant
    "patate": 200,

    # Piatti composti (peso finito = 1 porzione LARN)
    "primo_piatto": 200,           # 1 primo = ~80g pasta secca + condimento
    "secondo_piatto": 160,         # 1 secondo = proteina + condimento

    # Frutta e verdura
    "frutta_fresca": 150,
    "insalata_foglia": 80,
    "verdura_altra": 200,

    # Carne, pesce, uova, legumi
    "carne_fresca": 100,           # rossa e bianca
    "pesce_fresco": 150,
    "pesce_conservato": 50,        # tonno in scatola scolato
    "uova": 50,                    # 1 uovo
    "legumi_secchi": 50,
    "legumi_freschi": 150,
    "affettati": 50,
    "tofu_tempeh": 100,

    # Latte e derivati
    "latte": 125,                  # 1 bicchiere
    "yogurt": 125,                 # 1 vasetto
    "formaggio_fresco": 100,       # mozzarella
    "formaggio_stagionato": 50,    # parmigiano, grana

    # Grassi da condimento
    "olio": 10,                    # 1 cucchiaio

    # Frutta secca
    "frutta_secca": 30,

    # Dolci
    "dolci": 30,                   # cioccolato, caramelle
    "dessert": 100,                # torta, gelato
}


# ---------------------------------------------------------------------------
# Mapping ruoli meal_archetypes → sotto-gruppo LARN per porzioni
#
# Collega i ruoli usati nel generatore ai sotto-gruppi LARN ufficiali.
# Usato da portion_optimizer per clampare alle porzioni standard.
# ---------------------------------------------------------------------------

ROLE_TO_LARN_PORTION: dict[str, str] = {
    # Cereali
    "cereal": "cereali_colazione",
    "carb_light": "pane",                 # pane/gallette a cena → conta come pane

    # Primo piatto (pietanza) — 1 primo = 1 porzione LARN primo_piatto (200g)
    "primo_piatto": "primo_piatto",

    # Frutta/verdura
    "fruit": "frutta_fresca",
    "contorno": "verdura_altra",          # contorno (pietanza o verdura)

    # Secondo piatto (pietanze protein-rotated) → secondo_piatto standard
    "secondo_poultry": "secondo_piatto",
    "secondo_fish": "secondo_piatto",
    "secondo_legume": "secondo_piatto",
    "secondo_egg": "secondo_piatto",
    "secondo_red_meat": "secondo_piatto",
    "secondo_deli": "secondo_piatto",

    # Legacy roles (backward-compat)
    "protein_main": "carne_fresca",
    "protein_poultry": "carne_fresca",
    "protein_fish": "pesce_fresco",
    "protein_legume": "legumi_freschi",
    "protein_egg": "uova",
    "protein_red_meat": "carne_fresca",
    "protein_deli": "affettati",
    "carb_cooked": "pasta_secca",
    "bread": "pane",
    "salad": "insalata_foglia",
    "vegetable": "verdura_altra",

    # Latticini
    "dairy": "yogurt",
    "dairy_light": "yogurt",

    # Grassi e frutta secca
    "fat": "olio",
    "nuts": "frutta_secca",
}


# ---------------------------------------------------------------------------
# 5 Gruppi alimentari LARN — mapping verso categorie nutrition.db
#
# Ogni gruppo contiene:
#   - categorie_db: lista ID categorie_alimenti in nutrition.db
#   - sotto_gruppi: sotto-gruppi LARN con porzione standard
#   - note: raccomandazione sintetica
# ---------------------------------------------------------------------------

LARN_FOOD_GROUPS: dict[str, dict] = {
    "cereali_tuberi": {
        "label": "Cereali, derivati e tuberi",
        "categorie_db": [1, 2, 3],     # Cereali, Pasta/riso cotti, Pane/forno
        "sotto_gruppi": ["pane", "pasta_secca", "pasta_fresca", "riso",
                         "cereali_colazione", "fette_biscottate", "patate"],
        "note": "Privilegiare cereali integrali (LARN: ≥50% dei cereali)",
    },
    "frutta_verdura": {
        "label": "Frutta e verdura",
        "categorie_db": [5, 6],         # Verdure, Frutta fresca
        "sotto_gruppi": ["frutta_fresca", "insalata_foglia", "verdura_altra"],
        "note": "5 porzioni/giorno minimo, variare i colori (WCRF 2018)",
    },
    "proteine": {
        "label": "Carne, pesce, uova, legumi",
        "categorie_db": [4, 8, 9, 10, 11],  # Legumi, Carne, Salumi, Pesce, Uova
        "sotto_gruppi": ["carne_fresca", "pesce_fresco", "pesce_conservato",
                         "uova", "legumi_secchi", "legumi_freschi", "affettati"],
        "note": "Alternare fonti proteiche nella settimana (CREA 2018 Dir. 9)",
    },
    "latte_derivati": {
        "label": "Latte e derivati",
        "categorie_db": [12],            # Latte, yogurt, formaggi
        "sotto_gruppi": ["latte", "yogurt", "formaggio_fresco", "formaggio_stagionato"],
        "note": "Preferire latte/yogurt a basso contenuto di grassi",
    },
    "grassi_condimento": {
        "label": "Grassi da condimento",
        "categorie_db": [13],            # Oli e condimenti
        "sotto_gruppi": ["olio"],
        "note": "Olio EVO come condimento principale (LARN: 20-35% energia da lipidi)",
    },
}


# ---------------------------------------------------------------------------
# Frequenze di consumo CREA 2018 — porzioni/settimana per sotto-gruppo
#
# Fonte: Linee Guida per una Sana Alimentazione, CREA 2018, Direttiva 1-13.
# Formato: (min_porzioni_settimana, max_porzioni_settimana)
#
# Nota: i valori giornalieri sono moltiplicati x7 per uniformare a settimanale.
# Es. frutta 2-3/giorno → 14-21/settimana.
# ---------------------------------------------------------------------------

LARN_WEEKLY_FREQUENCIES: dict[str, tuple[int, int]] = {
    # === Piatti composti (v2 dish-based) ===
    # Primo piatto: 1/giorno a pranzo → 5-7/settimana
    "primo_piatto": (5, 7),
    # Secondo piatto: 1/giorno a cena → 5-7/settimana
    "secondo_piatto": (5, 7),

    # === Cereali (colazione + cena) ===
    "pane": (5, 14),               # pane a cena + eventuale colazione
    "cereali_colazione": (5, 7),   # colazione quotidiana

    # === Frutta e verdura — 5+ porzioni/giorno → 35+/settimana ===
    "frutta_fresca": (14, 21),     # 2-3 porzioni/giorno
    "verdura_altra": (10, 21),     # contorni (i primi contengono gia' verdure)

    # === Latticini — 2-3 porzioni/giorno → 14-21/settimana ===
    "yogurt": (7, 14),             # 1-2/giorno (colazione + spuntino)

    # === Grassi — 2-4 porzioni/giorno → 14-28/settimana ===
    # Nota: i primi/secondi piatti contengono gia' olio (calcolato nei macro).
    # Il conteggio qui e' per l'olio esplicito aggiuntivo.
    "olio": (3, 14),               # ridotto: condimento extra per contorni

    # === Frutta secca — 1 porzione/giorno → 7/settimana ===
    "frutta_secca": (5, 7),        # quasi quotidiano
}


# ---------------------------------------------------------------------------
# Sub-frequenze proteine specifiche (CREA 2018 Dir. 9)
#
# Sono vincoli aggiuntivi DENTRO il gruppo proteine.
# Il validator le usa per generare warning specifici.
# ---------------------------------------------------------------------------

PROTEIN_SUB_FREQUENCIES: dict[str, dict] = {
    "pesce": {
        "label": "Pesce",
        "min": 2, "max": 3,
        "ruoli": ["protein_fish", "secondo_fish"],
        "nota": "CREA 2018: 2-3 porzioni/settimana, preferire pesce azzurro",
    },
    "carne_bianca": {
        "label": "Carne bianca",
        "min": 1, "max": 3,
        "ruoli": ["protein_poultry", "secondo_poultry"],
        "nota": "CREA 2018: 1-3 porzioni/settimana",
    },
    "carne_rossa": {
        "label": "Carne rossa",
        "min": 0, "max": 2,
        "ruoli": ["protein_red_meat", "secondo_red_meat"],
        "nota": "CREA 2018: max 1-2 porzioni/settimana (WCRF: limitare)",
    },
    "uova": {
        "label": "Uova",
        "min": 2, "max": 4,
        "ruoli": ["protein_egg", "secondo_egg"],
        "nota": "CREA 2018: 2-4 uova/settimana",
    },
    "legumi": {
        "label": "Legumi",
        "min": 2, "max": 4,
        "ruoli": ["protein_legume", "secondo_legume"],
        "nota": "CREA 2018: 2-4 porzioni/settimana, fonte proteica vegetale",
    },
    "affettati": {
        "label": "Affettati",
        "min": 0, "max": 1,
        "ruoli": ["protein_deli", "secondo_deli"],
        "nota": "CREA 2018: max 1 porzione/settimana",
    },
}


# ---------------------------------------------------------------------------
# Nutrienti con fonti alimentari limitate (scoring attenuato)
#
# Questi nutrienti sono riconosciuti da LARN 2014 come difficili da
# raggiungere con la sola alimentazione. Il validatore li pesa di meno
# e aggiunge una nota clinica invece di penalizzare lo score.
# ---------------------------------------------------------------------------

DIET_LIMITED_NUTRIENTS: dict[str, str] = {
    "vitamina_d_ug": (
        "Vitamina D: il LARN 2014 riconosce che l'apporto alimentare e' "
        "insufficiente nella maggior parte della popolazione italiana. "
        "La sintesi cutanea (esposizione solare) e/o la supplementazione "
        "sono le fonti primarie raccomandate."
    ),
}
