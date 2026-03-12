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

from api.config import NUTRITION_DATABASE_URL
from api.database import create_nutrition_tables, nutrition_engine
from api.models.nutrition import FoodCategory, Food, StandardPortion
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
# Dati seed: alimenti (nome, categoria_nome, kcal, prot, carb, gras,
#                       zuccheri, saturi, fibra, sodio, acqua, colest)
# Fonte: CREA 2019 / USDA FoodData Central (prodotti senza equivalente CREA)
# Tutti i valori per 100g edibile.
# ---------------------------------------------------------------------------

FOODS = [
    # ── Cereali e derivati ──────────────────────────────────────────────
    ("Avena, fiocchi", "Cereali e derivati", 372, 13.2, 58.7, 7.1, 1.1, 1.3, 10.6, 6, 8.2, 0),
    ("Farro, crudo", "Cereali e derivati", 340, 14.7, 67.7, 2.5, 0.5, 0.4, 7.1, 3, 11.0, 0),
    ("Mais, farina gialla", "Cereali e derivati", 362, 9.2, 77.7, 3.8, 0.6, 0.5, 5.4, 5, 8.1, 0),
    ("Orzo perlato, crudo", "Cereali e derivati", 319, 10.0, 68.0, 1.0, 0.4, 0.2, 9.8, 4, 10.7, 0),
    ("Grano saraceno, crudo", "Cereali e derivati", 335, 13.3, 65.1, 3.4, 1.6, 0.7, 10.0, 2, 9.4, 0),
    ("Riso integrale, crudo", "Cereali e derivati", 330, 7.5, 68.5, 2.5, 0.4, 0.5, 3.5, 3, 12.4, 0),
    ("Quinoa, cruda", "Cereali e derivati", 368, 14.1, 64.2, 6.1, 2.7, 0.7, 7.0, 5, 13.3, 0),

    # ── Pasta, riso e cereali cotti ─────────────────────────────────────
    ("Pasta di semola, secca", "Pasta, riso e cereali cotti", 353, 12.9, 72.2, 1.5, 2.1, 0.3, 2.7, 5, 11.8, 0),
    ("Pasta di semola, cotta", "Pasta, riso e cereali cotti", 131, 4.9, 26.2, 0.5, 0.3, 0.1, 1.8, 1, 67.1, 0),
    ("Pasta integrale, secca", "Pasta, riso e cereali cotti", 340, 13.4, 67.3, 2.3, 2.0, 0.4, 9.0, 6, 10.9, 0),
    ("Pasta integrale, cotta", "Pasta, riso e cereali cotti", 124, 5.3, 23.5, 0.8, 0.5, 0.2, 3.9, 2, 67.5, 0),
    ("Riso bianco, crudo", "Pasta, riso e cereali cotti", 332, 6.5, 76.9, 0.4, 0.1, 0.1, 1.4, 3, 12.4, 0),
    ("Riso bianco, cotto", "Pasta, riso e cereali cotti", 138, 2.7, 31.9, 0.2, 0.0, 0.1, 0.6, 1, 65.1, 0),
    ("Riso integrale, cotto", "Pasta, riso e cereali cotti", 123, 2.7, 25.8, 1.0, 0.3, 0.2, 1.8, 2, 70.0, 0),
    ("Cous cous, cotto", "Pasta, riso e cereali cotti", 112, 3.8, 23.2, 0.2, 0.1, 0.0, 1.4, 5, 72.6, 0),
    ("Polenta, cotta", "Pasta, riso e cereali cotti", 84, 2.0, 17.8, 0.4, 0.2, 0.1, 1.2, 4, 79.0, 0),
    ("Farro, cotto", "Pasta, riso e cereali cotti", 147, 6.3, 27.8, 1.0, 0.3, 0.2, 3.9, 2, 64.2, 0),
    ("Quinoa, cotta", "Pasta, riso e cereali cotti", 120, 4.4, 21.3, 1.9, 0.9, 0.2, 2.8, 7, 72.0, 0),

    # ── Pane e prodotti da forno ────────────────────────────────────────
    ("Pane di frumento, bianco", "Pane e prodotti da forno", 270, 8.1, 53.8, 0.5, 2.7, 0.1, 3.8, 530, 35.5, 0),
    ("Pane integrale", "Pane e prodotti da forno", 224, 8.5, 40.6, 1.5, 3.5, 0.3, 6.5, 540, 42.7, 0),
    ("Pane di segale", "Pane e prodotti da forno", 258, 8.5, 48.3, 3.3, 3.8, 0.3, 5.8, 440, 33.9, 0),
    ("Crackers, classici", "Pane e prodotti da forno", 428, 10.1, 68.5, 12.5, 2.4, 1.6, 3.1, 790, 5.8, 0),
    ("Fiocchi di mais, cornflakes", "Pane e prodotti da forno", 357, 7.0, 84.1, 0.4, 7.7, 0.1, 2.8, 660, 3.8, 0),
    ("Gallette di riso", "Pane e prodotti da forno", 389, 8.0, 82.5, 3.1, 0.3, 0.7, 1.8, 30, 4.5, 0),
    ("Fette biscottate integrali", "Pane e prodotti da forno", 380, 10.9, 69.8, 5.6, 5.1, 0.9, 8.0, 460, 6.1, 0),

    # ── Legumi ───────────────────────────────────────────────────────────
    ("Ceci, cotti", "Legumi", 164, 8.4, 27.4, 2.6, 4.8, 0.3, 7.6, 24, 60.0, 0),
    ("Fagioli borlotti, cotti", "Legumi", 112, 7.5, 19.5, 0.5, 1.8, 0.1, 6.9, 5, 70.4, 0),
    ("Fagioli bianchi cannellini, cotti", "Legumi", 113, 7.3, 20.5, 0.5, 0.4, 0.1, 8.0, 6, 70.1, 0),
    ("Lenticchie, cotte", "Legumi", 116, 9.0, 20.1, 0.4, 1.8, 0.1, 7.9, 14, 68.0, 0),
    ("Piselli, surgelati cotti", "Legumi", 80, 5.4, 14.0, 0.4, 5.7, 0.1, 5.1, 115, 79.6, 0),
    ("Soia, semi cotti", "Legumi", 173, 16.6, 9.9, 9.0, 2.1, 1.3, 6.0, 2, 62.6, 0),
    ("Edamame, cotti", "Legumi", 122, 11.9, 8.9, 5.2, 2.2, 0.7, 5.2, 4, 72.8, 0),
    ("Fave, cotte", "Legumi", 110, 7.9, 18.3, 0.5, 3.8, 0.1, 5.4, 9, 71.5, 0),
    ("Ceci, secchi (crudi)", "Legumi", 334, 20.9, 54.3, 5.4, 10.7, 0.6, 17.4, 24, 10.7, 0),
    ("Lenticchie, secche (crude)", "Legumi", 319, 23.5, 55.8, 1.3, 2.0, 0.2, 10.7, 14, 10.7, 0),

    # ── Verdure e ortaggi ───────────────────────────────────────────────
    ("Spinaci, crudi", "Verdure e ortaggi", 23, 2.9, 3.6, 0.4, 0.4, 0.1, 2.2, 79, 91.4, 0),
    ("Broccoli, crudi", "Verdure e ortaggi", 31, 2.8, 5.2, 0.4, 1.7, 0.1, 2.6, 41, 88.2, 0),
    ("Broccoli, cotti", "Verdure e ortaggi", 36, 3.5, 5.0, 0.6, 1.4, 0.1, 3.3, 45, 89.2, 0),
    ("Pomodori, freschi", "Verdure e ortaggi", 20, 1.2, 3.9, 0.2, 2.6, 0.0, 1.2, 5, 93.5, 0),
    ("Zucchine", "Verdure e ortaggi", 17, 1.3, 2.5, 0.1, 1.7, 0.0, 1.0, 3, 94.8, 0),
    ("Carote", "Verdure e ortaggi", 40, 0.9, 9.3, 0.2, 4.7, 0.0, 2.8, 69, 88.3, 0),
    ("Peperoni rossi", "Verdure e ortaggi", 27, 1.0, 6.0, 0.3, 4.2, 0.0, 2.1, 4, 92.2, 0),
    ("Cetrioli", "Verdure e ortaggi", 12, 0.7, 2.2, 0.1, 1.7, 0.0, 0.5, 2, 96.7, 0),
    ("Lattuga, iceberg", "Verdure e ortaggi", 14, 1.4, 2.2, 0.2, 2.0, 0.0, 1.2, 10, 95.6, 0),
    ("Cavolo cappuccio", "Verdure e ortaggi", 25, 1.4, 5.0, 0.1, 2.6, 0.0, 2.5, 18, 92.2, 0),
    ("Asparagi", "Verdure e ortaggi", 20, 2.2, 3.9, 0.1, 1.9, 0.0, 2.1, 14, 92.4, 0),
    ("Fagiolini, cotti", "Verdure e ortaggi", 37, 2.2, 7.1, 0.2, 2.0, 0.0, 3.4, 6, 88.9, 0),
    ("Sedano", "Verdure e ortaggi", 15, 0.7, 2.9, 0.2, 1.8, 0.0, 1.8, 80, 95.4, 0),
    ("Melanzane", "Verdure e ortaggi", 24, 1.0, 5.7, 0.1, 2.4, 0.0, 3.4, 2, 92.0, 0),
    ("Carciofi", "Verdure e ortaggi", 47, 3.3, 9.5, 0.2, 1.0, 0.0, 5.7, 94, 84.9, 0),
    ("Funghi champignon, crudi", "Verdure e ortaggi", 22, 1.8, 3.3, 0.3, 1.9, 0.0, 1.0, 6, 93.5, 0),
    ("Cipolla", "Verdure e ortaggi", 40, 1.1, 9.3, 0.1, 4.2, 0.0, 1.7, 4, 89.1, 0),
    ("Cavolo nero", "Verdure e ortaggi", 35, 3.3, 5.0, 0.7, 1.0, 0.1, 4.1, 53, 89.6, 0),
    ("Finocchio", "Verdure e ortaggi", 31, 1.3, 6.9, 0.1, 4.1, 0.0, 3.1, 52, 90.2, 0),
    ("Bietola", "Verdure e ortaggi", 17, 1.6, 2.8, 0.2, 1.8, 0.0, 1.6, 213, 92.7, 0),
    ("Rucola", "Verdure e ortaggi", 25, 2.6, 2.0, 0.7, 2.0, 0.1, 1.6, 27, 91.7, 0),
    ("Radicchio", "Verdure e ortaggi", 23, 1.4, 4.5, 0.3, 0.3, 0.0, 3.1, 22, 92.2, 0),

    # ── Frutta fresca ───────────────────────────────────────────────────
    ("Mela, fresca", "Frutta fresca", 52, 0.3, 13.8, 0.2, 10.4, 0.0, 2.4, 1, 85.6, 0),
    ("Banana, fresca", "Frutta fresca", 89, 1.1, 22.8, 0.3, 12.2, 0.1, 2.6, 1, 74.9, 0),
    ("Arancia, fresca", "Frutta fresca", 47, 0.9, 11.8, 0.1, 9.4, 0.0, 2.4, 0, 86.8, 0),
    ("Pera, fresca", "Frutta fresca", 57, 0.4, 15.2, 0.1, 9.8, 0.0, 3.1, 1, 83.7, 0),
    ("Pesca, fresca", "Frutta fresca", 39, 0.9, 9.5, 0.1, 8.4, 0.0, 1.5, 0, 88.1, 0),
    ("Fragole, fresche", "Frutta fresca", 27, 0.8, 6.0, 0.3, 4.9, 0.0, 2.0, 1, 91.6, 0),
    ("Kiwi", "Frutta fresca", 61, 1.1, 14.6, 0.5, 9.0, 0.0, 3.0, 3, 83.1, 0),
    ("Avocado", "Frutta fresca", 160, 2.0, 8.5, 14.7, 0.7, 2.1, 6.7, 7, 73.2, 0),
    ("Uva, fresca", "Frutta fresca", 67, 0.6, 17.2, 0.4, 16.2, 0.1, 0.9, 2, 81.3, 0),
    ("Melone, fresco", "Frutta fresca", 34, 0.8, 8.2, 0.2, 7.9, 0.0, 0.9, 22, 90.2, 0),
    ("Anguria, fresca", "Frutta fresca", 30, 0.6, 7.6, 0.2, 6.2, 0.0, 0.4, 1, 91.5, 0),
    ("Mirtilli, freschi", "Frutta fresca", 57, 0.7, 14.5, 0.3, 10.0, 0.0, 2.4, 1, 84.2, 0),
    ("Ananas, fresco", "Frutta fresca", 50, 0.5, 13.1, 0.1, 9.9, 0.0, 1.4, 1, 86.0, 0),
    ("Pompelmo, fresco", "Frutta fresca", 42, 0.8, 10.7, 0.1, 6.9, 0.0, 1.7, 0, 88.1, 0),
    ("Limone", "Frutta fresca", 29, 1.1, 6.5, 0.6, 2.5, 0.1, 2.8, 2, 90.1, 0),

    # ── Frutta secca e semi ──────────────────────────────────────────────
    ("Mandorle", "Frutta secca e semi", 579, 21.2, 21.7, 49.9, 4.4, 3.8, 12.5, 1, 4.4, 0),
    ("Noci", "Frutta secca e semi", 654, 15.2, 13.7, 65.2, 2.6, 6.1, 6.7, 2, 4.1, 0),
    ("Anacardi", "Frutta secca e semi", 553, 18.2, 30.2, 43.9, 5.9, 7.8, 3.3, 12, 5.2, 0),
    ("Nocciole", "Frutta secca e semi", 628, 15.0, 16.7, 60.8, 4.3, 4.5, 9.7, 0, 5.3, 0),
    ("Pistacchi", "Frutta secca e semi", 560, 20.6, 27.2, 45.3, 7.7, 5.6, 10.6, 1, 4.0, 0),
    ("Arachidi, tostate", "Frutta secca e semi", 567, 25.8, 16.1, 49.2, 4.0, 6.9, 8.5, 6, 1.6, 0),
    ("Semi di chia", "Frutta secca e semi", 486, 16.5, 42.1, 30.7, 0.0, 3.3, 34.4, 16, 5.8, 0),
    ("Semi di lino", "Frutta secca e semi", 534, 18.3, 28.9, 42.2, 1.5, 3.7, 27.3, 30, 6.9, 0),
    ("Semi di zucca", "Frutta secca e semi", 559, 30.2, 10.7, 49.1, 1.4, 8.7, 6.0, 7, 5.3, 0),
    ("Semi di girasole", "Frutta secca e semi", 584, 20.8, 20.0, 51.5, 2.6, 4.5, 8.6, 9, 4.7, 0),

    # ── Carne e pollame ─────────────────────────────────────────────────
    ("Petto di pollo, crudo", "Carne e pollame", 110, 23.3, 0.0, 1.2, 0.0, 0.3, 0.0, 73, 74.9, 58),
    ("Petto di pollo, cotto al forno", "Carne e pollame", 165, 31.0, 0.0, 3.6, 0.0, 1.0, 0.0, 74, 64.0, 85),
    ("Coscia di pollo, cotta", "Carne e pollame", 232, 27.3, 0.0, 13.4, 0.0, 3.7, 0.0, 95, 59.4, 93),
    ("Petto di tacchino, crudo", "Carne e pollame", 107, 23.0, 0.0, 1.3, 0.0, 0.4, 0.0, 63, 74.0, 47),
    ("Petto di tacchino, cotto", "Carne e pollame", 157, 30.1, 0.0, 3.2, 0.0, 0.9, 0.0, 70, 64.7, 60),
    ("Manzo, fesa, cruda", "Carne e pollame", 105, 21.4, 0.0, 1.9, 0.0, 0.8, 0.0, 60, 75.3, 59),
    ("Manzo macinato magro 5%, crudo", "Carne e pollame", 137, 21.7, 0.0, 5.4, 0.0, 2.1, 0.0, 73, 71.4, 62),
    ("Vitello, scaloppina cruda", "Carne e pollame", 109, 21.0, 0.0, 2.6, 0.0, 1.0, 0.0, 78, 74.9, 70),
    ("Maiale, lonza cruda", "Carne e pollame", 122, 20.7, 0.0, 4.1, 0.0, 1.4, 0.0, 61, 73.8, 67),
    ("Maiale, filetto crudo", "Carne e pollame", 108, 22.4, 0.0, 2.2, 0.0, 0.8, 0.0, 58, 74.0, 62),
    ("Coniglio, cotto", "Carne e pollame", 179, 24.9, 0.0, 8.2, 0.0, 2.4, 0.0, 57, 65.2, 82),
    ("Fegato di manzo, crudo", "Carne e pollame", 133, 19.7, 3.8, 4.2, 1.9, 1.4, 0.0, 76, 71.2, 274),
    ("Fegato di pollo, crudo", "Carne e pollame", 130, 19.0, 0.9, 5.5, 0.9, 1.7, 0.0, 81, 72.4, 345),

    # ── Salumi e affettati ───────────────────────────────────────────────
    ("Bresaola", "Salumi e affettati", 151, 32.0, 0.3, 2.3, 0.0, 0.9, 0.0, 1800, 63.3, 74),
    ("Prosciutto crudo, magro", "Salumi e affettati", 158, 27.2, 0.0, 5.5, 0.0, 1.8, 0.0, 2580, 62.4, 73),
    ("Prosciutto cotto, magro", "Salumi e affettati", 124, 18.5, 1.5, 4.7, 1.1, 1.6, 0.0, 1140, 73.1, 58),
    ("Mortadella", "Salumi e affettati", 302, 14.7, 0.0, 26.7, 0.4, 9.9, 0.0, 1200, 58.1, 70),
    ("Salsiccia di maiale", "Salumi e affettati", 302, 14.3, 0.0, 27.0, 0.3, 9.9, 0.0, 870, 57.3, 80),
    ("Salame tipo Milano", "Salumi e affettati", 434, 21.4, 0.8, 39.0, 0.4, 14.5, 0.0, 1780, 33.0, 80),
    ("Speck", "Salumi e affettati", 234, 25.0, 0.9, 14.4, 0.6, 5.0, 0.0, 1840, 55.4, 76),

    # ── Prodotti ittici ──────────────────────────────────────────────────
    ("Salmone atlantico, crudo", "Prodotti ittici", 208, 20.4, 0.0, 13.4, 0.0, 3.1, 0.0, 59, 63.7, 63),
    ("Salmone, cotto al forno", "Prodotti ittici", 206, 25.4, 0.0, 10.9, 0.0, 2.5, 0.0, 69, 62.1, 70),
    ("Tonno in scatola al naturale", "Prodotti ittici", 103, 23.6, 0.0, 1.0, 0.0, 0.2, 0.0, 320, 74.8, 55),
    ("Tonno in scatola all'olio, sgocciolato", "Prodotti ittici", 184, 25.9, 0.0, 8.9, 0.0, 1.5, 0.0, 450, 64.5, 55),
    ("Merluzzo, filetto crudo", "Prodotti ittici", 82, 17.8, 0.0, 0.9, 0.0, 0.2, 0.0, 78, 80.3, 43),
    ("Branzino, cotto", "Prodotti ittici", 105, 20.5, 0.0, 2.7, 0.0, 0.5, 0.0, 72, 74.2, 63),
    ("Orata, cruda", "Prodotti ittici", 95, 20.1, 0.0, 1.7, 0.0, 0.5, 0.0, 79, 77.4, 57),
    ("Sgombro, crudo", "Prodotti ittici", 205, 18.7, 0.0, 13.9, 0.0, 3.3, 0.0, 90, 65.1, 70),
    ("Gamberi, cotti", "Prodotti ittici", 85, 18.0, 1.5, 0.9, 0.0, 0.2, 0.0, 566, 78.7, 152),
    ("Trota, cruda", "Prodotti ittici", 107, 20.8, 0.0, 2.7, 0.0, 0.7, 0.0, 50, 74.5, 58),
    ("Acciughe sott'olio, sgocciolate", "Prodotti ittici", 210, 28.9, 0.0, 10.0, 0.0, 2.1, 0.0, 3670, 58.2, 85),
    ("Pesce spada, crudo", "Prodotti ittici", 109, 17.0, 0.0, 4.2, 0.0, 1.1, 0.0, 98, 76.4, 39),
    ("Calamari, crudi", "Prodotti ittici", 92, 15.6, 3.1, 1.4, 0.0, 0.4, 0.0, 260, 79.3, 233),
    ("Polpo, cotto", "Prodotti ittici", 164, 29.8, 4.4, 2.1, 0.0, 0.5, 0.0, 450, 63.2, 96),
    ("Cod baccala' ammollato", "Prodotti ittici", 86, 19.5, 0.0, 0.5, 0.0, 0.1, 0.0, 220, 79.3, 57),

    # ── Uova ────────────────────────────────────────────────────────────
    ("Uovo intero, crudo", "Uova", 133, 12.4, 0.7, 8.7, 0.4, 2.7, 0.0, 126, 76.7, 371),
    ("Uovo intero, cotto sodo", "Uova", 147, 12.4, 0.7, 10.3, 0.4, 3.1, 0.0, 135, 74.6, 400),
    ("Albume d'uovo, crudo", "Uova", 52, 10.9, 0.7, 0.3, 0.6, 0.0, 0.0, 166, 87.6, 0),
    ("Tuorlo d'uovo, crudo", "Uova", 322, 16.0, 0.6, 27.8, 0.3, 8.1, 0.0, 48, 52.3, 1085),

    # ── Latte, yogurt e formaggi ─────────────────────────────────────────
    ("Latte intero, fresco", "Latte, yogurt e formaggi", 64, 3.3, 4.7, 3.6, 5.0, 2.1, 0.0, 44, 87.8, 13),
    ("Latte parzialmente scremato", "Latte, yogurt e formaggi", 49, 3.3, 4.8, 1.6, 5.0, 1.0, 0.0, 46, 89.6, 6),
    ("Latte scremato", "Latte, yogurt e formaggi", 36, 3.4, 5.0, 0.2, 5.0, 0.1, 0.0, 49, 91.0, 2),
    ("Yogurt intero bianco", "Latte, yogurt e formaggi", 73, 3.9, 4.9, 3.9, 4.9, 2.5, 0.0, 50, 87.2, 13),
    ("Yogurt greco 0% grassi", "Latte, yogurt e formaggi", 57, 10.0, 3.6, 0.4, 3.2, 0.3, 0.0, 36, 85.4, 5),
    ("Yogurt greco intero", "Latte, yogurt e formaggi", 97, 9.0, 3.6, 5.0, 3.2, 3.2, 0.0, 40, 81.1, 15),
    ("Mozzarella di bufala", "Latte, yogurt e formaggi", 253, 18.7, 0.7, 19.5, 0.4, 12.2, 0.0, 600, 59.1, 60),
    ("Mozzarella vaccina (fior di latte)", "Latte, yogurt e formaggi", 233, 17.1, 0.7, 17.8, 0.6, 11.1, 0.0, 500, 61.0, 56),
    ("Parmigiano reggiano", "Latte, yogurt e formaggi", 392, 33.0, 0.0, 28.1, 0.0, 18.0, 0.0, 700, 30.8, 90),
    ("Grana padano", "Latte, yogurt e formaggi", 384, 33.3, 0.0, 27.6, 0.0, 17.7, 0.0, 650, 31.9, 90),
    ("Ricotta di vaccino", "Latte, yogurt e formaggi", 146, 9.5, 2.7, 10.9, 2.7, 6.9, 0.0, 95, 73.0, 50),
    ("Fiocchi di latte (cottage cheese)", "Latte, yogurt e formaggi", 98, 10.7, 3.4, 4.4, 3.1, 2.8, 0.0, 364, 80.0, 15),
    ("Pecorino romano", "Latte, yogurt e formaggi", 387, 25.8, 0.2, 31.3, 0.1, 20.0, 0.0, 1200, 30.6, 93),
    ("Scamorza", "Latte, yogurt e formaggi", 334, 26.9, 1.3, 24.4, 1.2, 15.4, 0.0, 860, 44.9, 79),
    ("Asiago", "Latte, yogurt e formaggi", 352, 28.5, 0.1, 26.1, 0.1, 16.5, 0.0, 770, 39.0, 85),
    ("Latte di soia", "Latte, yogurt e formaggi", 33, 3.3, 1.9, 1.8, 0.9, 0.2, 0.3, 51, 90.4, 0),

    # ── Oli e condimenti ─────────────────────────────────────────────────
    ("Olio di oliva extravergine", "Oli e condimenti", 884, 0.0, 0.0, 99.9, 0.0, 13.8, 0.0, 2, 0.2, 0),
    ("Olio di semi di girasole", "Oli e condimenti", 884, 0.0, 0.0, 100.0, 0.0, 10.1, 0.0, 0, 0.0, 0),
    ("Olio di cocco", "Oli e condimenti", 892, 0.0, 0.0, 99.1, 0.0, 83.0, 0.0, 0, 0.0, 0),
    ("Burro", "Oli e condimenti", 758, 0.9, 0.8, 83.5, 0.7, 51.4, 0.0, 714, 14.0, 215),
    ("Salsa di pomodoro, passata", "Oli e condimenti", 35, 1.5, 7.0, 0.4, 5.4, 0.1, 1.5, 320, 90.5, 0),
    ("Aceto di vino rosso", "Oli e condimenti", 22, 0.0, 0.6, 0.0, 0.4, 0.0, 0.0, 8, 95.8, 0),
    ("Salsa di soia (tamari)", "Oli e condimenti", 53, 8.1, 4.9, 0.1, 2.0, 0.0, 0.0, 5480, 71.7, 0),

    # ── Dolci e zuccheri ─────────────────────────────────────────────────
    ("Zucchero bianco", "Dolci e zuccheri", 392, 0.0, 99.8, 0.0, 99.8, 0.0, 0.0, 0, 0.2, 0),
    ("Miele", "Dolci e zuccheri", 304, 0.3, 80.3, 0.0, 76.4, 0.0, 0.2, 4, 17.1, 0),
    ("Cioccolato fondente 70%", "Dolci e zuccheri", 598, 5.3, 45.9, 42.6, 28.0, 24.5, 11.9, 11, 1.0, 0),
    ("Cioccolato al latte", "Dolci e zuccheri", 534, 7.7, 59.4, 29.7, 57.1, 17.9, 1.5, 79, 1.0, 23),
    ("Marmellata, media", "Dolci e zuccheri", 265, 0.5, 68.0, 0.1, 55.0, 0.0, 1.2, 15, 30.0, 0),
    ("Sciroppo d'acero", "Dolci e zuccheri", 260, 0.0, 67.0, 0.1, 59.5, 0.0, 0.0, 9, 32.4, 0),

    # ── Bevande e integratori ────────────────────────────────────────────
    ("Latte di mandorla, non zuccherato", "Bevande e integratori", 24, 0.6, 3.0, 1.1, 0.4, 0.1, 0.3, 72, 94.4, 0),
    ("Succo d'arancia, fresco", "Bevande e integratori", 45, 0.7, 10.4, 0.2, 8.4, 0.0, 0.2, 1, 88.3, 0),
    ("Latte di riso", "Bevande e integratori", 47, 0.3, 9.2, 1.0, 4.4, 0.1, 0.3, 39, 89.2, 0),
    ("Latte di avena", "Bevande e integratori", 46, 1.0, 7.9, 1.5, 3.6, 0.2, 0.8, 44, 88.7, 0),
    ("Caffè espresso, senza zucchero", "Bevande e integratori", 2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 2, 97.3, 0),
    ("Whey protein isolate (polvere)", "Bevande e integratori", 375, 90.0, 4.5, 1.5, 2.0, 1.0, 0.0, 150, 3.0, 5),
    ("Creatina monoidrato (polvere)", "Bevande e integratori", 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 0),
    ("BCAA, polvere", "Bevande e integratori", 400, 95.0, 2.0, 2.0, 0.0, 0.0, 0.0, 20, 1.0, 0),
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

    if reset and not dry_run:
        # Svuota tabelle in ordine inverso (FK)
        with Session(nutrition_engine) as s:
            s.exec(StandardPortion.__table__.delete())
            s.exec(Food.__table__.delete())
            s.exec(FoodCategory.__table__.delete())
            s.commit()
        print("  [RESET] Tabelle svuotate.")

    create_nutrition_tables()
    print("  Tabelle create (o già esistenti).")

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
            (nome, cat_nome, kcal, prot, carb, gras,
             zucch, satur, fibra, sodio, acqua, colest) = row

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

            if not dry_run:
                food = Food(
                    nome=nome,
                    categoria_id=cat_id,
                    energia_kcal=kcal,
                    proteine_g=prot,
                    carboidrati_g=carb,
                    grassi_g=gras,
                    di_cui_zuccheri_g=zucch or None,
                    di_cui_saturi_g=satur or None,
                    fibra_g=fibra or None,
                    sodio_mg=sodio or None,
                    acqua_g=acqua or None,
                    colesterolo_mg=colest if colest > 0 else None,
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

    if dry_run:
        print("\n  [DRY RUN] Nessuna modifica eseguita.")
    else:
        print("\n  nutrition.db pronto.")
        _print_stats()


def _print_stats() -> None:
    """Stampa statistiche finali del DB."""
    with Session(nutrition_engine) as session:
        n_cat = session.exec(select(FoodCategory)).all().__len__()
        n_food = session.exec(select(Food).where(Food.is_active == True)).all().__len__()
        n_portions = session.exec(select(StandardPortion)).all().__len__()

    print(f"\n  Statistiche nutrition.db:")
    print(f"    Categorie:         {n_cat}")
    print(f"    Alimenti attivi:   {n_food}")
    print(f"    Porzioni standard: {n_portions}")


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
