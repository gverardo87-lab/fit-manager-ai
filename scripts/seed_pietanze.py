"""
S2 — Seed pietanze composte + classificazione bevande.

Inserisce ~50 piatti italiani tipici nel catalogo nutrition.db.
I valori nutrizionali per 100g sono calcolati dalla composizione ingredienti.
Popola anche la tabella ricette_pietanze.

Uso:
    ./venv/Scripts/python scripts/seed_pietanze.py
    ./venv/Scripts/python scripts/seed_pietanze.py --dry-run
"""

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "nutrition.db"


# ---------------------------------------------------------------------------
# Bevande da riclassificare
# ---------------------------------------------------------------------------

BEVANDA_IDS = [
    122,  # Latte intero, fresco
    123,  # Latte parzialmente scremato
    124,  # Latte scremato
    137,  # Latte di soia
    151,  # Latte di mandorla, non zuccherato
    152,  # Succo d'arancia, fresco
    153,  # Latte di riso
    154,  # Latte di avena
    155,  # Caffè espresso, senza zucchero
]


# ---------------------------------------------------------------------------
# Ricette pietanze — (nome, categoria_id, [(ingrediente_id, grammi, note)])
# Nota: i valori nutrizionali vengono calcolati dalla composizione.
# ---------------------------------------------------------------------------

@dataclass
class Recipe:
    nome: str
    nome_en: str
    categoria_id: int  # categoria nel catalogo
    ingredients: list  # [(ingrediente_id, quantita_g, note_or_None), ...]


# Categoria 16 = "Primi piatti" (nuova)
# Categoria 17 = "Secondi piatti" (nuova)
# Categoria 18 = "Piatti unici e bowl" (nuova)
# Categoria 19 = "Zuppe e minestre" (nuova)
# Categoria 20 = "Contorni composti" (nuova)
# Categoria 21 = "Colazioni composte" (nuova)

NEW_CATEGORIES = [
    (16, "Primi piatti", "First courses", "🍝"),
    (17, "Secondi piatti", "Main courses", "🥩"),
    (18, "Piatti unici e bowl", "One-dish meals and bowls", "🥗"),
    (19, "Zuppe e minestre", "Soups and stews", "🍲"),
    (20, "Contorni composti", "Composed side dishes", "🥦"),
    (21, "Colazioni composte", "Composed breakfasts", "🥣"),
]

