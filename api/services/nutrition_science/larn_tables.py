"""
Tabelle LARN 2014 — Livelli di Assunzione di Riferimento di Nutrienti ed energia.

Fonte: SINU (Societa' Italiana di Nutrizione Umana), IV Revisione, 2014.
Capitoli: Energia, Proteine, Lipidi, Carboidrati, Fibra, Vitamine, Minerali.

Struttura: dict[nutriente] → list di fasce eta'/sesso con AR/PRI/AI/UL.
Ogni entry e' un dict con: eta_min, eta_max, sesso, ar, pri, ai, ul.

Unita' di misura:
  - Proteine: g/kg/die (poi moltiplicare per peso corporeo)
  - Vitamine: mg o ug /die
  - Minerali: mg o ug /die
  - Fibra: g/die (AI)
  - Energia: kcal/die (non in questa tabella — calcolata da Harris-Benedict/Mifflin)

Note:
  - AR e PRI sono mutuamente esclusivi con AI per lo stesso nutriente/fascia
  - Se non esiste AR, si usa AI (es. vitamina D, K, potassio)
  - UL puo' essere assente se non definito (es. vitamina B12)
  - Gravidanza e allattamento hanno addendi separati (LARN_PREGNANCY_ADD, LARN_LACTATION_ADD)
"""

from api.services.nutrition_science.types import Sex


# ---------------------------------------------------------------------------
# Tipo entry: (eta_min, eta_max, sesso, ar, pri, ai, ul)
# None = non definito per quella fascia/livello
# ---------------------------------------------------------------------------

# Proteine (g/kg/die) — LARN 2014 Tab. Proteine
# AR e PRI espressi per kg di peso corporeo
LARN_PROTEINE_G_KG: list[dict] = [
    # Adulti 18-29
    {"eta_min": 18, "eta_max": 29, "sesso": Sex.M, "ar": 0.71, "pri": 0.90, "ai": None, "ul": None},
    {"eta_min": 18, "eta_max": 29, "sesso": Sex.F, "ar": 0.71, "pri": 0.90, "ai": None, "ul": None},
    # Adulti 30-59
    {"eta_min": 30, "eta_max": 59, "sesso": Sex.M, "ar": 0.71, "pri": 0.90, "ai": None, "ul": None},
    {"eta_min": 30, "eta_max": 59, "sesso": Sex.F, "ar": 0.71, "pri": 0.90, "ai": None, "ul": None},
    # Adulti 60-74
    {"eta_min": 60, "eta_max": 74, "sesso": Sex.M, "ar": 0.71, "pri": 1.10, "ai": None, "ul": None},
    {"eta_min": 60, "eta_max": 74, "sesso": Sex.F, "ar": 0.71, "pri": 1.10, "ai": None, "ul": None},
    # Anziani 75+
    {"eta_min": 75, "eta_max": 120, "sesso": Sex.M, "ar": 0.71, "pri": 1.10, "ai": None, "ul": None},
    {"eta_min": 75, "eta_max": 120, "sesso": Sex.F, "ar": 0.71, "pri": 1.10, "ai": None, "ul": None},
]

# ---------------------------------------------------------------------------
# Vitamine — valori in mg/die o ug/die come indicato
# ---------------------------------------------------------------------------

# Vitamina A (ug RE/die) — Retinolo Equivalenti
LARN_VITAMINA_A: list[dict] = [
    {"eta_min": 18, "eta_max": 29, "sesso": Sex.M, "ar": 500, "pri": 700, "ai": None, "ul": 3000},
    {"eta_min": 18, "eta_max": 29, "sesso": Sex.F, "ar": 400, "pri": 600, "ai": None, "ul": 3000},
    {"eta_min": 30, "eta_max": 59, "sesso": Sex.M, "ar": 500, "pri": 700, "ai": None, "ul": 3000},
    {"eta_min": 30, "eta_max": 59, "sesso": Sex.F, "ar": 400, "pri": 600, "ai": None, "ul": 3000},
    {"eta_min": 60, "eta_max": 74, "sesso": Sex.M, "ar": 500, "pri": 700, "ai": None, "ul": 3000},
    {"eta_min": 60, "eta_max": 74, "sesso": Sex.F, "ar": 400, "pri": 600, "ai": None, "ul": 3000},
    {"eta_min": 75, "eta_max": 120, "sesso": Sex.M, "ar": 500, "pri": 700, "ai": None, "ul": 3000},
    {"eta_min": 75, "eta_max": 120, "sesso": Sex.F, "ar": 400, "pri": 600, "ai": None, "ul": 3000},
]

