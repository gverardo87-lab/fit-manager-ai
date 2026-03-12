"""
Quarto blocco seed — da ~834 a ~900 alimenti.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "nutrition.db"

FOODS = [
    # Cereali
    ("Pasta di lenticchie rosse, secca", "Red lentil pasta, dry", 1, 342, 25.0, 55.0, 2.0, 1.0, 0.3, 9.5, 20, 10.0, "usda"),
    ("Chapati (pane indiano integrale)", "Wholemeal chapati bread", 1, 330, 11.0, 62.0, 5.0, 1.5, 0.8, 7.0, 290, 19.0, "usda"),
    ("Tortilla di farro", "Spelt flour tortilla", 1, 310, 10.0, 53.0, 7.0, 2.0, 2.3, 5.5, 490, 28.0, "crea"),

    # Cereali cotti
    ("Teff, cotto", "Teff, cooked", 2, 101, 3.9, 19.9, 0.7, 0.0, 0.1, 2.8, 5, 75.2, "usda"),
    ("Sorgo, cotto", "Sorghum, cooked", 2, 119, 3.9, 27.0, 1.3, 0.8, 0.2, 2.5, 5, 67.5, "usda"),

    # Pane e forno
    ("Pane di patate", "Potato bread", 3, 266, 8.0, 52.5, 3.0, 4.5, 0.8, 2.0, 430, 33.5, "usda"),
    ("Crumble di avena (base dolce)", "Oat crumble topping", 3, 435, 6.0, 55.0, 22.0, 15.0, 10.0, 3.5, 120, 10.0, "usda"),
    ("Biscotto al cocco (tipo Oro Saiwa)", "Coconut cookie", 3, 487, 5.5, 71.0, 20.0, 36.0, 17.0, 3.5, 220, 3.5, "crea"),

    # Legumi
    ("Fagiolini in scatola (sgocciolati)", "Canned green beans, drained", 4, 25, 1.8, 5.0, 0.2, 1.5, 0.0, 3.2, 265, 91.5, "usda"),
    ("Piselli primavera surgelati (cotti)", "Frozen spring peas, cooked", 4, 69, 5.0, 11.5, 0.4, 4.0, 0.1, 5.5, 3, 79.5, "crea"),
    ("Ceci al curry (piatto pronto)", "Chickpea curry (ready meal)", 4, 115, 5.5, 15.0, 4.5, 3.5, 0.8, 4.5, 520, 73.0, "usda"),
    ("Zuppa di fagioli neri", "Black bean soup", 4, 80, 4.8, 14.0, 0.8, 1.5, 0.1, 5.5, 410, 80.5, "usda"),

    # Verdure
    ("Rucola selvaggia (wild rocket)", "Wild rocket (arugula)", 5, 25, 2.6, 3.6, 0.7, 2.0, 0.1, 1.6, 27, 91.7, "crea"),
    ("Cavolo nero toscano (crudo)", "Tuscan black kale (raw)", 5, 49, 4.3, 8.8, 0.9, 2.0, 0.1, 3.6, 38, 84.5, "crea"),
    ("Cavolo nero toscano (cotto)", "Tuscan black kale (cooked)", 5, 28, 2.5, 4.8, 0.5, 0.8, 0.1, 2.0, 30, 91.5, "crea"),
    ("Erba cipollina, fresca", "Fresh chives", 5, 30, 3.3, 4.4, 0.7, 1.9, 0.1, 2.5, 3, 90.6, "usda"),
    ("Menta fresca", "Fresh mint", 5, 70, 3.8, 14.9, 0.9, 0.2, 0.2, 8.0, 31, 78.7, "usda"),
    ("Rosmarino fresco", "Fresh rosemary", 5, 131, 3.3, 20.7, 5.9, 0.0, 2.8, 14.1, 26, 67.8, "usda"),
    ("Timo fresco", "Fresh thyme", 5, 101, 5.6, 24.5, 1.7, 0.0, 0.5, 14.0, 9, 65.1, "usda"),
    ("Origano fresco", "Fresh oregano", 5, 265, 9.0, 68.9, 4.3, 0.0, 1.5, 42.5, 25, 9.9, "usda"),

    # Frutta
    ("Litchi essiccato", "Dried lychee", 6, 277, 3.8, 70.0, 1.2, 0.0, 0.3, 0.0, 3, 20.0, "usda"),
    ("Kaki essiccato (hoshigaki)", "Hoshigaki dried persimmon", 6, 274, 1.4, 71.3, 0.6, 59.0, 0.0, 14.5, 2, 25.0, "usda"),
    ("Ribes nero (succo, senza zucchero)", "Blackcurrant juice (unsweetened)", 6, 45, 1.0, 11.0, 0.2, 8.5, 0.0, 3.5, 2, 87.5, "usda"),
    ("Giuggiola fresca tipo cinese", "Chinese jujube, fresh", 6, 79, 1.2, 20.2, 0.2, 0.0, 0.0, 0.0, 3, 77.9, "usda"),
    ("Carambola (starfruit) essiccata", "Dried starfruit", 6, 220, 2.5, 55.0, 0.8, 38.0, 0.0, 12.0, 5, 20.0, "usda"),

    # Frutta secca
    ("Fave di cacao tostate (cacao nibs)", "Roasted cacao nibs", 7, 480, 13.5, 53.7, 43.1, 0.5, 26.0, 33.2, 14, 3.0, "usda"),
    ("Noci di Grenoble (noci francesi)", "Grenoble walnuts", 7, 654, 15.2, 13.7, 65.2, 2.6, 6.1, 6.7, 2, 4.1, "usda"),
    ("Arachidi con guscio (crude)", "Raw peanuts in shell", 7, 567, 25.8, 16.1, 49.2, 4.7, 6.8, 8.5, 18, 6.5, "crea"),
    ("Mix di semi (chia+lino+zucca+girasole)", "Mixed seeds (chia+flax+pumpkin+sunflower)", 7, 520, 20.0, 20.0, 41.0, 1.5, 6.0, 15.0, 20, 6.5, "usda"),

    # Carne
    ("Agnello, macinato cotto", "Ground lamb, cooked", 8, 320, 25.5, 0.0, 24.5, 0.0, 11.5, 0.0, 85, 52.0, "usda"),
    ("Struzzo, filetto cotto", "Ostrich fillet, cooked", 8, 148, 28.5, 0.0, 3.5, 0.0, 0.9, 0.0, 75, 66.0, "usda"),
    ("Coniglio, dorso cotto", "Rabbit back (saddle), cooked", 8, 175, 25.0, 0.0, 8.5, 0.0, 2.5, 0.0, 68, 65.0, "crea"),
    ("Cervo, coscia cotta", "Venison leg, cooked", 8, 158, 29.5, 0.0, 4.5, 0.0, 1.6, 0.0, 64, 65.0, "crea"),
    ("Anatra, petto cotto al forno", "Baked duck breast", 8, 201, 28.5, 0.0, 9.5, 0.0, 3.0, 0.0, 79, 60.5, "usda"),

    # Salumi
    ("Testa in cassetta (headcheese)", "Headcheese (testa in cassetta)", 9, 285, 17.0, 0.5, 23.5, 0.3, 8.5, 0.0, 1200, 56.0, "crea"),
    ("Coppa di testa", "Head sausage (coppa di testa)", 9, 305, 16.5, 0.5, 26.5, 0.3, 9.5, 0.0, 1100, 54.0, "crea"),
    ("Salsiccia di pollo e tacchino", "Chicken and turkey sausage", 9, 188, 16.0, 2.5, 13.0, 1.5, 3.8, 0.0, 780, 68.0, "usda"),

    # Prodotti ittici
    ("Anguilla affumicata", "Smoked eel", 10, 290, 18.5, 0.0, 24.0, 0.0, 5.0, 0.0, 700, 56.5, "crea"),
    ("Acciughe in pasta (tubo)", "Anchovy paste (tube)", 10, 210, 22.0, 2.0, 13.5, 0.5, 3.5, 0.0, 3200, 60.0, "crea"),
    ("Salmone teriyaki al forno", "Teriyaki baked salmon", 10, 195, 22.5, 8.5, 8.0, 7.0, 1.8, 0.0, 720, 60.5, "usda"),
    ("Branzino al cartoccio (cotto)", "Sea bass en papillote (cooked)", 10, 118, 22.0, 0.5, 3.5, 0.2, 0.8, 0.0, 95, 73.0, "crea"),
    ("Mazzancolle al vapore", "Steamed mazzancolle prawns", 10, 85, 18.5, 0.0, 1.2, 0.0, 0.2, 0.0, 185, 79.5, "crea"),

    # Latticini
    ("Caciotta fresca (tipo formaggella)", "Fresh caciotta cheese (formaggella)", 12, 245, 18.5, 2.5, 18.5, 1.5, 12.0, 0.0, 580, 55.0, "crea"),
    ("Latte intero UHT", "UHT whole milk", 12, 64, 3.2, 4.9, 3.7, 4.9, 2.4, 0.0, 44, 87.7, "crea"),
    ("Panna acida (sour cream)", "Sour cream", 12, 193, 2.9, 4.3, 19.4, 3.5, 12.0, 0.0, 57, 72.5, "usda"),
    ("Yogurt al frutto di bosco (magro)", "Low-fat mixed berry yogurt", 12, 80, 4.0, 13.5, 0.5, 11.5, 0.3, 0.5, 55, 80.0, "crea"),
    ("Kefir di acqua (water kefir)", "Water kefir", 12, 25, 0.1, 6.0, 0.0, 5.5, 0.0, 0.0, 5, 94.0, "usda"),

    # Condimenti
    ("Salsa di pomodoro fresco (bruschetta)", "Fresh tomato bruschetta sauce", 13, 65, 1.5, 7.5, 3.5, 4.5, 0.5, 1.2, 380, 85.0, "crea"),
    ("Crema di aceto balsamico", "Balsamic vinegar cream", 13, 182, 0.5, 44.5, 0.0, 42.0, 0.0, 0.0, 35, 52.5, "crea"),
    ("Senape di Digione", "Dijon mustard", 13, 77, 5.1, 5.8, 4.0, 1.0, 0.3, 1.2, 1020, 82.0, "usda"),
    ("Salsa barbecue (classica)", "Classic BBQ sauce", 13, 172, 1.4, 41.0, 0.5, 32.0, 0.1, 0.5, 820, 55.0, "usda"),

    # Dolci
    ("Coppetta di gelato (2 palline tipo)", "Ice cream cup (2 scoops, average)", 14, 200, 4.0, 26.0, 9.5, 21.0, 5.8, 0.0, 82, 58.5, "crea"),
    ("Bignè alla crema", "Cream puff (choux pastry with cream)", 14, 315, 5.5, 31.5, 19.0, 15.0, 8.5, 0.5, 120, 42.0, "crea"),
    ("Sfogliatella napoletana", "Neapolitan sfogliatella pastry", 14, 340, 7.0, 50.5, 12.5, 15.5, 5.0, 1.5, 280, 30.0, "crea"),
    ("Croissant integrale (whole wheat)", "Whole wheat croissant", 14, 390, 8.5, 52.5, 17.0, 12.0, 7.5, 3.5, 280, 19.0, "usda"),
    ("Torta di mele (classica)", "Classic apple cake", 14, 290, 4.5, 47.5, 10.0, 25.5, 3.5, 1.5, 180, 35.0, "crea"),

    # Bevande
    ("Succo di uva nera (100%)", "Pure black grape juice (100%)", 15, 67, 0.4, 16.2, 0.2, 14.8, 0.0, 0.2, 9, 82.9, "usda"),
    ("Succo di pera (100%)", "Pure pear juice (100%)", 15, 48, 0.2, 12.0, 0.1, 10.5, 0.0, 0.2, 3, 87.5, "usda"),
    ("Latte caldo con cacao (cioccolata calda)", "Hot cocoa with milk", 15, 78, 4.0, 10.0, 2.5, 8.0, 1.5, 0.8, 52, 82.5, "crea"),
    ("Frullato di banana e mandorle", "Banana almond smoothie", 15, 92, 2.5, 16.5, 2.5, 9.5, 0.3, 1.5, 25, 78.0, "usda"),
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
    print(f"Inseriti: {inserted} | Saltati: {skipped} | Totale finale DB: {total}")

    conn.close()


if __name__ == "__main__":
    seed()