RECIPES = [
    # ===== PRIMI PIATTI (cat 16) =====
    Recipe("Pasta al pomodoro", "Pasta with tomato sauce", 16, [
        (8, 80, "pasta secca"),        # Pasta di semola, secca
        (142, 80, "salsa pomodoro"),   # Salsa di pomodoro, passata
        (138, 10, "1 cucchiaio"),      # Olio EVO
        (130, 10, "grattugiato"),      # Parmigiano reggiano
    ]),
    Recipe("Pasta integrale al pomodoro", "Whole wheat pasta with tomato", 16, [
        (10, 80, "pasta integrale secca"),
        (142, 80, "salsa pomodoro"),
        (138, 10, None),
        (130, 10, "grattugiato"),
    ]),
    Recipe("Pasta e fagioli", "Pasta and beans", 16, [
        (8, 50, "pasta corta"),
        (27, 120, "fagioli borlotti cotti"),
        (142, 60, "salsa pomodoro"),
        (138, 10, None),
        (52, 20, "soffritto"),         # Cipolla
        (41, 20, "soffritto"),         # Carote
    ]),
    Recipe("Pasta e lenticchie", "Pasta and lentils", 16, [
        (8, 50, "pasta corta"),
        (29, 120, "lenticchie cotte"),
        (142, 60, None),
        (138, 10, None),
        (52, 20, None),
        (41, 20, None),
    ]),
    Recipe("Pasta e ceci", "Pasta and chickpeas", 16, [
        (8, 50, "pasta corta"),
        (26, 120, "ceci cotti"),
        (142, 60, None),
        (138, 10, None),
        (52, 20, None),
    ]),
    Recipe("Pasta con tonno e pomodoro", "Pasta with tuna and tomato", 16, [
        (8, 80, None),
        (105, 80, "tonno al naturale sgocciolato"),
        (142, 80, None),
        (138, 10, None),
    ]),
    Recipe("Pasta con salmone e zucchine", "Pasta with salmon and zucchini", 16, [
        (8, 80, None),
        (103, 100, "a cubetti"),       # Salmone crudo
        (40, 100, "a rondelle"),       # Zucchine
        (138, 10, None),
    ]),
    Recipe("Risotto ai funghi", "Mushroom risotto", 16, [
        (12, 80, "riso crudo"),        # Riso bianco, crudo
        (51, 100, "champignon"),       # Funghi champignon
        (130, 15, "grattugiato"),
        (138, 10, None),
        (141, 5, None),               # Burro
        (52, 15, "soffritto"),
    ]),
    Recipe("Cous cous con verdure", "Couscous with vegetables", 16, [
        (15, 150, "cous cous cotto"),
        (42, 60, "peperoni a cubetti"),
        (40, 60, "zucchine a cubetti"),
        (41, 40, "carote a rondelle"),
        (138, 10, None),
    ]),
    Recipe("Farro con verdure", "Spelt with vegetables", 16, [
        (17, 150, "farro cotto"),
        (39, 50, "pomodorini"),
        (40, 60, None),
        (42, 50, None),
        (138, 10, None),
    ]),

    # ===== SECONDI PIATTI — CARNE (cat 17) =====
    Recipe("Petto di pollo alla griglia", "Grilled chicken breast", 17, [
        (83, 150, "petto crudo"),
        (138, 10, None),
    ]),
    Recipe("Scaloppine di vitello", "Veal cutlets", 17, [
        (90, 150, "scaloppina cruda"),
        (138, 10, None),
    ]),
    Recipe("Polpette di manzo al pomodoro", "Beef meatballs in tomato", 17, [
        (89, 150, "macinato magro"),
        (118, 50, "1 uovo"),
        (19, 30, "pane ammollato"),
        (142, 80, "sugo"),
        (138, 10, None),
    ]),
    Recipe("Hamburger di tacchino", "Turkey burger", 17, [
        (86, 150, "macinato"),
        (118, 50, "1 uovo"),
        (138, 5, None),
    ]),
    Recipe("Pollo con verdure", "Chicken with vegetables", 17, [
        (83, 150, "petto crudo"),
        (40, 80, "zucchine"),
        (42, 80, "peperoni"),
        (138, 10, None),
    ]),
    Recipe("Lonza di maiale al forno", "Roasted pork loin", 17, [
        (91, 150, "lonza cruda"),
        (138, 10, None),
    ]),

    # ===== SECONDI PIATTI — PESCE (cat 17) =====
    Recipe("Salmone al forno con limone", "Baked salmon with lemon", 17, [
        (103, 150, "filetto crudo"),
        (138, 10, None),
        (72, 10, "succo di limone"),
    ]),
    Recipe("Merluzzo al forno con pomodorini", "Baked cod with cherry tomatoes", 17, [
        (107, 150, "filetto crudo"),
        (39, 80, "pomodorini"),
        (138, 10, None),
    ]),
    Recipe("Branzino al forno", "Baked sea bass", 17, [
        (108, 150, "intero cotto"),
        (138, 10, None),
    ]),
    Recipe("Gamberi saltati in padella", "Pan-seared shrimp", 17, [
        (111, 150, "gamberi cotti"),
        (138, 10, None),
        (72, 5, "succo di limone"),
    ]),

    # ===== SECONDI — UOVA (cat 17) =====
    Recipe("Frittata di spinaci", "Spinach frittata", 17, [
        (118, 120, "2 uova"),
        (36, 80, "spinaci crudi"),
        (138, 10, None),
        (130, 10, "grattugiato"),
    ]),
    Recipe("Frittata di zucchine", "Zucchini frittata", 17, [
        (118, 120, "2 uova"),
        (40, 100, "zucchine"),
        (138, 10, None),
        (130, 10, "grattugiato"),
    ]),

    # ===== SECONDI — VEGETARIANI (cat 17) =====
    Recipe("Tofu saltato con verdure", "Stir-fried tofu with vegetables", 17, [
        (163, 150, "tofu a cubetti"),
        (40, 80, None),
        (42, 60, None),
        (144, 10, "salsa di soia"),
        (138, 10, None),
    ]),
    Recipe("Tempeh con verdure", "Tempeh with vegetables", 17, [
        (164, 120, "a fette"),
        (38, 80, "broccoli cotti"),
        (41, 40, None),
        (138, 10, None),
    ]),

    # ===== PIATTI UNICI E BOWL (cat 18) =====
    Recipe("Bowl di quinoa con pollo e avocado", "Quinoa bowl with chicken and avocado", 18, [
        (18, 120, "quinoa cotta"),
        (84, 100, "pollo cotto"),
        (65, 50, "avocado a fette"),
        (39, 50, "pomodorini"),
        (138, 10, None),
    ]),
    Recipe("Insalata di farro con mozzarella", "Spelt salad with mozzarella", 18, [
        (17, 120, "farro cotto"),
        (129, 80, "mozzarella a cubetti"),
        (39, 50, "pomodorini"),
        (43, 40, "cetrioli"),
        (138, 10, None),
    ]),
    Recipe("Poke bowl tonno e riso", "Tuna poke bowl with rice", 18, [
        (13, 120, "riso cotto"),
        (105, 80, "tonno al naturale"),
        (65, 50, "avocado"),
        (32, 40, "edamame"),
        (43, 30, "cetrioli"),
        (144, 5, "salsa di soia"),
    ]),
    Recipe("Buddha bowl con ceci e spinaci", "Buddha bowl with chickpeas and spinach", 18, [
        (18, 100, "quinoa cotta"),
        (26, 80, "ceci cotti"),
        (36, 60, "spinaci crudi"),
        (65, 40, "avocado"),
        (41, 30, "carote"),
        (138, 10, None),
    ]),
    Recipe("Riso con pollo e broccoli", "Rice with chicken and broccoli", 18, [
        (13, 150, "riso cotto"),
        (84, 120, "pollo cotto"),
        (38, 100, "broccoli cotti"),
        (138, 10, None),
    ]),
    Recipe("Insalata di riso estiva", "Summer rice salad", 18, [
        (13, 150, "riso cotto"),
        (105, 60, "tonno al naturale"),
        (39, 50, "pomodorini"),
        (43, 40, "cetrioli"),
        (42, 40, "peperoni"),
        (138, 10, None),
    ]),
    Recipe("Wrap di tacchino e verdure", "Turkey and vegetable wrap", 18, [
        (87, 100, "tacchino cotto"),
        (44, 40, "lattuga"),
        (39, 40, "pomodori"),
        (43, 30, "cetrioli"),
        (19, 50, "pane bianco come base"),
        (138, 5, None),
    ]),

    # ===== ZUPPE E MINESTRE (cat 19) =====
    Recipe("Minestrone di verdure", "Vegetable minestrone", 19, [
        (8, 30, "pastina"),
        (159, 80, "patate bollite"),
        (40, 60, "zucchine"),
        (41, 40, "carote"),
        (47, 40, "fagiolini"),
        (27, 40, "fagioli borlotti"),
        (142, 40, "pomodoro"),
        (52, 20, None),
        (138, 10, None),
    ]),
    Recipe("Zuppa di lenticchie", "Lentil soup", 19, [
        (29, 150, "lenticchie cotte"),
        (41, 40, "carote"),
        (52, 20, "cipolla"),
        (48, 20, "sedano"),
        (142, 40, None),
        (138, 10, None),
    ]),
    Recipe("Vellutata di broccoli", "Cream of broccoli soup", 19, [
        (37, 200, "broccoli crudi"),
        (159, 80, "patate bollite"),
        (138, 10, None),
        (52, 15, None),
    ]),
    Recipe("Zuppa di ceci e spinaci", "Chickpea and spinach soup", 19, [
        (26, 120, "ceci cotti"),
        (36, 60, "spinaci crudi"),
        (142, 40, None),
        (52, 15, None),
        (138, 10, None),
    ]),
    Recipe("Passato di verdure", "Pureed vegetable soup", 19, [
        (159, 80, "patate"),
        (40, 60, "zucchine"),
        (41, 40, "carote"),
        (52, 20, "cipolla"),
        (54, 30, "finocchio"),
        (138, 10, None),
    ]),

    # ===== CONTORNI COMPOSTI (cat 20) =====
    Recipe("Insalata mista", "Mixed salad", 20, [
        (44, 80, "lattuga"),
        (39, 60, "pomodori"),
        (41, 30, "carote"),
        (43, 30, "cetrioli"),
        (138, 10, None),
    ]),
    Recipe("Verdure grigliate miste", "Mixed grilled vegetables", 20, [
        (40, 80, "zucchine"),
        (42, 80, "peperoni"),
        (49, 80, "melanzane"),
        (138, 15, None),
    ]),
    Recipe("Spinaci saltati", "Sauteed spinach", 20, [
        (36, 200, "spinaci crudi"),
        (138, 10, None),
    ]),
    Recipe("Broccoli al vapore con olio", "Steamed broccoli with oil", 20, [
        (37, 200, "broccoli crudi"),
        (138, 10, None),
    ]),
    Recipe("Caponata di verdure", "Vegetable caponata", 20, [
        (49, 100, "melanzane"),
        (39, 60, "pomodori"),
        (42, 50, "peperoni"),
        (52, 30, "cipolla"),
        (138, 15, None),
        (143, 10, "aceto"),
    ]),
    Recipe("Insalata di finocchi e arance", "Fennel and orange salad", 20, [
        (54, 120, "finocchio"),
        (60, 80, "arancia"),
        (138, 10, None),
    ]),
    Recipe("Patate al forno", "Roasted potatoes", 20, [
        (159, 250, "patate bollite"),
        (138, 15, None),
    ]),

    # ===== COLAZIONI COMPOSTE (cat 21) =====
    Recipe("Porridge di avena con banana e miele", "Oat porridge with banana and honey", 21, [
        (1, 40, "fiocchi d'avena"),
        (123, 150, "latte"),
        (59, 80, "banana"),
        (146, 10, "miele"),
    ]),
    Recipe("Yogurt greco con frutta e cereali", "Greek yogurt with fruit and cereal", 21, [
        (126, 150, "yogurt greco 0%"),
        (69, 50, "mirtilli"),
        (59, 50, "banana"),
        (1, 20, "fiocchi d'avena"),
        (146, 10, "miele"),
    ]),
    Recipe("Pancake proteici", "Protein pancakes", 21, [
        (1, 50, "fiocchi d'avena"),
        (118, 100, "2 uova"),
        (59, 80, "banana matura"),
    ]),
    Recipe("Toast integrale con avocado e uovo", "Whole wheat toast with avocado and egg", 21, [
        (20, 60, "2 fette pane integrale"),
        (65, 50, "avocado"),
        (119, 60, "uovo sodo"),
    ]),
    Recipe("Smoothie proteico banana", "Banana protein smoothie", 21, [
        (123, 200, "latte"),
        (59, 100, "banana"),
        (156, 30, "whey protein"),
        (1, 15, "fiocchi d'avena"),
    ]),
    Recipe("Overnight oats con frutti di bosco", "Overnight oats with berries", 21, [
        (1, 50, "fiocchi d'avena"),
        (125, 100, "yogurt intero"),
        (69, 40, "mirtilli"),
        (63, 40, "fragole"),
        (79, 5, "semi di chia"),
    ]),
]