# Vitamina D (ug/die) — solo AI, no AR/PRI per adulti (LARN 2014)
LARN_VITAMINA_D: list[dict] = [
    {"eta_min": 18, "eta_max": 59, "sesso": Sex.M, "ar": None, "pri": None, "ai": 15, "ul": 100},
    {"eta_min": 18, "eta_max": 59, "sesso": Sex.F, "ar": None, "pri": None, "ai": 15, "ul": 100},
    {"eta_min": 60, "eta_max": 74, "sesso": Sex.M, "ar": None, "pri": None, "ai": 15, "ul": 100},
    {"eta_min": 60, "eta_max": 74, "sesso": Sex.F, "ar": None, "pri": None, "ai": 15, "ul": 100},
    {"eta_min": 75, "eta_max": 120, "sesso": Sex.M, "ar": None, "pri": None, "ai": 20, "ul": 100},
    {"eta_min": 75, "eta_max": 120, "sesso": Sex.F, "ar": None, "pri": None, "ai": 20, "ul": 100},
]

# Vitamina E (mg/die) — alfa-tocoferolo, solo AI
LARN_VITAMINA_E: list[dict] = [
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.M, "ar": None, "pri": None, "ai": 13, "ul": 300},
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.F, "ar": None, "pri": None, "ai": 12, "ul": 300},
]

# Vitamina C (mg/die)
LARN_VITAMINA_C: list[dict] = [
    {"eta_min": 18, "eta_max": 29, "sesso": Sex.M, "ar": 75, "pri": 105, "ai": None, "ul": None},
    {"eta_min": 18, "eta_max": 29, "sesso": Sex.F, "ar": 60, "pri": 85, "ai": None, "ul": None},
    {"eta_min": 30, "eta_max": 59, "sesso": Sex.M, "ar": 75, "pri": 105, "ai": None, "ul": None},
    {"eta_min": 30, "eta_max": 59, "sesso": Sex.F, "ar": 60, "pri": 85, "ai": None, "ul": None},
    {"eta_min": 60, "eta_max": 74, "sesso": Sex.M, "ar": 75, "pri": 105, "ai": None, "ul": None},
    {"eta_min": 60, "eta_max": 74, "sesso": Sex.F, "ar": 60, "pri": 85, "ai": None, "ul": None},
    {"eta_min": 75, "eta_max": 120, "sesso": Sex.M, "ar": 75, "pri": 105, "ai": None, "ul": None},
    {"eta_min": 75, "eta_max": 120, "sesso": Sex.F, "ar": 60, "pri": 85, "ai": None, "ul": None},
]

# Vitamina B1 — Tiamina (mg/die)
LARN_VITAMINA_B1: list[dict] = [
    {"eta_min": 18, "eta_max": 59, "sesso": Sex.M, "ar": 1.0, "pri": 1.2, "ai": None, "ul": None},
    {"eta_min": 18, "eta_max": 59, "sesso": Sex.F, "ar": 0.9, "pri": 1.1, "ai": None, "ul": None},
    {"eta_min": 60, "eta_max": 120, "sesso": Sex.M, "ar": 1.0, "pri": 1.2, "ai": None, "ul": None},
    {"eta_min": 60, "eta_max": 120, "sesso": Sex.F, "ar": 0.9, "pri": 1.1, "ai": None, "ul": None},
]

# Vitamina B2 — Riboflavina (mg/die)
LARN_VITAMINA_B2: list[dict] = [
    {"eta_min": 18, "eta_max": 59, "sesso": Sex.M, "ar": 1.1, "pri": 1.6, "ai": None, "ul": None},
    {"eta_min": 18, "eta_max": 59, "sesso": Sex.F, "ar": 1.0, "pri": 1.3, "ai": None, "ul": None},
    {"eta_min": 60, "eta_max": 120, "sesso": Sex.M, "ar": 1.1, "pri": 1.6, "ai": None, "ul": None},
    {"eta_min": 60, "eta_max": 120, "sesso": Sex.F, "ar": 1.0, "pri": 1.3, "ai": None, "ul": None},
]

