"""
Terzo blocco seed — da ~746 a ~900 alimenti.
Eseguire DOPO seed_nutrition_foods_2.py.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "nutrition.db"

FOODS = [
    # ── CAT 1: Cereali ────────────────────────────────────────────────────────
    ("Pasta proteica (+proteine di legumi), secca", "High-protein pasta (legume protein), dry", 1, 348, 22.0, 57.0, 3.5, 1.5, 0.5, 8.0, 20, 10.0, "usda"),
    ("Pasta di konjac (shirataki, cotta)", "Konjac pasta (shirataki, cooked)", 1, 10, 0.1, 2.8, 0.0, 0.0, 0.0, 2.5, 15, 97.0, "usda"),
    ("Pasta di edamame/soia, secca", "Edamame/soy pasta, dry", 1, 355, 24.0, 50.0, 6.0, 3.5, 0.9, 8.5, 25, 9.5, "usda"),
    ("Riso rosso (Camargue), crudo", "Red Camargue rice, raw", 1, 349, 7.5, 74.0, 2.8, 0.0, 0.6, 3.5, 3, 11.0, "usda"),
    ("Farro spelta, chicchi crudi", "Spelt wheat grains, raw", 1, 338, 14.6, 68.5, 2.4, 0.0, 0.4, 10.7, 8, 11.0, "crea"),

    # ── CAT 3: Pane e forno ───────────────────────────────────────────────────
    ("Panino al sesamo", "Sesame seed burger bun", 3, 298, 9.5, 53.5, 5.5, 5.0, 1.2, 3.0, 450, 31.0, "usda"),
    ("Pane tipo pugliese (semola rimacinata)", "Apulian-style remilled semolina bread", 3, 281, 9.0, 57.5, 1.5, 1.5, 0.3, 3.2, 465, 30.0, "crea"),
    ("Pane di mais senza glutine", "Gluten-free corn bread", 3, 265, 4.5, 52.0, 5.0, 5.0, 1.0, 2.5, 430, 36.0, "usda"),
    ("Pane di segale compatto (tipo wasa)", "Compact rye crispbread (Wasa-style)", 3, 335, 10.0, 71.0, 1.5, 1.5, 0.2, 13.5, 330, 8.0, "crea"),
    ("Tortino di mais (polenta al forno)", "Baked polenta cake", 3, 160, 3.5, 31.0, 2.5, 1.0, 0.8, 1.5, 220, 62.0, "crea"),

    # ── CAT 4: Legumi ─────────────────────────────────────────────────────────
    ("Zuppa di lenticchie (piatto pronto)", "Ready lentil soup", 4, 87, 5.5, 13.5, 1.5, 2.0, 0.2, 4.5, 380, 78.0, "crea"),
    ("Passata di ceci (hummus base ridotta)", "Chickpea passata (reduced hummus base)", 4, 120, 6.5, 19.5, 2.5, 0.5, 0.3, 5.5, 35, 72.0, "crea"),
    ("Fagioli al pomodoro (in scatola)", "Baked beans in tomato sauce (canned)", 4, 94, 5.2, 17.5, 0.5, 5.5, 0.1, 3.7, 430, 73.0, "usda"),
    ("Minestrone con legumi (piatto pronto)", "Vegetable and legume minestrone (ready)", 4, 65, 3.5, 11.0, 1.0, 3.0, 0.1, 3.5, 450, 83.0, "crea"),

    # ── CAT 5: Verdure ────────────────────────────────────────────────────────
    ("Cavoletti di Bruxelles arrosto", "Roasted Brussels sprouts", 5, 55, 3.5, 9.0, 1.5, 2.0, 0.3, 4.5, 30, 83.0, "usda"),
    ("Zucca gialla, gratinata al forno", "Baked gratinated yellow pumpkin", 5, 52, 1.5, 11.5, 0.5, 3.5, 0.1, 2.0, 15, 84.0, "crea"),
    ("Patate al vapore (no sale)", "Steamed potatoes (no salt)", 5, 75, 2.0, 17.0, 0.1, 0.8, 0.0, 1.8, 4, 80.5, "crea"),
    ("Broccoli romanesco, crudi", "Romanesco broccoli, raw", 5, 28, 2.9, 5.0, 0.2, 2.0, 0.0, 2.5, 23, 91.5, "crea"),
    ("Cipolla di Tropea, cruda", "Tropea red onion, raw", 5, 38, 1.0, 8.8, 0.1, 5.5, 0.0, 1.5, 3, 90.0, "crea"),
    ("Peperone rosso arrostito (in vasetto)", "Roasted red pepper in jar", 5, 35, 1.0, 7.5, 0.5, 5.0, 0.1, 1.5, 350, 89.0, "crea"),
    ("Pomodori datterini, freschi", "Datterini (finger) tomatoes, fresh", 5, 20, 0.9, 4.3, 0.2, 2.9, 0.0, 1.0, 5, 94.0, "crea"),
    ("Friggitelli (peperoni piccoli verdi)", "Friggitello small green peppers", 5, 23, 1.2, 4.5, 0.4, 2.5, 0.0, 2.0, 5, 92.5, "crea"),
    ("Bietola rossa, cruda", "Red chard, raw", 5, 19, 1.8, 3.8, 0.2, 1.1, 0.0, 1.6, 213, 92.7, "crea"),
    ("Zucchine lunghe (romanesche)", "Roman long zucchini", 5, 16, 1.1, 2.8, 0.3, 2.0, 0.0, 1.2, 6, 94.5, "crea"),
    ("Peperoni gialli arrostiti", "Roasted yellow peppers", 5, 36, 1.0, 8.0, 0.3, 5.5, 0.0, 1.5, 5, 88.5, "crea"),
    ("Pomodori ramati, freschi", "Vine tomatoes (ramati), fresh", 5, 19, 0.9, 4.0, 0.2, 2.7, 0.0, 1.1, 4, 94.2, "crea"),
    ("Insalata di finocchi e arance", "Fennel and orange salad (no dressing)", 5, 42, 1.0, 9.8, 0.2, 6.5, 0.0, 2.5, 30, 87.5, "crea"),

    # ── CAT 6: Frutta ─────────────────────────────────────────────────────────
    ("Fico d'India (ficodindia), polpa", "Prickly pear flesh", 6, 50, 0.7, 11.3, 0.5, 7.1, 0.0, 3.6, 5, 87.5, "crea"),
    ("Corbezzolo, fresco", "Arbutus berry (strawberry tree), fresh", 6, 83, 0.7, 20.0, 0.5, 0.0, 0.1, 4.0, 2, 78.0, "crea"),
    ("Bacche di acai (polvere, 100%)", "Acai berry powder (100%)", 6, 534, 8.1, 35.7, 32.5, 0.0, 7.7, 44.2, 9, 7.6, "usda"),
    ("Bacche di goji, essiccate", "Dried goji berries", 6, 349, 14.3, 77.1, 0.4, 45.6, 0.0, 13.0, 298, 7.5, "usda"),
    ("Bacche di aronia (chokeberry)", "Aronia (chokeberry) berries", 6, 47, 1.4, 9.6, 0.5, 4.3, 0.0, 5.3, 1, 80.3, "usda"),
    ("Mela rossa (Fuji), fresca", "Fuji apple, fresh", 6, 53, 0.3, 14.0, 0.2, 10.4, 0.0, 2.4, 1, 85.6, "usda"),
    ("Mela verde (Granny Smith), fresca", "Granny Smith apple, fresh", 6, 53, 0.4, 13.6, 0.2, 9.6, 0.0, 2.8, 1, 85.9, "usda"),
    ("Pera Williams, fresca", "Williams pear, fresh", 6, 57, 0.4, 15.5, 0.1, 9.8, 0.0, 3.1, 1, 83.8, "crea"),
    ("Pesca bianca, fresca", "White peach, fresh", 6, 39, 0.9, 9.5, 0.3, 8.4, 0.0, 1.5, 0, 89.3, "crea"),
    ("Pesca tabacchiera, fresca", "Flat (donut) peach, fresh", 6, 40, 0.9, 9.5, 0.3, 8.4, 0.0, 1.5, 0, 89.0, "crea"),

    # ── CAT 7: Frutta secca ───────────────────────────────────────────────────
    ("Mandorle pelate e blanched", "Blanched almonds", 7, 576, 21.9, 18.7, 50.6, 4.4, 3.8, 11.8, 1, 4.7, "usda"),
    ("Nocciole fresche (non tostate)", "Fresh hazelnuts (raw)", 7, 628, 15.0, 16.7, 60.8, 4.3, 4.5, 9.7, 0, 5.3, "crea"),
    ("Farro soffiato", "Puffed spelt", 7, 365, 14.0, 72.0, 2.5, 0.5, 0.4, 8.5, 5, 9.0, "crea"),
    ("Riso soffiato", "Puffed rice", 7, 381, 6.0, 87.0, 0.5, 0.5, 0.1, 0.5, 4, 6.0, "usda"),
    ("Mais soffiato (popcorn commercial)", "Commercial popcorn (butter flavored)", 7, 500, 8.0, 60.0, 28.0, 0.5, 14.0, 10.0, 730, 3.0, "usda"),

    # ── CAT 8: Carne ──────────────────────────────────────────────────────────
    ("Pollo in scatola (al naturale)", "Canned chicken breast (in water)", 8, 110, 23.5, 0.5, 1.5, 0.3, 0.4, 0.0, 310, 74.0, "usda"),
    ("Tonno-pollo proteico (piatto mix)", "Tuna-chicken protein mix (meal prep)", 8, 120, 24.0, 0.5, 2.5, 0.2, 0.6, 0.0, 380, 72.5, "usda"),
    ("Hamburger di manzo (80% magro)", "Beef burger patty (80% lean)", 8, 245, 20.0, 0.0, 18.0, 0.0, 7.0, 0.0, 65, 60.5, "usda"),
    ("Hamburger di pollo (grigliato)", "Grilled chicken burger patty", 8, 150, 27.0, 0.5, 4.5, 0.3, 1.3, 0.0, 80, 67.5, "usda"),
    ("Polpette di carne al sugo (cotte)", "Meatballs in tomato sauce (cooked)", 8, 195, 14.5, 7.5, 12.5, 3.5, 4.0, 0.5, 350, 64.0, "crea"),
    ("Scaloppina di vitello al marsala", "Veal scallopini with Marsala (cooked)", 8, 168, 21.5, 3.5, 7.5, 1.5, 2.5, 0.0, 320, 66.0, "crea"),
    ("Pollo tikka masala (piatto indiano)", "Chicken tikka masala (Indian dish)", 8, 150, 15.5, 9.0, 6.5, 4.0, 2.5, 0.5, 450, 67.0, "usda"),

    # ── CAT 9: Salumi ─────────────────────────────────────────────────────────
    ("Prosciutto crudo magro affettato (packed)", "Lean packaged sliced prosciutto crudo", 9, 140, 26.5, 0.5, 3.5, 0.3, 1.2, 0.0, 1900, 68.0, "crea"),
    ("Salume di cinghiale", "Wild boar salumi", 9, 390, 25.0, 0.5, 33.0, 0.3, 11.0, 0.0, 1450, 38.0, "crea"),
    ("Salamella (salsiccia tipo mantovana)", "Salamella sausage (Mantua-style)", 9, 360, 18.0, 0.5, 32.0, 0.3, 11.5, 0.0, 1200, 44.0, "crea"),
    ("Zampone di Modena IGP (cotto)", "Cooked Zampone di Modena IGP", 9, 360, 15.0, 0.5, 33.5, 0.0, 12.5, 0.0, 1050, 48.0, "crea"),
    ("Petto di pollo arrosto (affettato, packed)", "Sliced roast chicken breast (packed)", 9, 105, 22.0, 1.0, 1.8, 0.8, 0.5, 0.0, 700, 75.0, "crea"),

    # ── CAT 10: Prodotti ittici ────────────────────────────────────────────────
    ("Mazzancolle (gamberi grandi), cotte", "Cooked large prawns (mazzancolle)", 10, 98, 20.8, 0.0, 1.5, 0.0, 0.3, 0.0, 220, 76.5, "crea"),
    ("Scampi fritti (impanati)", "Breaded fried scampi", 10, 240, 16.0, 18.5, 10.5, 0.5, 2.0, 0.8, 480, 55.0, "crea"),
    ("Baccalà alla vicentina (piatto cotto)", "Baccalà alla vicentina (cooked dish)", 10, 155, 18.5, 3.5, 8.0, 0.5, 1.5, 0.0, 680, 67.0, "crea"),
    ("Tonno in scatola al naturale (sgocciolato)", "Drained canned tuna in water", 10, 103, 23.5, 0.0, 1.0, 0.0, 0.3, 0.0, 330, 74.0, "crea"),
    ("Sardine grigliate", "Grilled sardines", 10, 185, 24.0, 0.0, 10.0, 0.0, 2.5, 0.0, 95, 64.5, "crea"),
    ("Sgombro in scatola al naturale", "Canned mackerel in water", 10, 156, 21.0, 0.0, 8.0, 0.0, 2.4, 0.0, 400, 69.0, "crea"),
    ("Ostriche gratinate al forno", "Baked gratinated oysters", 10, 95, 9.5, 5.5, 4.0, 0.5, 1.0, 0.0, 390, 78.0, "crea"),
    ("Ceviche di branzino (piatto crudo)", "Sea bass ceviche", 10, 85, 15.5, 3.5, 1.5, 1.5, 0.3, 0.5, 350, 78.0, "usda"),

    # ── CAT 12: Latticini ─────────────────────────────────────────────────────
    ("Caciocavallo podolico stagionato", "Aged caciocavallo podolico cheese", 12, 415, 30.5, 1.0, 32.5, 0.5, 21.0, 0.0, 980, 31.0, "crea"),
    ("Pecorino di Pienza", "Pienza Pecorino cheese", 12, 405, 24.0, 0.5, 34.5, 0.3, 23.0, 0.0, 1750, 30.0, "crea"),
    ("Mozzarella affumicata", "Smoked mozzarella", 12, 290, 20.0, 2.5, 22.5, 0.8, 14.5, 0.0, 780, 54.0, "crea"),
    ("Yogurt greco proteico (15g prot/100g)", "High-protein Greek yogurt (15g prot)", 12, 90, 15.0, 4.5, 0.5, 3.5, 0.3, 0.0, 52, 79.0, "usda"),
    ("Ricotta al forno (siciliana)", "Sicilian baked ricotta", 12, 200, 14.5, 3.0, 14.5, 2.5, 9.5, 0.0, 330, 65.0, "crea"),

    # ── CAT 13: Condimenti ────────────────────────────────────────────────────
    ("Olio di ribes nero (omega-6)", "Black currant seed oil (omega-6)", 13, 884, 0.0, 0.0, 100.0, 0.0, 7.2, 0.0, 0, 0.0, "usda"),
    ("Salsa di ostrica", "Oyster sauce", 13, 73, 3.0, 14.5, 0.5, 7.0, 0.1, 0.5, 2733, 80.0, "usda"),
    ("Olio di canapa", "Hemp seed oil", 13, 884, 0.0, 0.0, 100.0, 0.0, 9.7, 0.0, 0, 0.0, "usda"),
    ("Salsa harissa (pasta di peperoncino)", "Harissa chili paste", 13, 95, 2.5, 10.5, 5.5, 5.5, 0.8, 3.5, 2050, 75.0, "usda"),
    ("Aceto di riso (giapponese)", "Japanese rice vinegar", 13, 18, 0.0, 0.6, 0.0, 0.6, 0.0, 0.0, 2, 99.0, "usda"),

    # ── CAT 14: Dolci ─────────────────────────────────────────────────────────
    ("Ciambelle glassate (donuts)", "Glazed donuts", 14, 424, 4.9, 51.3, 22.8, 22.0, 9.7, 1.1, 320, 19.0, "usda"),
    ("Cheesecake (fetta, base biscotto)", "Cheesecake slice (cookie crust)", 14, 321, 5.5, 30.0, 20.5, 20.5, 11.5, 0.3, 260, 41.0, "usda"),
    ("Cioccolato fondente proteico (>25% prot)", "High-protein dark chocolate (>25% prot)", 14, 445, 25.0, 40.0, 20.0, 10.0, 12.0, 8.0, 150, 5.0, "usda"),
    ("Granita al limone (senza latte)", "Lemon granita (dairy-free)", 14, 85, 0.1, 21.5, 0.0, 20.0, 0.0, 0.2, 8, 78.0, "crea"),
    ("Crema di marroni (crema di castagne)", "Chestnut cream (sweetened)", 14, 250, 2.5, 60.0, 1.5, 45.0, 0.3, 4.5, 20, 33.0, "crea"),

    # ── CAT 15: Bevande ───────────────────────────────────────────────────────
    ("Latte di nocciole non zuccherato", "Unsweetened hazelnut milk", 15, 28, 0.5, 2.5, 2.0, 1.0, 0.2, 0.4, 55, 95.0, "usda"),
    ("Succo di kiwi (100% frutto)", "Pure kiwi juice (100% fruit)", 15, 45, 0.7, 10.5, 0.3, 8.5, 0.0, 1.5, 10, 88.5, "usda"),
    ("Smoothie verde (spinaci+mela+zenzero)", "Green smoothie (spinach+apple+ginger)", 15, 38, 1.0, 8.5, 0.3, 6.0, 0.0, 1.5, 20, 90.0, "usda"),
    ("Acqua di cocco (100% naturale)", "Coconut water (100% natural)", 15, 19, 0.7, 3.7, 0.2, 2.6, 0.0, 0.0, 105, 95.0, "usda"),
    ("Tisana di finocchio e anice", "Fennel and anise herbal tea", 15, 2, 0.1, 0.4, 0.0, 0.0, 0.0, 0.0, 2, 99.5, "crea"),
    ("Tisana di orzo (caffe' d'orzo)", "Barley coffee (orzo)", 15, 8, 0.4, 1.5, 0.1, 0.0, 0.0, 0.0, 5, 98.0, "crea"),
    ("Smoothie proteico (whey+banana+latte)", "Protein smoothie (whey+banana+milk)", 15, 85, 8.5, 10.5, 1.5, 7.0, 0.9, 0.5, 65, 78.0, "usda"),
    ("Red bull (energy drink 250ml/100ml)", "Red Bull energy drink (per 100ml)", 15, 45, 0.5, 11.0, 0.0, 11.0, 0.0, 0.0, 40, 88.5, "usda"),
    ("Succo di limone (puro, senza zucchero)", "Pure unsweetened lemon juice", 15, 25, 0.4, 8.0, 0.3, 2.5, 0.0, 0.3, 1, 91.3, "crea"),
    ("Sprite / gassosa (100ml)", "Lemon-lime soda (100ml)", 15, 42, 0.0, 10.5, 0.0, 10.5, 0.0, 0.0, 20, 89.5, "usda"),
    ("Cola (100ml)", "Cola drink (100ml)", 15, 42, 0.0, 10.6, 0.0, 10.6, 0.0, 0.0, 4, 89.0, "usda"),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT nome FROM alimenti")
    existing = {r[0] for r in c.fetchall()}

    inserted = 0
    skipped = 0

    for row in FOODS:
        (nome, nome_en, cat_id, kcal, prot, carb, grassi,
         zuccheri, saturi, fibra, sodio, acqua, source) = row

        if nome in existing:
            skipped += 1
            continue

        c.execute("""
            INSERT INTO alimenti
              (nome, nome_en, categoria_id,
               energia_kcal, proteine_g, carboidrati_g, grassi_g,
               di_cui_zuccheri_g, di_cui_saturi_g, fibra_g, sodio_mg, acqua_g,
               source, is_active)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1)
        """, (nome, nome_en, cat_id, kcal, prot, carb, grassi,
              zuccheri, saturi, fibra, sodio, acqua, source))
        existing.add(nome)
        inserted += 1

    conn.commit()

    c.execute("SELECT COUNT(*) FROM alimenti")
    total = c.fetchone()[0]

    # Riepilogo per categoria
    print(f"\nInseriti: {inserted} | Saltati: {skipped} | Totale DB: {total}\n")
    print("Alimenti per categoria:")
    c.execute("""
        SELECT c.nome, COUNT(a.id)
        FROM alimenti a
        JOIN categorie_alimenti c ON a.categoria_id = c.id
        GROUP BY c.id
        ORDER BY c.id
    """)
    for cat, count in c.fetchall():
        print(f"  {cat}: {count}")

    conn.close()


if __name__ == "__main__":
    seed()