# Nutrient columns to calculate
NUTRIENT_COLS = [
    "energia_kcal", "proteine_g", "carboidrati_g", "grassi_g",
    "di_cui_zuccheri_g", "di_cui_saturi_g", "fibra_g", "sodio_mg",
    "acqua_g", "colesterolo_mg",
    "calcio_mg", "ferro_mg", "zinco_mg", "magnesio_mg",
    "fosforo_mg", "potassio_mg", "selenio_ug",
    "vitamina_a_ug", "vitamina_d_ug", "vitamina_e_mg", "vitamina_c_mg",
    "vitamina_b1_mg", "vitamina_b2_mg", "vitamina_b3_mg",
    "vitamina_b6_mg", "vitamina_b9_ug", "vitamina_b12_ug",
]


def load_ingredient_data(cur: sqlite3.Cursor) -> dict[int, dict]:
    """Load all active foods with their nutrient data."""
    cols = ", ".join(["id", "nome"] + NUTRIENT_COLS)
    cur.execute(f"SELECT {cols} FROM alimenti WHERE is_active=1")
    rows = cur.fetchall()
    col_names = ["id", "nome"] + NUTRIENT_COLS
    result = {}
    for row in rows:
        d = dict(zip(col_names, row))
        result[d["id"]] = d
    return result