# Vitamina B3 — Niacina (mg NE/die)
LARN_VITAMINA_B3: list[dict] = [
    {"eta_min": 18, "eta_max": 59, "sesso": Sex.M, "ar": 14, "pri": 18, "ai": None, "ul": 900},
    {"eta_min": 18, "eta_max": 59, "sesso": Sex.F, "ar": 11, "pri": 14, "ai": None, "ul": 900},
    {"eta_min": 60, "eta_max": 120, "sesso": Sex.M, "ar": 14, "pri": 18, "ai": None, "ul": 900},
    {"eta_min": 60, "eta_max": 120, "sesso": Sex.F, "ar": 11, "pri": 14, "ai": None, "ul": 900},
]

# Vitamina B6 — Piridossina (mg/die)
LARN_VITAMINA_B6: list[dict] = [
    {"eta_min": 18, "eta_max": 59, "sesso": Sex.M, "ar": 1.1, "pri": 1.3, "ai": None, "ul": 25},
    {"eta_min": 18, "eta_max": 59, "sesso": Sex.F, "ar": 1.1, "pri": 1.3, "ai": None, "ul": 25},
    {"eta_min": 60, "eta_max": 120, "sesso": Sex.M, "ar": 1.4, "pri": 1.7, "ai": None, "ul": 25},
    {"eta_min": 60, "eta_max": 120, "sesso": Sex.F, "ar": 1.4, "pri": 1.7, "ai": None, "ul": 25},
]

# Vitamina B9 — Folato (ug DFE/die)
LARN_VITAMINA_B9: list[dict] = [
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.M, "ar": 320, "pri": 400, "ai": None, "ul": 1000},
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.F, "ar": 320, "pri": 400, "ai": None, "ul": 1000},
]

# Vitamina B12 — Cobalamina (ug/die)
LARN_VITAMINA_B12: list[dict] = [
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.M, "ar": 2.0, "pri": 2.4, "ai": None, "ul": None},
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.F, "ar": 2.0, "pri": 2.4, "ai": None, "ul": None},
]

# ---------------------------------------------------------------------------
# Minerali — valori in mg/die o ug/die
# ---------------------------------------------------------------------------

# Calcio (mg/die)
LARN_CALCIO: list[dict] = [
    {"eta_min": 18, "eta_max": 29, "sesso": Sex.M, "ar": 800, "pri": 1000, "ai": None, "ul": 2500},
    {"eta_min": 18, "eta_max": 29, "sesso": Sex.F, "ar": 800, "pri": 1000, "ai": None, "ul": 2500},
    {"eta_min": 30, "eta_max": 59, "sesso": Sex.M, "ar": 800, "pri": 1000, "ai": None, "ul": 2500},
    {"eta_min": 30, "eta_max": 59, "sesso": Sex.F, "ar": 800, "pri": 1000, "ai": None, "ul": 2500},
    {"eta_min": 60, "eta_max": 74, "sesso": Sex.M, "ar": 800, "pri": 1000, "ai": None, "ul": 2500},
    {"eta_min": 60, "eta_max": 74, "sesso": Sex.F, "ar": 1000, "pri": 1200, "ai": None, "ul": 2500},
    {"eta_min": 75, "eta_max": 120, "sesso": Sex.M, "ar": 800, "pri": 1000, "ai": None, "ul": 2500},
    {"eta_min": 75, "eta_max": 120, "sesso": Sex.F, "ar": 1000, "pri": 1200, "ai": None, "ul": 2500},
]

