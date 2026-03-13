"""
build_nutrition.py — Costruisce e popola nutrition.db con dati CREA 2019.

Crea da zero il database alimenti con:
  - 15 categorie alimentari (CREA 2019)
  - ~210 alimenti italiani con macro per 100g
  - Porzioni standard per gli alimenti principali

Fonte dati: CREA — Centro di Ricerca Alimenti e Nutrizione, 2019.
             Tabelle di Composizione degli Alimenti (IV edizione).
             https://www.alimentinutrizione.it/tabelle-di-composizione-degli-alimenti

Tutti i valori macro sono riferiti a 100g di prodotto edibile.

Utilizzo:
  python -m tools.admin_scripts.build_nutrition              # Costruisce nutrition.db
  python -m tools.admin_scripts.build_nutrition --dry-run    # Conta record senza scrivere
  python -m tools.admin_scripts.build_nutrition --reset      # Svuota e ricostruisce

Note:
  - Idempotente: non duplica record esistenti (check per nome categoria/alimento)
  - nutrition.db viene creato in data/nutrition.db
  - Compatible con l'installer (usa DATA_DIR da api/config.py)
"""

import argparse
import sys
from pathlib import Path

# Aggiungi root progetto al path per importare api.*
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import json

from api.config import NUTRITION_DATABASE_URL
from api.database import create_nutrition_tables, nutrition_engine
from api.models.nutrition import (
    FoodCategory, Food, PlanTemplate, StandardPortion,
    TemplatePlanComponent, TemplatePlanMeal,
)
from sqlmodel import Session, select


# ---------------------------------------------------------------------------
# Dati seed: categorie
# ---------------------------------------------------------------------------

CATEGORIES = [
    # (nome_it, nome_en, icona)
    ("Cereali e derivati", "Cereals and derivatives", "🌾"),
    ("Pasta, riso e cereali cotti", "Pasta, rice and cooked cereals", "🍝"),
    ("Pane e prodotti da forno", "Bread and bakery products", "🍞"),
    ("Legumi", "Legumes", "🫘"),
    ("Verdure e ortaggi", "Vegetables", "🥦"),
    ("Frutta fresca", "Fresh fruit", "🍎"),
    ("Frutta secca e semi", "Nuts and seeds", "🥜"),
    ("Carne e pollame", "Meat and poultry", "🥩"),
    ("Salumi e affettati", "Cured meats", "🥓"),
    ("Prodotti ittici", "Fish and seafood", "🐟"),
    ("Uova", "Eggs", "🥚"),
    ("Latte, yogurt e formaggi", "Dairy products", "🧀"),
    ("Oli e condimenti", "Oils and condiments", "🫒"),
    ("Dolci e zuccheri", "Sweets and sugars", "🍯"),
    ("Bevande e integratori", "Beverages and supplements", "🥛"),
]


# ---------------------------------------------------------------------------
# Dati seed: alimenti — 29 campi per 100g edibile
# Formato tupla:
#   (nome, cat_nome, kcal, prot, carb, gras, zucch, satur, fibra, sodio,
#    acqua, colest, calcio, ferro, zinco, magnesio, fosforo, potassio,
#    selenio, vit_a, vit_d, vit_e, vit_c, vit_b1, vit_b2, vit_b3,
#    vit_b6, vit_b9, vit_b12)
# Fonte: CREA 2019 / USDA FoodData Central. 0 = dato assente/trascurabile.
# ---------------------------------------------------------------------------