def calc_per_100g(recipe: Recipe, foods: dict[int, dict]) -> dict:
    """Calculate nutritional values per 100g of finished dish."""
    total_weight = sum(qty for _, qty, _ in recipe.ingredients)
    totals = {col: 0.0 for col in NUTRIENT_COLS}

    for ing_id, qty_g, _ in recipe.ingredients:
        food = foods[ing_id]
        for col in NUTRIENT_COLS:
            val = food[col]
            if val is not None:
                totals[col] += val * qty_g / 100.0

    # Convert to per 100g
    result = {}
    for col in NUTRIENT_COLS:
        raw = totals[col]
        per100 = round(raw / total_weight * 100, 2)
        result[col] = per100

    return result


def main():
    parser = argparse.ArgumentParser(description="Seed pietanze composte in nutrition.db")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # Load ingredient data
    foods = load_ingredient_data(cur)
    print(f"Loaded {len(foods)} ingredients from DB")

    # Validate all recipe ingredients exist
    errors = []
    for r in RECIPES:
        for ing_id, _, _ in r.ingredients:
            if ing_id not in foods:
                errors.append(f"  {r.nome}: ingredient ID {ing_id} not found")
    if errors:
        print("ERRORS - missing ingredients:")
        for e in errors:
            print(e)
        sys.exit(1)

    # --- Step 1: Classify beverages ---
    cur.execute("SELECT id, nome, food_type FROM alimenti WHERE id IN ({})".format(
        ",".join(str(i) for i in BEVANDA_IDS)
    ))
    existing_beverages = cur.fetchall()
    bev_updates = 0
    for row in existing_beverages:
        if row[2] != "bevanda":
            if not args.dry_run:
                cur.execute("UPDATE alimenti SET food_type='bevanda' WHERE id=?", (row[0],))
            bev_updates += 1
            print(f"  bevanda: {row[1]}")
    print(f"\nBevande classified: {bev_updates}")

    # --- Step 2: Create new categories ---
    for cat_id, nome, nome_en, icona in NEW_CATEGORIES:
        cur.execute("SELECT id FROM categorie_alimenti WHERE id=?", (cat_id,))
        if not cur.fetchone():
            if not args.dry_run:
                cur.execute(
                    "INSERT INTO categorie_alimenti (id, nome, nome_en, icona) VALUES (?,?,?,?)",
                    (cat_id, nome, nome_en, icona)
                )
            print(f"  + categoria: {nome}")

    # --- Step 3: Insert pietanze + recipes ---
    inserted = 0
    skipped = 0
    for recipe in RECIPES:
        # Check if already exists
        cur.execute("SELECT id FROM alimenti WHERE nome=?", (recipe.nome,))
        if cur.fetchone():
            skipped += 1
            continue

        # Calculate nutrients
        nutrients = calc_per_100g(recipe, foods)

        # Insert pietanza
        cols = ["nome", "nome_en", "categoria_id", "food_type", "source", "is_active"]
        vals = [recipe.nome, recipe.nome_en, recipe.categoria_id, "pietanza", "calcolato", True]
        for col in NUTRIENT_COLS:
            cols.append(col)
            vals.append(nutrients[col])

        placeholders = ", ".join(["?"] * len(vals))
        col_str = ", ".join(cols)

        if not args.dry_run:
            cur.execute(f"INSERT INTO alimenti ({col_str}) VALUES ({placeholders})", vals)
            pietanza_id = cur.lastrowid
        else:
            pietanza_id = f"(new:{recipe.nome})"

        # Insert recipe components
        total_g = sum(qty for _, qty, _ in recipe.ingredients)
        for ing_id, qty_g, note in recipe.ingredients:
            if not args.dry_run:
                cur.execute(
                    "INSERT INTO ricette_pietanze (pietanza_id, ingrediente_id, quantita_g, note) "
                    "VALUES (?, ?, ?, ?)",
                    (pietanza_id, ing_id, qty_g, note)
                )

        kcal = nutrients["energia_kcal"]
        prot = nutrients["proteine_g"]
        carb = nutrients["carboidrati_g"]
        fat = nutrients["grassi_g"]
        print(f"  + {recipe.nome} ({total_g}g) — "
              f"{kcal:.0f}kcal P{prot:.1f} C{carb:.1f} G{fat:.1f} /100g")
        inserted += 1

    if not args.dry_run:
        conn.commit()

    print(f"\nRiepilogo:")
    print(f"  Bevande riclassificate: {bev_updates}")
    print(f"  Pietanze inserite: {inserted}")
    print(f"  Pietanze skippate (gia' esistenti): {skipped}")
    print(f"  Ricette componenti: {sum(len(r.ingredients) for r in RECIPES)}")

    # Final stats
    if not args.dry_run:
        cur.execute("SELECT food_type, COUNT(*) FROM alimenti WHERE is_active=1 GROUP BY food_type")
        print(f"\nDistribuzione food_type:")
        for ft, cnt in cur.fetchall():
            print(f"  {ft}: {cnt}")

    conn.close()


if __name__ == "__main__":
    main()