# Ferro (mg/die) — nota: donna fertile AR/PRI piu' alti per perdite mestruali
LARN_FERRO: list[dict] = [
    {"eta_min": 18, "eta_max": 29, "sesso": Sex.M, "ar": 7, "pri": 10, "ai": None, "ul": None},
    {"eta_min": 18, "eta_max": 29, "sesso": Sex.F, "ar": 10, "pri": 18, "ai": None, "ul": None},
    {"eta_min": 30, "eta_max": 59, "sesso": Sex.M, "ar": 7, "pri": 10, "ai": None, "ul": None},
    {"eta_min": 30, "eta_max": 59, "sesso": Sex.F, "ar": 10, "pri": 18, "ai": None, "ul": None},
    {"eta_min": 60, "eta_max": 74, "sesso": Sex.M, "ar": 7, "pri": 10, "ai": None, "ul": None},
    {"eta_min": 60, "eta_max": 74, "sesso": Sex.F, "ar": 7, "pri": 10, "ai": None, "ul": None},
    {"eta_min": 75, "eta_max": 120, "sesso": Sex.M, "ar": 7, "pri": 10, "ai": None, "ul": None},
    {"eta_min": 75, "eta_max": 120, "sesso": Sex.F, "ar": 7, "pri": 10, "ai": None, "ul": None},
]

# Zinco (mg/die)
LARN_ZINCO: list[dict] = [
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.M, "ar": 10, "pri": 12, "ai": None, "ul": 25},
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.F, "ar": 8, "pri": 9, "ai": None, "ul": 25},
]

# Magnesio (mg/die) — solo AI (no AR/PRI definiti LARN 2014)
LARN_MAGNESIO: list[dict] = [
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.M, "ar": None, "pri": None, "ai": 240, "ul": None},
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.F, "ar": None, "pri": None, "ai": 240, "ul": None},
]

# Fosforo (mg/die)
LARN_FOSFORO: list[dict] = [
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.M, "ar": 580, "pri": 700, "ai": None, "ul": None},
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.F, "ar": 580, "pri": 700, "ai": None, "ul": None},
]

# Potassio (mg/die) — solo AI
LARN_POTASSIO: list[dict] = [
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.M, "ar": None, "pri": None, "ai": 3900, "ul": None},
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.F, "ar": None, "pri": None, "ai": 3900, "ul": None},
]

# Selenio (ug/die)
LARN_SELENIO: list[dict] = [
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.M, "ar": 45, "pri": 55, "ai": None, "ul": 300},
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.F, "ar": 45, "pri": 55, "ai": None, "ul": 300},
]

# Sodio (mg/die) — solo AI + obiettivo SDT (Suggested Dietary Target)
LARN_SODIO: list[dict] = [
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.M, "ar": None, "pri": None, "ai": 1500, "ul": None},
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.F, "ar": None, "pri": None, "ai": 1500, "ul": None},
]
# SDT sodio: < 2000 mg/die (OMS) — gestito come warning nel validatore

# Fibra (g/die) — solo AI (LARN 2014: 25g/die)
LARN_FIBRA: list[dict] = [
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.M, "ar": None, "pri": None, "ai": 25, "ul": None},
    {"eta_min": 18, "eta_max": 120, "sesso": Sex.F, "ar": None, "pri": None, "ai": 25, "ul": None},
]

# ---------------------------------------------------------------------------
# Addendi gravidanza e allattamento (LARN 2014)
# nutriente → (delta_ar, delta_pri, delta_ai)
# ---------------------------------------------------------------------------

LARN_PREGNANCY_ADD: dict[str, tuple[float, float, float]] = {
    "proteine_g_kg":  (0.0, 0.0, 0.0),      # +1g/die I trim, +8 II, +26 III (gestito separato)
    "vitamina_a_ug":  (0, 100, 0),            # PRI +100
    "vitamina_d_ug":  (0, 0, 0),              # invariato
    "vitamina_c_mg":  (0, 10, 0),             # PRI +10
    "vitamina_b9_ug": (0, 200, 0),            # PRI 600 (da 400)
    "vitamina_b12_ug": (0.2, 0.2, 0),         # PRI 2.6
    "calcio_mg":      (0, 0, 0),              # invariato
    "ferro_mg":       (0, 9, 0),              # PRI 27
    "zinco_mg":       (1, 2, 0),              # PRI +2
    "selenio_ug":     (0, 5, 0),              # PRI 60
    "magnesio_mg":    (0, 0, 0),              # invariato
    "fosforo_mg":     (0, 0, 0),              # invariato
    "potassio_mg":    (0, 0, 0),              # invariato
}