FOODS = [
    # ── Cereali e derivati ──────────────────────────────────────────────
    # (nome, cat, kcal, prot, carb, gras, zucch, satur, fibra, sodio, acqua, colest,
    #  calcio, ferro, zinco, mg, P, K, Se, vitA, vitD, vitE, vitC, B1, B2, B3, B6, B9, B12)
    ("Avena, fiocchi", "Cereali e derivati", 372, 13.2, 58.7, 7.1, 1.1, 1.3, 10.6, 6, 8.2, 0,
     54, 4.7, 3.6, 177, 523, 429, 28, 0, 0, 1.1, 0, 0.76, 0.14, 0.96, 0.12, 56, 0),
    ("Farro, crudo", "Cereali e derivati", 340, 14.7, 67.7, 2.5, 0.5, 0.4, 7.1, 3, 11.0, 0,
     22, 3.7, 3.3, 136, 420, 390, 37, 0, 0, 0.8, 0, 0.36, 0.11, 6.8, 0.26, 38, 0),
    ("Mais, farina gialla", "Cereali e derivati", 362, 9.2, 77.7, 3.8, 0.6, 0.5, 5.4, 5, 8.1, 0,
     7, 2.7, 1.8, 127, 241, 287, 15, 11, 0, 0.5, 0, 0.39, 0.20, 3.6, 0.37, 25, 0),
    ("Orzo perlato, crudo", "Cereali e derivati", 319, 10.0, 68.0, 1.0, 0.4, 0.2, 9.8, 4, 10.7, 0,
     29, 2.5, 2.1, 79, 221, 280, 38, 1, 0, 0.6, 0, 0.19, 0.11, 4.6, 0.26, 23, 0),
    ("Grano saraceno, crudo", "Cereali e derivati", 335, 13.3, 65.1, 3.4, 1.6, 0.7, 10.0, 2, 9.4, 0,
     18, 2.2, 2.4, 231, 347, 460, 8, 0, 0, 0.3, 0, 0.10, 0.43, 7.0, 0.21, 30, 0),
    ("Riso integrale, crudo", "Cereali e derivati", 330, 7.5, 68.5, 2.5, 0.4, 0.5, 3.5, 3, 12.4, 0,
     23, 1.5, 2.0, 143, 333, 223, 23, 0, 0, 1.2, 0, 0.41, 0.09, 5.1, 0.51, 20, 0),
    ("Quinoa, cruda", "Cereali e derivati", 368, 14.1, 64.2, 6.1, 2.7, 0.7, 7.0, 5, 13.3, 0,
     47, 4.6, 3.1, 197, 457, 563, 8, 1, 0, 2.4, 0, 0.36, 0.32, 1.5, 0.49, 184, 0),

    # ── Pasta, riso e cereali cotti ─────────────────────────────────────
    ("Pasta di semola, secca", "Pasta, riso e cereali cotti", 353, 12.9, 72.2, 1.5, 2.1, 0.3, 2.7, 5, 11.8, 0,
     21, 1.4, 1.4, 53, 189, 223, 63, 0, 0, 0.2, 0, 0.10, 0.04, 3.2, 0.14, 18, 0),
    ("Pasta di semola, cotta", "Pasta, riso e cereali cotti", 131, 4.9, 26.2, 0.5, 0.3, 0.1, 1.8, 1, 67.1, 0,
     7, 0.5, 0.5, 18, 58, 44, 26, 0, 0, 0.1, 0, 0.02, 0.02, 0.4, 0.05, 7, 0),
    ("Pasta integrale, secca", "Pasta, riso e cereali cotti", 340, 13.4, 67.3, 2.3, 2.0, 0.4, 9.0, 6, 10.9, 0,
     40, 3.6, 2.8, 128, 258, 407, 74, 0, 0, 0.5, 0, 0.49, 0.10, 5.1, 0.22, 44, 0),
    ("Pasta integrale, cotta", "Pasta, riso e cereali cotti", 124, 5.3, 23.5, 0.8, 0.5, 0.2, 3.9, 2, 67.5, 0,
     15, 1.4, 1.1, 47, 89, 117, 26, 0, 0, 0.2, 0, 0.16, 0.06, 1.6, 0.09, 13, 0),
    ("Riso bianco, crudo", "Pasta, riso e cereali cotti", 332, 6.5, 76.9, 0.4, 0.1, 0.1, 1.4, 3, 12.4, 0,
     9, 0.8, 1.1, 25, 115, 115, 15, 0, 0, 0.1, 0, 0.07, 0.05, 1.6, 0.16, 8, 0),
    ("Riso bianco, cotto", "Pasta, riso e cereali cotti", 138, 2.7, 31.9, 0.2, 0.0, 0.1, 0.6, 1, 65.1, 0,
     3, 0.2, 0.4, 12, 37, 35, 8, 0, 0, 0.0, 0, 0.02, 0.01, 0.4, 0.06, 3, 0),
    ("Riso integrale, cotto", "Pasta, riso e cereali cotti", 123, 2.7, 25.8, 1.0, 0.3, 0.2, 1.8, 2, 70.0, 0,
     10, 0.5, 0.6, 44, 83, 79, 10, 0, 0, 0.2, 0, 0.10, 0.02, 1.5, 0.15, 4, 0),
    ("Cous cous, cotto", "Pasta, riso e cereali cotti", 112, 3.8, 23.2, 0.2, 0.1, 0.0, 1.4, 5, 72.6, 0,
     8, 0.4, 0.3, 8, 22, 58, 28, 0, 0, 0.0, 0, 0.06, 0.02, 1.0, 0.05, 15, 0),
    ("Polenta, cotta", "Pasta, riso e cereali cotti", 84, 2.0, 17.8, 0.4, 0.2, 0.1, 1.2, 4, 79.0, 0,
     2, 0.5, 0.3, 11, 19, 25, 3, 3, 0, 0.1, 0, 0.04, 0.02, 0.3, 0.04, 3, 0),
    ("Farro, cotto", "Pasta, riso e cereali cotti", 147, 6.3, 27.8, 1.0, 0.3, 0.2, 3.9, 2, 64.2, 0,
     10, 1.5, 1.3, 50, 162, 149, 14, 0, 0, 0.3, 0, 0.14, 0.04, 2.6, 0.10, 14, 0),
    ("Quinoa, cotta", "Pasta, riso e cereali cotti", 120, 4.4, 21.3, 1.9, 0.9, 0.2, 2.8, 7, 72.0, 0,
     17, 1.5, 1.1, 64, 152, 172, 3, 0, 0, 0.6, 0, 0.11, 0.11, 0.4, 0.12, 42, 0),

    # ── Pane e prodotti da forno ────────────────────────────────────────
    ("Pane di frumento, bianco", "Pane e prodotti da forno", 270, 8.1, 53.8, 0.5, 2.7, 0.1, 3.8, 530, 35.5, 0,
     52, 1.2, 0.7, 25, 97, 115, 22, 0, 0, 0.1, 0, 0.09, 0.05, 1.5, 0.06, 28, 0),
    ("Pane integrale", "Pane e prodotti da forno", 224, 8.5, 40.6, 1.5, 3.5, 0.3, 6.5, 540, 42.7, 0,
     72, 2.5, 1.5, 65, 185, 230, 36, 0, 0, 0.3, 0, 0.22, 0.09, 3.8, 0.18, 42, 0),
    ("Pane di segale", "Pane e prodotti da forno", 258, 8.5, 48.3, 3.3, 3.8, 0.3, 5.8, 440, 33.9, 0,
     73, 2.8, 1.1, 40, 125, 166, 31, 1, 0, 0.3, 0, 0.43, 0.34, 3.4, 0.08, 51, 0),
    ("Crackers, classici", "Pane e prodotti da forno", 428, 10.1, 68.5, 12.5, 2.4, 1.6, 3.1, 790, 5.8, 0,
     30, 1.8, 0.8, 24, 120, 140, 20, 0, 0, 2.5, 0, 0.14, 0.10, 2.0, 0.04, 18, 0),
    ("Fiocchi di mais, cornflakes", "Pane e prodotti da forno", 357, 7.0, 84.1, 0.4, 7.7, 0.1, 2.8, 660, 3.8, 0,
     4, 6.7, 0.5, 15, 45, 100, 5, 0, 0, 0.1, 0, 0.36, 0.43, 5.0, 0.50, 167, 0),
    ("Gallette di riso", "Pane e prodotti da forno", 389, 8.0, 82.5, 3.1, 0.3, 0.7, 1.8, 30, 4.5, 0,
     5, 0.7, 1.3, 63, 102, 120, 18, 0, 0, 0.6, 0, 0.07, 0.03, 2.6, 0.12, 7, 0),
    ("Fette biscottate integrali", "Pane e prodotti da forno", 380, 10.9, 69.8, 5.6, 5.1, 0.9, 8.0, 460, 6.1, 0,
     50, 3.3, 1.9, 70, 200, 260, 34, 0, 0, 0.5, 0, 0.30, 0.10, 4.0, 0.16, 36, 0),

    # ── Legumi ───────────────────────────────────────────────────────────
    ("Ceci, cotti", "Legumi", 164, 8.4, 27.4, 2.6, 4.8, 0.3, 7.6, 24, 60.0, 0,
     49, 2.9, 1.5, 48, 168, 291, 3, 1, 0, 0.4, 1.3, 0.12, 0.06, 0.5, 0.14, 172, 0),
    ("Fagioli borlotti, cotti", "Legumi", 112, 7.5, 19.5, 0.5, 1.8, 0.1, 6.9, 5, 70.4, 0,
     41, 2.0, 1.0, 45, 130, 375, 1, 0, 0, 0.1, 0.9, 0.16, 0.06, 0.5, 0.10, 130, 0),
    ("Fagioli bianchi cannellini, cotti", "Legumi", 113, 7.3, 20.5, 0.5, 0.4, 0.1, 8.0, 6, 70.1, 0,
     65, 2.4, 1.0, 47, 113, 358, 1, 0, 0, 0.0, 0, 0.12, 0.05, 0.3, 0.09, 81, 0),
    ("Lenticchie, cotte", "Legumi", 116, 9.0, 20.1, 0.4, 1.8, 0.1, 7.9, 14, 68.0, 0,
     19, 3.3, 1.3, 36, 180, 369, 3, 1, 0, 0.1, 1.5, 0.17, 0.07, 1.1, 0.18, 181, 0),
    ("Piselli, surgelati cotti", "Legumi", 80, 5.4, 14.0, 0.4, 5.7, 0.1, 5.1, 115, 79.6, 0,
     25, 1.5, 1.0, 33, 108, 271, 2, 38, 0, 0.1, 14.2, 0.26, 0.10, 1.7, 0.15, 53, 0),
    ("Soia, semi cotti", "Legumi", 173, 16.6, 9.9, 9.0, 2.1, 1.3, 6.0, 2, 62.6, 0,
     102, 5.1, 1.2, 86, 245, 515, 7, 1, 0, 0.4, 1.7, 0.16, 0.29, 0.4, 0.23, 54, 0),
    ("Edamame, cotti", "Legumi", 122, 11.9, 8.9, 5.2, 2.2, 0.7, 5.2, 4, 72.8, 0,
     63, 2.3, 1.4, 64, 169, 436, 1, 9, 0, 0.7, 6.1, 0.20, 0.16, 1.0, 0.10, 311, 0),
    ("Fave, cotte", "Legumi", 110, 7.9, 18.3, 0.5, 3.8, 0.1, 5.4, 9, 71.5, 0,
     18, 1.5, 1.0, 43, 125, 268, 1, 3, 0, 0.1, 0.3, 0.10, 0.09, 0.7, 0.07, 104, 0),
    ("Ceci, secchi (crudi)", "Legumi", 334, 20.9, 54.3, 5.4, 10.7, 0.6, 17.4, 24, 10.7, 0,
     105, 6.2, 3.4, 115, 366, 875, 9, 3, 0, 0.8, 4.0, 0.48, 0.21, 1.5, 0.54, 557, 0),
    ("Lenticchie, secche (crude)", "Legumi", 319, 23.5, 55.8, 1.3, 2.0, 0.2, 10.7, 14, 10.7, 0,
     56, 7.5, 3.3, 77, 281, 677, 8, 2, 0, 0.5, 4.5, 0.87, 0.21, 2.6, 0.54, 479, 0),

    # ── Verdure e ortaggi ───────────────────────────────────────────────
    ("Spinaci, crudi", "Verdure e ortaggi", 23, 2.9, 3.6, 0.4, 0.4, 0.1, 2.2, 79, 91.4, 0,
     99, 2.7, 0.5, 79, 49, 558, 1, 469, 0, 2.0, 28.1, 0.08, 0.19, 0.7, 0.20, 194, 0),
    ("Broccoli, crudi", "Verdure e ortaggi", 31, 2.8, 5.2, 0.4, 1.7, 0.1, 2.6, 41, 88.2, 0,
     47, 0.7, 0.4, 21, 66, 316, 2, 31, 0, 0.8, 89.2, 0.07, 0.12, 0.6, 0.18, 63, 0),
    ("Broccoli, cotti", "Verdure e ortaggi", 36, 3.5, 5.0, 0.6, 1.4, 0.1, 3.3, 45, 89.2, 0,
     40, 0.7, 0.5, 21, 67, 293, 3, 77, 0, 1.5, 64.9, 0.06, 0.10, 0.5, 0.16, 108, 0),
    ("Pomodori, freschi", "Verdure e ortaggi", 20, 1.2, 3.9, 0.2, 2.6, 0.0, 1.2, 5, 93.5, 0,
     10, 0.3, 0.2, 11, 24, 237, 0, 42, 0, 0.5, 14.0, 0.04, 0.02, 0.6, 0.08, 15, 0),
    ("Zucchine", "Verdure e ortaggi", 17, 1.3, 2.5, 0.1, 1.7, 0.0, 1.0, 3, 94.8, 0,
     16, 0.4, 0.3, 18, 38, 261, 0, 10, 0, 0.1, 17.9, 0.04, 0.09, 0.5, 0.16, 24, 0),
    ("Carote", "Verdure e ortaggi", 40, 0.9, 9.3, 0.2, 4.7, 0.0, 2.8, 69, 88.3, 0,
     33, 0.3, 0.2, 12, 35, 320, 1, 835, 0, 0.7, 5.9, 0.07, 0.06, 1.0, 0.14, 19, 0),
    ("Peperoni rossi", "Verdure e ortaggi", 27, 1.0, 6.0, 0.3, 4.2, 0.0, 2.1, 4, 92.2, 0,
     7, 0.4, 0.3, 12, 26, 211, 0, 157, 0, 1.6, 127.7, 0.05, 0.09, 1.0, 0.29, 46, 0),
    ("Cetrioli", "Verdure e ortaggi", 12, 0.7, 2.2, 0.1, 1.7, 0.0, 0.5, 2, 96.7, 0,
     16, 0.3, 0.2, 13, 24, 147, 0, 5, 0, 0.0, 2.8, 0.03, 0.03, 0.1, 0.04, 7, 0),
    ("Lattuga, iceberg", "Verdure e ortaggi", 14, 1.4, 2.2, 0.2, 2.0, 0.0, 1.2, 10, 95.6, 0,
     18, 0.4, 0.2, 7, 20, 141, 0, 25, 0, 0.2, 2.8, 0.04, 0.03, 0.1, 0.04, 29, 0),
    ("Cavolo cappuccio", "Verdure e ortaggi", 25, 1.4, 5.0, 0.1, 2.6, 0.0, 2.5, 18, 92.2, 0,
     40, 0.5, 0.2, 12, 26, 170, 1, 5, 0, 0.2, 36.6, 0.06, 0.04, 0.2, 0.12, 43, 0),
    ("Asparagi", "Verdure e ortaggi", 20, 2.2, 3.9, 0.1, 1.9, 0.0, 2.1, 14, 92.4, 0,
     24, 2.1, 0.5, 14, 52, 202, 2, 38, 0, 1.1, 5.6, 0.14, 0.14, 1.0, 0.09, 52, 0),
    ("Fagiolini, cotti", "Verdure e ortaggi", 37, 2.2, 7.1, 0.2, 2.0, 0.0, 3.4, 6, 88.9, 0,
     37, 0.8, 0.3, 25, 38, 209, 1, 35, 0, 0.4, 12.2, 0.08, 0.10, 0.6, 0.07, 33, 0),
    ("Sedano", "Verdure e ortaggi", 15, 0.7, 2.9, 0.2, 1.8, 0.0, 1.8, 80, 95.4, 0,
     40, 0.2, 0.1, 11, 24, 260, 0, 22, 0, 0.3, 3.1, 0.02, 0.06, 0.3, 0.07, 36, 0),
    ("Melanzane", "Verdure e ortaggi", 24, 1.0, 5.7, 0.1, 2.4, 0.0, 3.4, 2, 92.0, 0,
     9, 0.2, 0.2, 14, 24, 229, 0, 1, 0, 0.3, 2.2, 0.04, 0.04, 0.6, 0.08, 22, 0),
    ("Carciofi", "Verdure e ortaggi", 47, 3.3, 9.5, 0.2, 1.0, 0.0, 5.7, 94, 84.9, 0,
     44, 1.3, 0.5, 60, 90, 370, 1, 13, 0, 0.2, 11.7, 0.07, 0.07, 1.0, 0.12, 68, 0),
    ("Funghi champignon, crudi", "Verdure e ortaggi", 22, 1.8, 3.3, 0.3, 1.9, 0.0, 1.0, 6, 93.5, 0,
     3, 0.5, 0.5, 9, 86, 318, 9, 0, 0.2, 0.0, 2.1, 0.08, 0.40, 3.6, 0.10, 17, 0.04),
    ("Cipolla", "Verdure e ortaggi", 40, 1.1, 9.3, 0.1, 4.2, 0.0, 1.7, 4, 89.1, 0,
     23, 0.2, 0.2, 10, 29, 146, 1, 0, 0, 0.0, 7.4, 0.05, 0.03, 0.1, 0.12, 19, 0),
    ("Cavolo nero", "Verdure e ortaggi", 35, 3.3, 5.0, 0.7, 1.0, 0.1, 4.1, 53, 89.6, 0,
     254, 1.6, 0.4, 33, 55, 348, 1, 241, 0, 0.9, 93.4, 0.05, 0.13, 1.0, 0.14, 62, 0),
    ("Finocchio", "Verdure e ortaggi", 31, 1.3, 6.9, 0.1, 4.1, 0.0, 3.1, 52, 90.2, 0,
     49, 0.7, 0.2, 17, 50, 414, 1, 7, 0, 0.6, 12.0, 0.01, 0.03, 0.6, 0.05, 27, 0),
    ("Bietola", "Verdure e ortaggi", 17, 1.6, 2.8, 0.2, 1.8, 0.0, 1.6, 213, 92.7, 0,
     51, 1.8, 0.4, 81, 46, 379, 1, 306, 0, 1.9, 30.0, 0.04, 0.09, 0.4, 0.09, 14, 0),
    ("Rucola", "Verdure e ortaggi", 25, 2.6, 2.0, 0.7, 2.0, 0.1, 1.6, 27, 91.7, 0,
     160, 1.5, 0.5, 47, 52, 369, 0, 119, 0, 0.4, 15.0, 0.04, 0.09, 0.3, 0.07, 97, 0),
    ("Radicchio", "Verdure e ortaggi", 23, 1.4, 4.5, 0.3, 0.3, 0.0, 3.1, 22, 92.2, 0,
     19, 0.6, 0.6, 13, 40, 302, 1, 27, 0, 2.3, 8.0, 0.02, 0.03, 0.3, 0.06, 60, 0),

    # ── Frutta fresca ───────────────────────────────────────────────────
    ("Mela, fresca", "Frutta fresca", 52, 0.3, 13.8, 0.2, 10.4, 0.0, 2.4, 1, 85.6, 0,
     6, 0.1, 0.0, 5, 11, 107, 0, 3, 0, 0.2, 4.6, 0.02, 0.03, 0.1, 0.04, 3, 0),
    ("Banana, fresca", "Frutta fresca", 89, 1.1, 22.8, 0.3, 12.2, 0.1, 2.6, 1, 74.9, 0,
     5, 0.3, 0.2, 27, 22, 358, 1, 3, 0, 0.1, 8.7, 0.03, 0.07, 0.7, 0.37, 20, 0),
    ("Arancia, fresca", "Frutta fresca", 47, 0.9, 11.8, 0.1, 9.4, 0.0, 2.4, 0, 86.8, 0,
     40, 0.1, 0.1, 10, 14, 181, 1, 11, 0, 0.2, 53.2, 0.09, 0.04, 0.3, 0.06, 30, 0),
    ("Pera, fresca", "Frutta fresca", 57, 0.4, 15.2, 0.1, 9.8, 0.0, 3.1, 1, 83.7, 0,
     9, 0.2, 0.1, 7, 12, 116, 0, 1, 0, 0.1, 4.3, 0.01, 0.03, 0.2, 0.03, 7, 0),
    ("Pesca, fresca", "Frutta fresca", 39, 0.9, 9.5, 0.1, 8.4, 0.0, 1.5, 0, 88.1, 0,
     6, 0.3, 0.2, 9, 20, 190, 0, 16, 0, 0.7, 6.6, 0.02, 0.03, 0.8, 0.03, 4, 0),
    ("Fragole, fresche", "Frutta fresca", 27, 0.8, 6.0, 0.3, 4.9, 0.0, 2.0, 1, 91.6, 0,
     16, 0.4, 0.1, 13, 24, 153, 0, 1, 0, 0.3, 58.8, 0.02, 0.02, 0.4, 0.05, 24, 0),
    ("Kiwi", "Frutta fresca", 61, 1.1, 14.6, 0.5, 9.0, 0.0, 3.0, 3, 83.1, 0,
     34, 0.3, 0.1, 17, 34, 312, 0, 4, 0, 1.5, 92.7, 0.03, 0.03, 0.3, 0.06, 25, 0),
    ("Avocado", "Frutta fresca", 160, 2.0, 8.5, 14.7, 0.7, 2.1, 6.7, 7, 73.2, 0,
     12, 0.6, 0.6, 29, 52, 485, 0, 7, 0, 2.1, 10.0, 0.07, 0.13, 1.7, 0.26, 81, 0),
    ("Uva, fresca", "Frutta fresca", 67, 0.6, 17.2, 0.4, 16.2, 0.1, 0.9, 2, 81.3, 0,
     10, 0.4, 0.1, 7, 20, 191, 0, 3, 0, 0.2, 3.2, 0.07, 0.07, 0.2, 0.09, 2, 0),
    ("Melone, fresco", "Frutta fresca", 34, 0.8, 8.2, 0.2, 7.9, 0.0, 0.9, 22, 90.2, 0,
     9, 0.2, 0.2, 12, 15, 267, 0, 169, 0, 0.1, 36.7, 0.04, 0.02, 0.7, 0.07, 21, 0),
    ("Anguria, fresca", "Frutta fresca", 30, 0.6, 7.6, 0.2, 6.2, 0.0, 0.4, 1, 91.5, 0,
     7, 0.2, 0.1, 10, 11, 112, 0, 28, 0, 0.1, 8.1, 0.03, 0.02, 0.2, 0.05, 3, 0),
    ("Mirtilli, freschi", "Frutta fresca", 57, 0.7, 14.5, 0.3, 10.0, 0.0, 2.4, 1, 84.2, 0,
     6, 0.3, 0.2, 6, 12, 77, 0, 3, 0, 0.6, 9.7, 0.04, 0.04, 0.4, 0.05, 6, 0),
    ("Ananas, fresco", "Frutta fresca", 50, 0.5, 13.1, 0.1, 9.9, 0.0, 1.4, 1, 86.0, 0,
     13, 0.3, 0.1, 12, 8, 109, 0, 3, 0, 0.0, 47.8, 0.08, 0.03, 0.5, 0.11, 18, 0),
    ("Pompelmo, fresco", "Frutta fresca", 42, 0.8, 10.7, 0.1, 6.9, 0.0, 1.7, 0, 88.1, 0,
     22, 0.1, 0.1, 9, 18, 135, 0, 46, 0, 0.1, 31.2, 0.04, 0.02, 0.2, 0.04, 13, 0),
    ("Limone", "Frutta fresca", 29, 1.1, 6.5, 0.6, 2.5, 0.1, 2.8, 2, 90.1, 0,
     26, 0.6, 0.1, 8, 16, 138, 0, 1, 0, 0.2, 53.0, 0.04, 0.02, 0.1, 0.08, 11, 0),

    # ── Frutta secca e semi ──────────────────────────────────────────────
    ("Mandorle", "Frutta secca e semi", 579, 21.2, 21.7, 49.9, 4.4, 3.8, 12.5, 1, 4.4, 0,
     269, 3.7, 3.1, 270, 481, 733, 4, 0, 0, 25.6, 0, 0.21, 1.14, 3.6, 0.14, 44, 0),
    ("Noci", "Frutta secca e semi", 654, 15.2, 13.7, 65.2, 2.6, 6.1, 6.7, 2, 4.1, 0,
     98, 2.9, 3.1, 158, 346, 441, 5, 1, 0, 0.7, 1.3, 0.34, 0.15, 1.1, 0.54, 98, 0),
    ("Anacardi", "Frutta secca e semi", 553, 18.2, 30.2, 43.9, 5.9, 7.8, 3.3, 12, 5.2, 0,
     37, 6.7, 5.8, 292, 593, 660, 20, 0, 0, 0.9, 0, 0.42, 0.06, 1.1, 0.42, 25, 0),
    ("Nocciole", "Frutta secca e semi", 628, 15.0, 16.7, 60.8, 4.3, 4.5, 9.7, 0, 5.3, 0,
     114, 4.7, 2.5, 163, 290, 680, 2, 1, 0, 15.0, 6.3, 0.64, 0.11, 1.8, 0.56, 113, 0),
    ("Pistacchi", "Frutta secca e semi", 560, 20.6, 27.2, 45.3, 7.7, 5.6, 10.6, 1, 4.0, 0,
     105, 3.9, 2.2, 121, 490, 1025, 7, 26, 0, 2.9, 5.6, 0.87, 0.16, 1.3, 1.70, 51, 0),
    ("Arachidi, tostate", "Frutta secca e semi", 567, 25.8, 16.1, 49.2, 4.0, 6.9, 8.5, 6, 1.6, 0,
     54, 1.5, 3.3, 168, 376, 705, 7, 0, 0, 8.3, 0, 0.44, 0.10, 12.1, 0.35, 240, 0),
    ("Semi di chia", "Frutta secca e semi", 486, 16.5, 42.1, 30.7, 0.0, 3.3, 34.4, 16, 5.8, 0,
     631, 7.7, 4.6, 335, 860, 407, 55, 0, 0, 0.5, 1.6, 0.62, 0.17, 8.8, 0.0, 49, 0),
    ("Semi di lino", "Frutta secca e semi", 534, 18.3, 28.9, 42.2, 1.5, 3.7, 27.3, 30, 6.9, 0,
     255, 5.7, 4.3, 392, 642, 813, 25, 0, 0, 0.3, 0.6, 1.64, 0.16, 3.1, 0.47, 87, 0),
    ("Semi di zucca", "Frutta secca e semi", 559, 30.2, 10.7, 49.1, 1.4, 8.7, 6.0, 7, 5.3, 0,
     46, 8.8, 7.8, 592, 1233, 809, 9, 1, 0, 2.2, 1.9, 0.27, 0.15, 5.0, 0.14, 58, 0),
    ("Semi di girasole", "Frutta secca e semi", 584, 20.8, 20.0, 51.5, 2.6, 4.5, 8.6, 9, 4.7, 0,
     78, 5.3, 5.0, 325, 660, 645, 53, 3, 0, 35.2, 1.4, 1.48, 0.36, 8.3, 1.35, 227, 0),

    # ── Carne e pollame ─────────────────────────────────────────────────
    ("Petto di pollo, crudo", "Carne e pollame", 110, 23.3, 0.0, 1.2, 0.0, 0.3, 0.0, 73, 74.9, 58,
     5, 0.4, 0.7, 29, 228, 370, 17, 6, 0.1, 0.3, 0, 0.07, 0.09, 12.4, 0.60, 4, 0.34),
    ("Petto di pollo, cotto al forno", "Carne e pollame", 165, 31.0, 0.0, 3.6, 0.0, 1.0, 0.0, 74, 64.0, 85,
     11, 0.7, 1.0, 29, 246, 256, 24, 7, 0.1, 0.3, 0, 0.06, 0.11, 13.7, 0.54, 4, 0.31),
    ("Coscia di pollo, cotta", "Carne e pollame", 232, 27.3, 0.0, 13.4, 0.0, 3.7, 0.0, 95, 59.4, 93,
     12, 1.0, 2.5, 23, 179, 240, 21, 18, 0.1, 0.3, 0, 0.07, 0.18, 6.7, 0.33, 7, 0.28),
    ("Petto di tacchino, crudo", "Carne e pollame", 107, 23.0, 0.0, 1.3, 0.0, 0.4, 0.0, 63, 74.0, 47,
     8, 0.7, 1.2, 30, 213, 340, 22, 0, 0.1, 0.1, 0, 0.06, 0.12, 10.5, 0.60, 8, 0.37),
    ("Petto di tacchino, cotto", "Carne e pollame", 157, 30.1, 0.0, 3.2, 0.0, 0.9, 0.0, 70, 64.7, 60,
     10, 1.0, 1.7, 28, 230, 293, 27, 0, 0.1, 0.1, 0, 0.04, 0.14, 8.0, 0.48, 6, 0.36),
    ("Manzo, fesa, cruda", "Carne e pollame", 105, 21.4, 0.0, 1.9, 0.0, 0.8, 0.0, 60, 75.3, 59,
     4, 2.1, 4.0, 24, 204, 355, 18, 0, 0, 0.2, 0, 0.07, 0.14, 5.8, 0.37, 10, 2.50),
    ("Manzo macinato magro 5%, crudo", "Carne e pollame", 137, 21.7, 0.0, 5.4, 0.0, 2.1, 0.0, 73, 71.4, 62,
     9, 2.3, 4.8, 21, 187, 318, 15, 0, 0, 0.2, 0, 0.04, 0.17, 5.1, 0.34, 8, 2.10),
    ("Vitello, scaloppina cruda", "Carne e pollame", 109, 21.0, 0.0, 2.6, 0.0, 1.0, 0.0, 78, 74.9, 70,
     6, 0.8, 3.1, 24, 200, 325, 9, 0, 0, 0.3, 0, 0.06, 0.21, 7.5, 0.28, 10, 1.10),
    ("Maiale, lonza cruda", "Carne e pollame", 122, 20.7, 0.0, 4.1, 0.0, 1.4, 0.0, 61, 73.8, 67,
     5, 0.6, 1.8, 24, 222, 384, 33, 2, 0.5, 0.2, 0.6, 0.91, 0.22, 5.0, 0.46, 3, 0.57),
    ("Maiale, filetto crudo", "Carne e pollame", 108, 22.4, 0.0, 2.2, 0.0, 0.8, 0.0, 58, 74.0, 62,
     5, 1.0, 2.0, 28, 246, 410, 41, 0, 0.5, 0.2, 0, 0.98, 0.34, 6.3, 0.63, 5, 0.60),
    ("Coniglio, cotto", "Carne e pollame", 179, 24.9, 0.0, 8.2, 0.0, 2.4, 0.0, 57, 65.2, 82,
     16, 1.6, 2.4, 21, 234, 343, 33, 0, 0, 0.2, 0, 0.04, 0.10, 7.0, 0.28, 8, 5.40),
    ("Fegato di manzo, crudo", "Carne e pollame", 133, 19.7, 3.8, 4.2, 1.9, 1.4, 0.0, 76, 71.2, 274,
     5, 4.9, 4.0, 18, 387, 313, 40, 9442, 1.2, 0.5, 1.3, 0.19, 2.76, 13.2, 1.08, 290, 59.3),
    ("Fegato di pollo, crudo", "Carne e pollame", 130, 19.0, 0.9, 5.5, 0.9, 1.7, 0.0, 81, 72.4, 345,
     8, 8.9, 2.7, 19, 297, 230, 55, 11078, 0.2, 0.7, 17.9, 0.31, 1.78, 9.7, 0.85, 588, 16.6),

    # ── Salumi e affettati ───────────────────────────────────────────────
    ("Bresaola", "Salumi e affettati", 151, 32.0, 0.3, 2.3, 0.0, 0.9, 0.0, 1800, 63.3, 74,
     7, 2.8, 5.0, 22, 216, 390, 11, 0, 0, 0.1, 0, 0.06, 0.28, 7.0, 0.30, 6, 2.00),
    ("Prosciutto crudo, magro", "Salumi e affettati", 158, 27.2, 0.0, 5.5, 0.0, 1.8, 0.0, 2580, 62.4, 73,
     6, 0.9, 2.2, 22, 240, 505, 22, 0, 0.1, 0.2, 0, 0.80, 0.17, 6.5, 0.52, 3, 0.80),
    ("Prosciutto cotto, magro", "Salumi e affettati", 124, 18.5, 1.5, 4.7, 1.1, 1.6, 0.0, 1140, 73.1, 58,
     7, 0.7, 1.7, 17, 228, 287, 19, 0, 0.3, 0.2, 0, 0.72, 0.19, 5.0, 0.32, 2, 0.60),
    ("Mortadella", "Salumi e affettati", 302, 14.7, 0.0, 26.7, 0.4, 9.9, 0.0, 1200, 58.1, 70,
     9, 1.4, 1.9, 14, 130, 225, 14, 0, 0, 0.2, 0, 0.18, 0.12, 4.0, 0.18, 2, 1.50),
    ("Salsiccia di maiale", "Salumi e affettati", 302, 14.3, 0.0, 27.0, 0.3, 9.9, 0.0, 870, 57.3, 80,
     11, 1.2, 2.4, 16, 148, 260, 18, 0, 0.5, 0.1, 0.7, 0.38, 0.17, 3.7, 0.24, 2, 0.90),
    ("Salame tipo Milano", "Salumi e affettati", 434, 21.4, 0.8, 39.0, 0.4, 14.5, 0.0, 1780, 33.0, 80,
     10, 1.5, 2.9, 18, 168, 340, 14, 0, 0.5, 0.1, 0, 0.50, 0.22, 5.5, 0.26, 2, 1.00),
    ("Speck", "Salumi e affettati", 234, 25.0, 0.9, 14.4, 0.6, 5.0, 0.0, 1840, 55.4, 76,
     6, 1.1, 2.5, 20, 230, 400, 15, 0, 0.2, 0.2, 0, 0.70, 0.20, 6.0, 0.42, 2, 0.90),

    # ── Prodotti ittici ──────────────────────────────────────────────────
    ("Salmone atlantico, crudo", "Prodotti ittici", 208, 20.4, 0.0, 13.4, 0.0, 3.1, 0.0, 59, 63.7, 63,
     12, 0.8, 0.6, 29, 240, 363, 37, 12, 11.0, 3.5, 0, 0.23, 0.38, 8.0, 0.64, 25, 3.18),
    ("Salmone, cotto al forno", "Prodotti ittici", 206, 25.4, 0.0, 10.9, 0.0, 2.5, 0.0, 69, 62.1, 70,
     15, 0.5, 0.6, 30, 252, 384, 42, 50, 14.0, 2.0, 0, 0.20, 0.15, 8.6, 0.64, 26, 3.05),
    ("Tonno in scatola al naturale", "Prodotti ittici", 103, 23.6, 0.0, 1.0, 0.0, 0.2, 0.0, 320, 74.8, 55,
     11, 1.3, 0.6, 26, 217, 237, 80, 6, 1.7, 0.5, 0, 0.02, 0.11, 10.2, 0.32, 4, 2.22),
    ("Tonno in scatola all'olio, sgocciolato", "Prodotti ittici", 184, 25.9, 0.0, 8.9, 0.0, 1.5, 0.0, 450, 64.5, 55,
     5, 1.0, 0.7, 25, 195, 207, 72, 18, 1.0, 2.5, 0, 0.03, 0.10, 10.0, 0.35, 5, 2.00),
    ("Merluzzo, filetto crudo", "Prodotti ittici", 82, 17.8, 0.0, 0.9, 0.0, 0.2, 0.0, 78, 80.3, 43,
     16, 0.4, 0.5, 32, 203, 413, 33, 12, 1.0, 0.6, 1.0, 0.08, 0.07, 2.1, 0.25, 7, 0.91),
    ("Branzino, cotto", "Prodotti ittici", 105, 20.5, 0.0, 2.7, 0.0, 0.5, 0.0, 72, 74.2, 63,
     15, 0.3, 0.5, 30, 210, 280, 36, 50, 4.0, 0.5, 2.0, 0.10, 0.08, 3.0, 0.30, 15, 3.00),
    ("Orata, cruda", "Prodotti ittici", 95, 20.1, 0.0, 1.7, 0.0, 0.5, 0.0, 79, 77.4, 57,
     20, 0.4, 0.4, 27, 215, 350, 38, 9, 5.0, 0.5, 0, 0.07, 0.06, 4.5, 0.35, 5, 1.50),
    ("Sgombro, crudo", "Prodotti ittici", 205, 18.7, 0.0, 13.9, 0.0, 3.3, 0.0, 90, 65.1, 70,
     12, 1.6, 0.6, 76, 217, 314, 44, 50, 16.1, 1.5, 0.4, 0.18, 0.31, 9.1, 0.40, 1, 8.71),
    ("Gamberi, cotti", "Prodotti ittici", 85, 18.0, 1.5, 0.9, 0.0, 0.2, 0.0, 566, 78.7, 152,
     52, 0.5, 1.6, 37, 214, 182, 40, 54, 0, 1.3, 0, 0.02, 0.02, 2.6, 0.10, 3, 1.11),
    ("Trota, cruda", "Prodotti ittici", 107, 20.8, 0.0, 2.7, 0.0, 0.7, 0.0, 50, 74.5, 58,
     67, 0.7, 0.5, 31, 245, 422, 13, 20, 4.0, 2.0, 2.4, 0.12, 0.11, 5.4, 0.40, 12, 4.45),
    ("Acciughe sott'olio, sgocciolate", "Prodotti ittici", 210, 28.9, 0.0, 10.0, 0.0, 2.1, 0.0, 3670, 58.2, 85,
     232, 4.6, 2.4, 69, 252, 383, 69, 15, 0, 1.0, 0, 0.06, 0.26, 14.0, 0.14, 10, 1.50),
    ("Pesce spada, crudo", "Prodotti ittici", 109, 17.0, 0.0, 4.2, 0.0, 1.1, 0.0, 98, 76.4, 39,
     5, 0.5, 0.7, 29, 217, 418, 52, 35, 14.0, 0.6, 0, 0.04, 0.10, 10.3, 0.32, 2, 1.80),
    ("Calamari, crudi", "Prodotti ittici", 92, 15.6, 3.1, 1.4, 0.0, 0.4, 0.0, 260, 79.3, 233,
     32, 0.7, 1.5, 33, 221, 246, 45, 10, 0, 1.2, 4.7, 0.02, 0.41, 2.2, 0.06, 5, 1.30),
    ("Polpo, cotto", "Prodotti ittici", 164, 29.8, 4.4, 2.1, 0.0, 0.5, 0.0, 450, 63.2, 96,
     53, 5.3, 1.7, 30, 195, 350, 45, 45, 0, 1.0, 0, 0.03, 0.04, 2.1, 0.36, 16, 20.0),
    ("Cod baccala' ammollato", "Prodotti ittici", 86, 19.5, 0.0, 0.5, 0.0, 0.1, 0.0, 220, 79.3, 57,
     18, 0.4, 0.5, 28, 195, 350, 30, 10, 0.8, 0.4, 1.0, 0.05, 0.05, 2.0, 0.20, 5, 0.80),

    # ── Uova ────────────────────────────────────────────────────────────
    ("Uovo intero, crudo", "Uova", 133, 12.4, 0.7, 8.7, 0.4, 2.7, 0.0, 126, 76.7, 371,
     50, 1.8, 1.3, 12, 198, 130, 31, 160, 2.0, 1.1, 0, 0.04, 0.46, 0.1, 0.17, 47, 0.89),
    ("Uovo intero, cotto sodo", "Uova", 147, 12.4, 0.7, 10.3, 0.4, 3.1, 0.0, 135, 74.6, 400,
     50, 1.2, 1.1, 10, 172, 126, 30, 149, 2.2, 1.0, 0, 0.07, 0.51, 0.1, 0.12, 44, 1.11),
    ("Albume d'uovo, crudo", "Uova", 52, 10.9, 0.7, 0.3, 0.6, 0.0, 0.0, 166, 87.6, 0,
     7, 0.1, 0.0, 11, 15, 163, 20, 0, 0, 0.0, 0, 0.00, 0.44, 0.1, 0.01, 4, 0.09),
    ("Tuorlo d'uovo, crudo", "Uova", 322, 16.0, 0.6, 27.8, 0.3, 8.1, 0.0, 48, 52.3, 1085,
     129, 2.7, 2.3, 5, 390, 109, 56, 381, 5.4, 2.6, 0, 0.18, 0.53, 0.0, 0.35, 146, 1.95),

    # ── Latte, yogurt e formaggi ─────────────────────────────────────────
    ("Latte intero, fresco", "Latte, yogurt e formaggi", 64, 3.3, 4.7, 3.6, 5.0, 2.1, 0.0, 44, 87.8, 13,
     113, 0.0, 0.4, 10, 84, 132, 2, 46, 1.3, 0.1, 0, 0.04, 0.18, 0.1, 0.04, 5, 0.44),
    ("Latte parzialmente scremato", "Latte, yogurt e formaggi", 49, 3.3, 4.8, 1.6, 5.0, 1.0, 0.0, 46, 89.6, 6,
     120, 0.0, 0.5, 11, 95, 150, 3, 22, 1.1, 0.0, 0, 0.04, 0.18, 0.1, 0.04, 5, 0.44),
    ("Latte scremato", "Latte, yogurt e formaggi", 36, 3.4, 5.0, 0.2, 5.0, 0.1, 0.0, 49, 91.0, 2,
     122, 0.0, 0.4, 11, 101, 156, 3, 1, 0.0, 0.0, 0, 0.04, 0.19, 0.1, 0.04, 5, 0.44),
    ("Yogurt intero bianco", "Latte, yogurt e formaggi", 73, 3.9, 4.9, 3.9, 4.9, 2.5, 0.0, 50, 87.2, 13,
     121, 0.1, 0.6, 12, 95, 155, 3, 27, 0.0, 0.1, 0.5, 0.03, 0.14, 0.1, 0.03, 7, 0.37),
    ("Yogurt greco 0% grassi", "Latte, yogurt e formaggi", 57, 10.0, 3.6, 0.4, 3.2, 0.3, 0.0, 36, 85.4, 5,
     110, 0.1, 0.5, 11, 135, 141, 10, 2, 0.0, 0.0, 0, 0.02, 0.27, 0.2, 0.06, 7, 0.75),
    ("Yogurt greco intero", "Latte, yogurt e formaggi", 97, 9.0, 3.6, 5.0, 3.2, 3.2, 0.0, 40, 81.1, 15,
     100, 0.1, 0.5, 11, 120, 141, 9, 36, 0.1, 0.1, 0, 0.02, 0.24, 0.2, 0.06, 7, 0.70),
    ("Mozzarella di bufala", "Latte, yogurt e formaggi", 253, 18.7, 0.7, 19.5, 0.4, 12.2, 0.0, 600, 59.1, 60,
     210, 0.2, 2.0, 15, 200, 90, 10, 153, 0.4, 0.3, 0, 0.02, 0.20, 0.2, 0.05, 10, 0.90),
    ("Mozzarella vaccina (fior di latte)", "Latte, yogurt e formaggi", 233, 17.1, 0.7, 17.8, 0.6, 11.1, 0.0, 500, 61.0, 56,
     505, 0.4, 2.8, 20, 354, 76, 17, 145, 0.4, 0.3, 0, 0.01, 0.24, 0.1, 0.04, 7, 1.00),
    ("Parmigiano reggiano", "Latte, yogurt e formaggi", 392, 33.0, 0.0, 28.1, 0.0, 18.0, 0.0, 700, 30.8, 90,
     1184, 0.8, 4.0, 38, 694, 92, 12, 207, 0.5, 0.3, 0, 0.03, 0.33, 0.3, 0.10, 10, 1.50),
    ("Grana padano", "Latte, yogurt e formaggi", 384, 33.3, 0.0, 27.6, 0.0, 17.7, 0.0, 650, 31.9, 90,
     1165, 0.5, 3.9, 37, 680, 107, 12, 224, 0.5, 0.3, 0, 0.02, 0.35, 0.1, 0.09, 10, 1.60),
    ("Ricotta di vaccino", "Latte, yogurt e formaggi", 146, 9.5, 2.7, 10.9, 2.7, 6.9, 0.0, 95, 73.0, 50,
     207, 0.4, 1.2, 11, 158, 105, 15, 120, 0.2, 0.1, 0, 0.01, 0.21, 0.1, 0.04, 12, 0.34),
    ("Fiocchi di latte (cottage cheese)", "Latte, yogurt e formaggi", 98, 10.7, 3.4, 4.4, 3.1, 2.8, 0.0, 364, 80.0, 15,
     83, 0.1, 0.4, 8, 159, 104, 9, 37, 0.1, 0.0, 0, 0.02, 0.16, 0.1, 0.05, 12, 0.63),
    ("Pecorino romano", "Latte, yogurt e formaggi", 387, 25.8, 0.2, 31.3, 0.1, 20.0, 0.0, 1200, 30.6, 93,
     1064, 0.8, 3.6, 30, 620, 86, 12, 174, 0.5, 0.3, 0, 0.04, 0.37, 0.3, 0.10, 10, 1.20),
    ("Scamorza", "Latte, yogurt e formaggi", 334, 26.9, 1.3, 24.4, 1.2, 15.4, 0.0, 860, 44.9, 79,
     594, 0.4, 3.0, 28, 435, 93, 14, 165, 0.4, 0.3, 0, 0.02, 0.22, 0.2, 0.04, 9, 1.00),
    ("Asiago", "Latte, yogurt e formaggi", 352, 28.5, 0.1, 26.1, 0.1, 16.5, 0.0, 770, 39.0, 85,
     929, 0.5, 3.5, 33, 562, 100, 12, 270, 0.3, 0.2, 0, 0.03, 0.36, 0.2, 0.07, 36, 1.40),
    ("Latte di soia", "Latte, yogurt e formaggi", 33, 3.3, 1.9, 1.8, 0.9, 0.2, 0.3, 51, 90.4, 0,
     25, 0.6, 0.3, 25, 52, 118, 5, 0, 1.1, 0.1, 0, 0.06, 0.07, 0.5, 0.04, 18, 0.42),

    # ── Oli e condimenti ─────────────────────────────────────────────────
    ("Olio di oliva extravergine", "Oli e condimenti", 884, 0.0, 0.0, 99.9, 0.0, 13.8, 0.0, 2, 0.2, 0,
     1, 0.6, 0.0, 0, 0, 1, 0, 0, 0, 14.4, 0, 0, 0, 0, 0, 0, 0),
    ("Olio di semi di girasole", "Oli e condimenti", 884, 0.0, 0.0, 100.0, 0.0, 10.1, 0.0, 0, 0.0, 0,
     0, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 41.1, 0, 0, 0, 0, 0, 0, 0),
    ("Olio di cocco", "Oli e condimenti", 892, 0.0, 0.0, 99.1, 0.0, 83.0, 0.0, 0, 0.0, 0,
     0, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0.1, 0, 0, 0, 0, 0, 0, 0),
    ("Burro", "Oli e condimenti", 758, 0.9, 0.8, 83.5, 0.7, 51.4, 0.0, 714, 14.0, 215,
     24, 0.0, 0.1, 2, 24, 24, 1, 684, 1.5, 2.3, 0, 0.01, 0.03, 0.0, 0.00, 3, 0.17),
    ("Salsa di pomodoro, passata", "Oli e condimenti", 35, 1.5, 7.0, 0.4, 5.4, 0.1, 1.5, 320, 90.5, 0,
     18, 0.8, 0.2, 19, 29, 330, 1, 30, 0, 1.3, 13.0, 0.04, 0.03, 1.1, 0.14, 13, 0),
    ("Aceto di vino rosso", "Oli e condimenti", 22, 0.0, 0.6, 0.0, 0.4, 0.0, 0.0, 8, 95.8, 0,
     6, 0.5, 0.0, 4, 8, 39, 1, 0, 0, 0.0, 0, 0, 0, 0, 0, 0, 0),
    ("Salsa di soia (tamari)", "Oli e condimenti", 53, 8.1, 4.9, 0.1, 2.0, 0.0, 0.0, 5480, 71.7, 0,
     20, 2.4, 0.4, 40, 130, 212, 1, 0, 0, 0.0, 0, 0.02, 0.16, 4.0, 0.20, 18, 0),

    # ── Dolci e zuccheri ─────────────────────────────────────────────────
    ("Zucchero bianco", "Dolci e zuccheri", 392, 0.0, 99.8, 0.0, 99.8, 0.0, 0.0, 0, 0.2, 0,
     1, 0.0, 0.0, 0, 0, 2, 1, 0, 0, 0.0, 0, 0, 0, 0, 0, 0, 0),
    ("Miele", "Dolci e zuccheri", 304, 0.3, 80.3, 0.0, 76.4, 0.0, 0.2, 4, 17.1, 0,
     6, 0.4, 0.2, 2, 4, 52, 1, 0, 0, 0.0, 0.5, 0, 0.04, 0.1, 0.02, 2, 0),
    ("Cioccolato fondente 70%", "Dolci e zuccheri", 598, 5.3, 45.9, 42.6, 28.0, 24.5, 11.9, 11, 1.0, 0,
     56, 8.0, 2.0, 146, 206, 559, 4, 0, 0, 0.6, 0, 0.03, 0.04, 0.7, 0.04, 12, 0),
    ("Cioccolato al latte", "Dolci e zuccheri", 534, 7.7, 59.4, 29.7, 57.1, 17.9, 1.5, 79, 1.0, 23,
     189, 2.3, 2.3, 63, 208, 372, 5, 60, 0, 0.5, 0, 0.11, 0.30, 0.4, 0.04, 12, 0.39),
    ("Marmellata, media", "Dolci e zuccheri", 265, 0.5, 68.0, 0.1, 55.0, 0.0, 1.2, 15, 30.0, 0,
     20, 0.5, 0.1, 4, 11, 55, 1, 3, 0, 0.2, 8.0, 0.01, 0.02, 0.1, 0.02, 3, 0),
    ("Sciroppo d'acero", "Dolci e zuccheri", 260, 0.0, 67.0, 0.1, 59.5, 0.0, 0.0, 9, 32.4, 0,
     102, 0.1, 1.5, 21, 2, 212, 1, 0, 0, 0.0, 0, 0.01, 0.01, 0.1, 0.00, 0, 0),

    # ── Bevande e integratori ────────────────────────────────────────────
    ("Latte di mandorla, non zuccherato", "Bevande e integratori", 24, 0.6, 3.0, 1.1, 0.4, 0.1, 0.3, 72, 94.4, 0,
     184, 0.3, 0.1, 7, 9, 67, 0, 0, 0, 3.3, 0, 0, 0.01, 0.1, 0.01, 1, 0),
    ("Succo d'arancia, fresco", "Bevande e integratori", 45, 0.7, 10.4, 0.2, 8.4, 0.0, 0.2, 1, 88.3, 0,
     11, 0.2, 0.1, 11, 17, 200, 0, 10, 0, 0.0, 50.0, 0.09, 0.03, 0.4, 0.04, 30, 0),
    ("Latte di riso", "Bevande e integratori", 47, 0.3, 9.2, 1.0, 4.4, 0.1, 0.3, 39, 89.2, 0,
     118, 0.2, 0.1, 11, 56, 27, 3, 0, 1.0, 0.0, 0, 0.03, 0.01, 0.4, 0.01, 2, 0.38),
    ("Latte di avena", "Bevande e integratori", 46, 1.0, 7.9, 1.5, 3.6, 0.2, 0.8, 44, 88.7, 0,
     120, 0.3, 0.1, 5, 42, 43, 3, 0, 1.0, 0.0, 0, 0.08, 0.21, 0.2, 0.01, 2, 0.38),
    ("Caffè espresso, senza zucchero", "Bevande e integratori", 2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 2, 97.3, 0,
     2, 0.1, 0.0, 80, 7, 115, 0, 0, 0, 0.0, 0, 0, 0.18, 5.2, 0, 1, 0),
    ("Whey protein isolate (polvere)", "Bevande e integratori", 375, 90.0, 4.5, 1.5, 2.0, 1.0, 0.0, 150, 3.0, 5,
     100, 0.5, 0.8, 20, 130, 160, 15, 0, 0, 0.0, 0, 0.04, 0.15, 0.1, 0.03, 5, 0.50),
    ("Creatina monoidrato (polvere)", "Bevande e integratori", 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    ("BCAA, polvere", "Bevande e integratori", 400, 95.0, 2.0, 2.0, 0.0, 0.0, 0.0, 20, 1.0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
]


# ---------------------------------------------------------------------------
# Porzioni standard — (nome_alimento, nome_porzione, grammi)
# ---------------------------------------------------------------------------

PORTIONS = [
    # Pasta / riso
    ("Pasta di semola, secca", "1 porzione (cruda)", 80),
    ("Pasta di semola, secca", "1 porzione abbondante (cruda)", 100),
    ("Pasta di semola, cotta", "1 piatto (cotto)", 200),
    ("Pasta integrale, secca", "1 porzione (cruda)", 80),
    ("Riso bianco, crudo", "1 porzione (crudo)", 70),
    ("Riso bianco, cotto", "1 piatto (cotto)", 180),
    ("Farro, crudo", "1 porzione (crudo)", 70),
    ("Quinoa, cotta", "1 porzione (cotta)", 150),

    # Pane
    ("Pane di frumento, bianco", "1 fetta", 35),
    ("Pane di frumento, bianco", "1 panino piccolo", 80),
    ("Pane integrale", "1 fetta", 35),
    ("Gallette di riso", "1 galletta", 10),

    # Carni e pesce
    ("Petto di pollo, crudo", "1 petto piccolo", 130),
    ("Petto di pollo, crudo", "1 petto grande", 200),
    ("Uovo intero, crudo", "1 uovo medio", 55),
    ("Uovo intero, crudo", "1 uovo grande", 65),
    ("Albume d'uovo, crudo", "1 albume medio", 35),
    ("Tonno in scatola al naturale", "1 lattina (sgocciolata)", 80),
    ("Salmone atlantico, crudo", "1 porzione", 150),

    # Latticini
    ("Latte intero, fresco", "1 bicchiere", 200),
    ("Latte parzialmente scremato", "1 bicchiere", 200),
    ("Yogurt intero bianco", "1 vasetto standard", 125),
    ("Yogurt greco 0% grassi", "1 vasetto standard", 150),
    ("Parmigiano reggiano", "1 cucchiaio grattugiato", 10),
    ("Parmigiano reggiano", "1 porzione (scaglie)", 30),
    ("Mozzarella di bufala", "1 mozzarella piccola", 125),
    ("Mozzarella vaccina (fior di latte)", "1 mozzarella piccola", 100),
    ("Ricotta di vaccino", "1 cucchiaio colmo", 50),

    # Frutta
    ("Mela, fresca", "1 mela media", 150),
    ("Banana, fresca", "1 banana media", 120),
    ("Arancia, fresca", "1 arancia media", 150),
    ("Pera, fresca", "1 pera media", 160),
    ("Fragole, fresche", "1 porzione", 150),
    ("Avocado", "1/2 avocado", 70),
    ("Avocado", "1 avocado intero", 140),

    # Frutta secca
    ("Mandorle", "1 manciata (30 pz)", 30),
    ("Noci", "3 noci", 30),
    ("Anacardi", "1 manciata", 30),

    # Oli e condimenti
    ("Olio di oliva extravergine", "1 cucchiaio", 10),
    ("Olio di oliva extravergine", "1 cucchiaino", 5),
    ("Burro", "1 noce", 10),

    # Legumi
    ("Ceci, cotti", "1 porzione", 150),
    ("Lenticchie, cotte", "1 porzione", 150),
    ("Fagioli borlotti, cotti", "1 porzione", 150),

    # Dolci
    ("Miele", "1 cucchiaino", 10),
    ("Miele", "1 cucchiaio", 20),
    ("Cioccolato fondente 70%", "1 quadratino", 10),
    ("Cioccolato fondente 70%", "2 quadratini", 20),
]


# ---------------------------------------------------------------------------
# Core build functions
# ---------------------------------------------------------------------------


def build_nutrition_db(dry_run: bool = False, reset: bool = False) -> None:
    """Costruisce e popola nutrition.db."""
    print(f"Nutrition DB: {NUTRITION_DATABASE_URL}")

    create_nutrition_tables()
    print("  Tabelle create (o già esistenti).")

    if reset and not dry_run:
        # Svuota tabelle in ordine inverso (FK)
        with Session(nutrition_engine) as s:
            s.exec(TemplatePlanComponent.__table__.delete())
            s.exec(TemplatePlanMeal.__table__.delete())
            s.exec(PlanTemplate.__table__.delete())
            s.exec(StandardPortion.__table__.delete())
            s.exec(Food.__table__.delete())
            s.exec(FoodCategory.__table__.delete())
            s.commit()
        print("  [RESET] Tabelle svuotate.")

    with Session(nutrition_engine) as session:
        # ── Categorie ──────────────────────────────────────────────
        cat_map: dict[str, int] = {}
        inserted_cats = 0
        for nome, nome_en, icona in CATEGORIES:
            existing = session.exec(
                select(FoodCategory).where(FoodCategory.nome == nome)
            ).first()
            if existing:
                cat_map[nome] = existing.id
            else:
                if not dry_run:
                    cat = FoodCategory(nome=nome, nome_en=nome_en, icona=icona)
                    session.add(cat)
                    session.flush()
                    cat_map[nome] = cat.id
                inserted_cats += 1

        if not dry_run:
            session.commit()

        print(f"  Categorie: {len(CATEGORIES)} totali, {inserted_cats} nuove inserite.")

        # Ricarica mappa dopo commit
        if not dry_run:
            all_cats = session.exec(select(FoodCategory)).all()
            cat_map = {c.nome: c.id for c in all_cats}

        # ── Alimenti ───────────────────────────────────────────────
        inserted_foods = 0
        food_id_map: dict[str, int] = {}  # nome → id

        for row in FOODS:
            (nome, cat_nome, kcal, prot, carb, gras, zucch, satur, fibra,
             sodio, acqua, colest, calcio, ferro, zinco, magnesio, fosforo,
             potassio, selenio, vit_a, vit_d, vit_e, vit_c, vit_b1, vit_b2,
             vit_b3, vit_b6, vit_b9, vit_b12) = row

            existing = session.exec(
                select(Food).where(Food.nome == nome)
            ).first()
            if existing:
                food_id_map[nome] = existing.id
                continue

            cat_id = cat_map.get(cat_nome)
            if not cat_id:
                print(f"  [WARN] Categoria non trovata: '{cat_nome}' per '{nome}'")
                continue

            _n = lambda v: v or None  # noqa: E731 — 0 → None
            _pos = lambda v: v if v and v > 0 else None  # noqa: E731

            if not dry_run:
                food = Food(
                    nome=nome,
                    categoria_id=cat_id,
                    energia_kcal=kcal,
                    proteine_g=prot,
                    carboidrati_g=carb,
                    grassi_g=gras,
                    di_cui_zuccheri_g=_n(zucch),
                    di_cui_saturi_g=_n(satur),
                    fibra_g=_n(fibra),
                    sodio_mg=_n(sodio),
                    acqua_g=_n(acqua),
                    colesterolo_mg=_pos(colest),
                    calcio_mg=_n(calcio),
                    ferro_mg=_n(ferro),
                    zinco_mg=_n(zinco),
                    magnesio_mg=_n(magnesio),
                    fosforo_mg=_n(fosforo),
                    potassio_mg=_n(potassio),
                    selenio_ug=_n(selenio),
                    vitamina_a_ug=_n(vit_a),
                    vitamina_d_ug=_n(vit_d),
                    vitamina_e_mg=_n(vit_e),
                    vitamina_c_mg=_n(vit_c),
                    vitamina_b1_mg=_n(vit_b1),
                    vitamina_b2_mg=_n(vit_b2),
                    vitamina_b3_mg=_n(vit_b3),
                    vitamina_b6_mg=_n(vit_b6),
                    vitamina_b9_ug=_n(vit_b9),
                    vitamina_b12_ug=_n(vit_b12),
                    source="crea",
                )
                session.add(food)
                session.flush()
                food_id_map[nome] = food.id
            inserted_foods += 1

        if not dry_run:
            session.commit()

        print(f"  Alimenti: {len(FOODS)} totali, {inserted_foods} nuovi inseriti.")

        # Ricarica mappa food dopo commit
        if not dry_run:
            all_foods = session.exec(select(Food)).all()
            food_id_map = {f.nome: f.id for f in all_foods}

        # ── Porzioni standard ──────────────────────────────────────
        inserted_portions = 0
        for alimento_nome, porz_nome, grammi in PORTIONS:
            food_id = food_id_map.get(alimento_nome)
            if not food_id:
                print(f"  [WARN] Alimento non trovato per porzione: '{alimento_nome}'")
                continue

            existing = session.exec(
                select(StandardPortion).where(
                    StandardPortion.alimento_id == food_id,
                    StandardPortion.nome == porz_nome,
                )
            ).first()
            if existing:
                continue

            if not dry_run:
                p = StandardPortion(
                    alimento_id=food_id,
                    nome=porz_nome,
                    grammi=grammi,
                )
                session.add(p)
            inserted_portions += 1

        if not dry_run:
            session.commit()

        print(f"  Porzioni standard: {len(PORTIONS)} totali, {inserted_portions} nuove inserite.")

        # ── Template piani ────────────────────────────────────────────
        _seed_templates(session, food_id_map, dry_run)

    if dry_run:
        print("\n  [DRY RUN] Nessuna modifica eseguita.")
    else:
        print("\n  nutrition.db pronto.")
        _print_stats()


# ---------------------------------------------------------------------------
# Template piani — 8 profili macro + 1 dieta completa (donna_under30_attiva)
# ---------------------------------------------------------------------------

PLAN_TEMPLATES = [
    {
        "slug": "uomo_under30_sedentario",
        "nome": "Uomo under 30 — Sedentario",
        "descrizione": "Ufficio/studio, <3h attivita' fisica a settimana",
        "tags": ["uomo", "under30", "sedentario"],
        "obiettivo_calorico": 1900,
        "proteine_g_target": 140,
        "carboidrati_g_target": 220,
        "grassi_g_target": 65,
        "note_cliniche": (
            "Profilo sedentario maschile under 30. "
            "Priorita': mantenimento massa muscolare con deficit moderato. "
            "P 1.6g/kg (70kg), C ~45% kcal, G ~30% kcal. "
            "Colazione + pranzo + cena + 1 spuntino pomeriggio."
        ),
    },
    {
        "slug": "uomo_under30_attivo",
        "nome": "Uomo under 30 — Attivo",
        "descrizione": "3-5 sessioni allenamento a settimana",
        "tags": ["uomo", "under30", "attivo"],
        "obiettivo_calorico": 2400,
        "proteine_g_target": 175,
        "carboidrati_g_target": 290,
        "grassi_g_target": 80,
        "note_cliniche": (
            "Profilo attivo maschile under 30. "
            "P 2.0g/kg (87kg), C ~48% kcal per sostenere le sessioni, G ~30% kcal. "
            "Pre e post-workout consigliati nei giorni di allenamento."
        ),
    },
    {
        "slug": "uomo_under30_sportivo",
        "nome": "Uomo under 30 — Sportivo",
        "descrizione": "Atleta o >5 sessioni intense a settimana",
        "tags": ["uomo", "under30", "sportivo"],
        "obiettivo_calorico": 2900,
        "proteine_g_target": 210,
        "carboidrati_g_target": 360,
        "grassi_g_target": 85,
        "note_cliniche": (
            "Profilo agonistico maschile under 30. "
            "P 2.2g/kg, C elevati per performance e recupero, G moderati. "
            "6 pasti giornalieri consigliati. Pre/post-workout obbligatori."
        ),
    },
    {
        "slug": "uomo_over30_mantenimento",
        "nome": "Uomo over 30 — Mantenimento",
        "descrizione": "Adulto attivo, obiettivo composizione corporea",
        "tags": ["uomo", "over30", "attivo"],
        "obiettivo_calorico": 2200,
        "proteine_g_target": 170,
        "carboidrati_g_target": 240,
        "grassi_g_target": 75,
        "note_cliniche": (
            "Profilo maschile over 30 con metabolismo rallentato. "
            "Proteina elevata per prevenire catabolismo muscolare (eta'-dipendente). "
            "P 2.0g/kg, C moderati, G 30% kcal. Timing post-workout critico."
        ),
    },
    {
        "slug": "donna_under30_sedentaria",
        "nome": "Donna under 30 — Sedentaria",
        "descrizione": "Ufficio/studio, <2h attivita' fisica a settimana",
        "tags": ["donna", "under30", "sedentaria"],
        "obiettivo_calorico": 1500,
        "proteine_g_target": 110,
        "carboidrati_g_target": 175,
        "grassi_g_target": 52,
        "note_cliniche": (
            "Profilo sedentario femminile under 30. "
            "Deficit calorico moderato per dimagrimento controllato. "
            "P 1.8g/kg (61kg), C ~46% kcal, G ~31% kcal. "
            "Attenzione al ferro e calcio. Colazione sostanziosa consigliata."
        ),
    },
    {
        "slug": "donna_under30_attiva",
        "nome": "Donna under 30 — Attiva",
        "descrizione": "3-4 sessioni allenamento a settimana",
        "tags": ["donna", "under30", "attiva"],
        "obiettivo_calorico": 1900,
        "proteine_g_target": 140,
        "carboidrati_g_target": 220,
        "grassi_g_target": 65,
        "note_cliniche": (
            "Profilo attivo femminile under 30. "
            "Bilanciato per supportare l'allenamento e la composizione corporea. "
            "P 2.0g/kg, C ~46% kcal. Pre/post-workout leggeri nei giorni di allenamento. "
            "Monitorare ferro e vitamina D."
        ),
    },
    {
        "slug": "donna_under30_sportiva",
        "nome": "Donna under 30 — Sportiva",
        "descrizione": "Atleta o >5 sessioni intensive a settimana",
        "tags": ["donna", "under30", "sportiva"],
        "obiettivo_calorico": 2300,
        "proteine_g_target": 165,
        "carboidrati_g_target": 280,
        "grassi_g_target": 72,
        "note_cliniche": (
            "Profilo agonistico femminile under 30. "
            "Apporto calorico adeguato a prevenire RED-S (Relative Energy Deficiency in Sport). "
            "P 2.2g/kg, C elevati, G 28% kcal. 5-6 pasti. "
            "Integrazione ferro e calcio da valutare."
        ),
    },
    {
        "slug": "donna_over30_mantenimento",
        "nome": "Donna over 30 — Mantenimento",
        "descrizione": "Adulta attiva, obiettivo benessere e composizione",
        "tags": ["donna", "over30", "attiva"],
        "obiettivo_calorico": 1750,
        "proteine_g_target": 135,
        "carboidrati_g_target": 195,
        "grassi_g_target": 60,
        "note_cliniche": (
            "Profilo femminile over 30. Metabolismo basale in calo, "
            "proteina elevata per preservare la massa muscolare. "
            "P 2.0g/kg, C 44% kcal, G 31% kcal. "
            "Particolare attenzione a calcio e vitamina D per salute ossea."
        ),
    },
]

# Dieta settimanale completa per "donna_under30_attiva" (~1900 kcal/die)
# Struttura: (giorno 1-7, tipo_pasto, ordine, [(alimento_nome, grammi_g), ...])
DIETA_DONNA_ATTIVA = [
    # ── Lunedi (giorno 1) ───────────────────────────────────────────────
    (1, "COLAZIONE", 0, [
        ("Yogurt greco 0% grassi", 150),
        ("Avena, fiocchi", 40),
        ("Mirtilli, freschi", 80),
        ("Mandorle", 15),
    ]),
    (1, "SPUNTINO_MATTINA", 1, [
        ("Mela, fresca", 150),
    ]),
    (1, "PRANZO", 2, [
        ("Petto di pollo, crudo", 150),
        ("Riso integrale, cotto", 180),
        ("Zucchine", 200),
        ("Olio di oliva extravergine", 10),
    ]),
    (1, "SPUNTINO_POMERIGGIO", 3, [
        ("Yogurt greco 0% grassi", 125),
        ("Noci", 15),
    ]),
    (1, "CENA", 4, [
        ("Salmone atlantico, crudo", 150),
        ("Spinaci, crudi", 150),
        ("Pane integrale", 40),
        ("Olio di oliva extravergine", 10),
    ]),
    # ── Martedi (giorno 2) ──────────────────────────────────────────────
    (2, "COLAZIONE", 0, [
        ("Latte parzialmente scremato", 200),
        ("Avena, fiocchi", 40),
        ("Banana, fresca", 100),
        ("Semi di chia", 10),
    ]),
    (2, "SPUNTINO_MATTINA", 1, [
        ("Arancia, fresca", 150),
    ]),
    (2, "PRANZO", 2, [
        ("Pasta integrale, secca", 80),
        ("Lenticchie, cotte", 150),
        ("Pomodori, freschi", 100),
        ("Olio di oliva extravergine", 10),
    ]),
    (2, "SPUNTINO_POMERIGGIO", 3, [
        ("Fiocchi di latte (cottage cheese)", 100),
        ("Crackers, classici", 20),
    ]),
    (2, "CENA", 4, [
        ("Merluzzo, filetto crudo", 180),
        ("Broccoli, cotti", 200),
        ("Pane di frumento, bianco", 40),
        ("Olio di oliva extravergine", 10),
    ]),
    # ── Mercoledi (giorno 3) ────────────────────────────────────────────
    (3, "COLAZIONE", 0, [
        ("Yogurt greco 0% grassi", 150),
        ("Avena, fiocchi", 40),
        ("Fragole, fresche", 120),
        ("Nocciole", 15),
    ]),
    (3, "SPUNTINO_MATTINA", 1, [
        ("Pera, fresca", 150),
    ]),
    (3, "PRANZO", 2, [
        ("Petto di tacchino, crudo", 150),
        ("Farro, cotto", 180),
        ("Peperoni rossi", 150),
        ("Olio di oliva extravergine", 10),
    ]),
    (3, "SPUNTINO_POMERIGGIO", 3, [
        ("Banana, fresca", 100),
        ("Mandorle", 15),
    ]),
    (3, "CENA", 4, [
        ("Uovo intero, crudo", 120),  # 2 uova
        ("Asparagi", 200),
        ("Pane integrale", 40),
        ("Olio di oliva extravergine", 10),
    ]),
    # ── Giovedi (giorno 4) ──────────────────────────────────────────────
    (4, "COLAZIONE", 0, [
        ("Latte parzialmente scremato", 200),
        ("Fette biscottate integrali", 40),
        ("Miele", 15),
        ("Noci", 15),
    ]),
    (4, "SPUNTINO_MATTINA", 1, [
        ("Kiwi", 120),
    ]),
    (4, "PRANZO", 2, [
        ("Tonno in scatola al naturale", 120),
        ("Quinoa, cotta", 180),
        ("Pomodori, freschi", 150),
        ("Olio di oliva extravergine", 10),
    ]),
    (4, "SPUNTINO_POMERIGGIO", 3, [
        ("Yogurt greco 0% grassi", 125),
        ("Mirtilli, freschi", 60),
    ]),
    (4, "CENA", 4, [
        ("Manzo, fesa, cruda", 140),
        ("Fagiolini, cotti", 200),
        ("Pane di frumento, bianco", 40),
        ("Olio di oliva extravergine", 10),
    ]),
    # ── Venerdi (giorno 5) ──────────────────────────────────────────────
    (5, "COLAZIONE", 0, [
        ("Yogurt greco 0% grassi", 150),
        ("Avena, fiocchi", 40),
        ("Banana, fresca", 100),
        ("Semi di lino", 10),
    ]),
    (5, "SPUNTINO_MATTINA", 1, [
        ("Mandorle", 20),
    ]),
    (5, "PRANZO", 2, [
        ("Pasta di semola, secca", 80),
        ("Gamberi, cotti", 150),
        ("Zucchine", 150),
        ("Olio di oliva extravergine", 10),
    ]),
    (5, "SPUNTINO_POMERIGGIO", 3, [
        ("Mela, fresca", 150),
        ("Ricotta di vaccino", 50),
    ]),
    (5, "CENA", 4, [
        ("Orata, cruda", 180),
        ("Carote", 150),
        ("Lattuga, iceberg", 100),
        ("Pane integrale", 40),
        ("Olio di oliva extravergine", 10),
    ]),
    # ── Sabato (giorno 6) ───────────────────────────────────────────────
    (6, "COLAZIONE", 0, [
        ("Yogurt greco intero", 150),
        ("Avena, fiocchi", 35),
        ("Miele", 10),
        ("Fragole, fresche", 100),
    ]),
    (6, "SPUNTINO_MATTINA", 1, [
        ("Arancia, fresca", 150),
    ]),
    (6, "PRANZO", 2, [
        ("Ceci, cotti", 200),
        ("Riso integrale, cotto", 160),
        ("Spinaci, crudi", 100),
        ("Olio di oliva extravergine", 10),
    ]),
    (6, "SPUNTINO_POMERIGGIO", 3, [
        ("Fiocchi di latte (cottage cheese)", 100),
        ("Gallette di riso", 20),
    ]),
    (6, "CENA", 4, [
        ("Petto di pollo, crudo", 150),
        ("Melanzane", 200),
        ("Pane di frumento, bianco", 40),
        ("Olio di oliva extravergine", 10),
    ]),
    # ── Domenica (giorno 7) ─────────────────────────────────────────────
    (7, "COLAZIONE", 0, [
        ("Latte parzialmente scremato", 200),
        ("Pane integrale", 50),
        ("Avocado", 50),
        ("Uovo intero, crudo", 60),  # 1 uovo
    ]),
    (7, "SPUNTINO_MATTINA", 1, [
        ("Pesca, fresca", 150),
    ]),
    (7, "PRANZO", 2, [
        ("Pasta integrale, secca", 80),
        ("Branzino, cotto", 160),
        ("Pomodori, freschi", 100),
        ("Olio di oliva extravergine", 10),
    ]),
    (7, "SPUNTINO_POMERIGGIO", 3, [
        ("Yogurt greco 0% grassi", 125),
        ("Anacardi", 15),
    ]),
    (7, "CENA", 4, [
        ("Edamame, cotti", 150),
        ("Riso bianco, cotto", 160),
        ("Broccoli, crudi", 150),
        ("Olio di oliva extravergine", 10),
    ]),
]


def _seed_templates(session: Session, food_id_map: dict[str, int], dry_run: bool) -> None:
    """Seed template piani + dieta completa donna_under30_attiva."""
    inserted_templates = 0
    inserted_meals = 0
    inserted_components = 0

    for tmpl_data in PLAN_TEMPLATES:
        existing = session.exec(
            select(PlanTemplate).where(PlanTemplate.slug == tmpl_data["slug"])
        ).first()
        if existing:
            continue
        if dry_run:
            inserted_templates += 1
            continue

        tmpl = PlanTemplate(
            slug=tmpl_data["slug"],
            nome=tmpl_data["nome"],
            descrizione=tmpl_data["descrizione"],
            tags=json.dumps(tmpl_data["tags"]),
            obiettivo_calorico=tmpl_data["obiettivo_calorico"],
            proteine_g_target=tmpl_data["proteine_g_target"],
            carboidrati_g_target=tmpl_data["carboidrati_g_target"],
            grassi_g_target=tmpl_data["grassi_g_target"],
            note_cliniche=tmpl_data["note_cliniche"],
        )
        session.add(tmpl)
        session.flush()
        inserted_templates += 1

        # Seed dieta completa solo per donna_under30_attiva
        if tmpl_data["slug"] == "donna_under30_attiva":
            for giorno, tipo_pasto, ordine, alimenti in DIETA_DONNA_ATTIVA:
                meal = TemplatePlanMeal(
                    template_id=tmpl.id,
                    giorno_settimana=giorno,
                    tipo_pasto=tipo_pasto,
                    ordine=ordine,
                )
                session.add(meal)
                session.flush()
                inserted_meals += 1

                for alimento_nome, grammi in alimenti:
                    food_id = food_id_map.get(alimento_nome)
                    if not food_id:
                        print(f"  [WARN] Alimento non trovato per template: '{alimento_nome}'")
                        continue
                    comp = TemplatePlanComponent(
                        meal_id=meal.id,
                        alimento_id=food_id,
                        quantita_g=grammi,
                    )
                    session.add(comp)
                    inserted_components += 1

    if not dry_run:
        session.commit()

    print(f"  Template piani: {len(PLAN_TEMPLATES)} totali, {inserted_templates} nuovi inseriti.")
    if inserted_meals or inserted_components:
        print(f"  Dieta template: {inserted_meals} pasti, {inserted_components} componenti.")


def _print_stats() -> None:
    """Stampa statistiche finali del DB."""
    with Session(nutrition_engine) as session:
        n_cat = session.exec(select(FoodCategory)).all().__len__()
        n_food = session.exec(select(Food).where(Food.is_active == True)).all().__len__()
        n_portions = session.exec(select(StandardPortion)).all().__len__()
        n_templates = session.exec(select(PlanTemplate)).all().__len__()
        n_tmpl_meals = session.exec(select(TemplatePlanMeal)).all().__len__()
        n_tmpl_comps = session.exec(select(TemplatePlanComponent)).all().__len__()

    print(f"\n  Statistiche nutrition.db:")
    print(f"    Categorie:           {n_cat}")
    print(f"    Alimenti attivi:     {n_food}")
    print(f"    Porzioni standard:   {n_portions}")
    print(f"    Template piani:      {n_templates}")
    print(f"    Pasti template:      {n_tmpl_meals}")
    print(f"    Componenti template: {n_tmpl_comps}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Costruisce nutrition.db con dati CREA 2019"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Conta i record da inserire senza scrivere",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Svuota le tabelle prima di reinserire (ricostruzione completa)",
    )
    args = parser.parse_args()
    build_nutrition_db(dry_run=args.dry_run, reset=args.reset)