LARN_LACTATION_ADD: dict[str, tuple[float, float, float]] = {
    "proteine_g_kg":  (0.0, 0.0, 0.0),       # +21g/die primi 6 mesi (gestito separato)
    "vitamina_a_ug":  (0, 350, 0),            # PRI +350
    "vitamina_d_ug":  (0, 0, 0),              # invariato
    "vitamina_c_mg":  (0, 30, 0),             # PRI +30
    "vitamina_b9_ug": (0, 100, 0),            # PRI 500
    "vitamina_b12_ug": (0.4, 0.4, 0),         # PRI 2.8
    "calcio_mg":      (0, 0, 0),              # invariato
    "ferro_mg":       (0, -7, 0),             # PRI 11 (calo da 18 per amenorrea)
    "zinco_mg":       (4, 3, 0),              # PRI +3
    "selenio_ug":     (0, 10, 0),             # PRI 65
    "magnesio_mg":    (0, 0, 0),              # invariato
    "fosforo_mg":     (0, 0, 0),              # invariato
    "potassio_mg":    (0, 0, 0),              # invariato
}


# ---------------------------------------------------------------------------
# Registro nutrienti — mappa campo DB → tabella LARN + unita' + label
# ---------------------------------------------------------------------------

NUTRIENT_REGISTRY: list[dict] = [
    {"campo_db": "calcio_mg",       "label": "Calcio",          "unita": "mg",  "tabella": LARN_CALCIO},
    {"campo_db": "ferro_mg",        "label": "Ferro",           "unita": "mg",  "tabella": LARN_FERRO},
    {"campo_db": "zinco_mg",        "label": "Zinco",           "unita": "mg",  "tabella": LARN_ZINCO},
    {"campo_db": "magnesio_mg",     "label": "Magnesio",        "unita": "mg",  "tabella": LARN_MAGNESIO},
    {"campo_db": "fosforo_mg",      "label": "Fosforo",         "unita": "mg",  "tabella": LARN_FOSFORO},
    {"campo_db": "potassio_mg",     "label": "Potassio",        "unita": "mg",  "tabella": LARN_POTASSIO},
    {"campo_db": "selenio_ug",      "label": "Selenio",         "unita": "ug",  "tabella": LARN_SELENIO},
    {"campo_db": "sodio_mg",        "label": "Sodio",           "unita": "mg",  "tabella": LARN_SODIO},
    {"campo_db": "fibra_g",         "label": "Fibra",           "unita": "g",   "tabella": LARN_FIBRA},
    {"campo_db": "vitamina_a_ug",   "label": "Vitamina A",      "unita": "ug",  "tabella": LARN_VITAMINA_A},
    {"campo_db": "vitamina_d_ug",   "label": "Vitamina D",      "unita": "ug",  "tabella": LARN_VITAMINA_D},
    {"campo_db": "vitamina_e_mg",   "label": "Vitamina E",      "unita": "mg",  "tabella": LARN_VITAMINA_E},
    {"campo_db": "vitamina_c_mg",   "label": "Vitamina C",      "unita": "mg",  "tabella": LARN_VITAMINA_C},
    {"campo_db": "vitamina_b1_mg",  "label": "Tiamina (B1)",    "unita": "mg",  "tabella": LARN_VITAMINA_B1},
    {"campo_db": "vitamina_b2_mg",  "label": "Riboflavina (B2)","unita": "mg",  "tabella": LARN_VITAMINA_B2},
    {"campo_db": "vitamina_b3_mg",  "label": "Niacina (B3)",    "unita": "mg",  "tabella": LARN_VITAMINA_B3},
    {"campo_db": "vitamina_b6_mg",  "label": "Piridossina (B6)","unita": "mg",  "tabella": LARN_VITAMINA_B6},
    {"campo_db": "vitamina_b9_ug",  "label": "Folato (B9)",     "unita": "ug",  "tabella": LARN_VITAMINA_B9},
    {"campo_db": "vitamina_b12_ug", "label": "Cobalamina (B12)","unita": "ug",  "tabella": LARN_VITAMINA_B12},
]


def lookup_larn(
    tabella: list[dict],
    eta: int,
    sesso: Sex,
) -> dict | None:
    """Cerca il riferimento LARN per eta' e sesso. Ritorna il primo match."""
    for entry in tabella:
        if (entry["eta_min"] <= eta <= entry["eta_max"]
                and entry["sesso"] == sesso):
            return entry
    return None
