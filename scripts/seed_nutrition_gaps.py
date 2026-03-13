"""
seed_nutrition_gaps.py — Aggiunge alimenti mancanti critici per il generatore LARN.

Alimenti identificati dall'analisi dei warning del frequency_validator:
- Formaggi (parmigiano, mozzarella) per coprire "formaggio_fresco/stagionato"
- Patate per coprire "patate" nel gruppo cereali/tuberi
- Tofu/Tempeh per profili vegetariani
- Piatti composti base (frittata, insalata mista) per S2

Formato: stesso di build_nutrition.py — tupla 29 campi per 100g edibile.
Fonte: CREA 2019 / USDA FoodData Central.

Utilizzo:
  python -m scripts.seed_nutrition_gaps              # Aggiunge alimenti
  python -m scripts.seed_nutrition_gaps --dry-run     # Solo conta
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from api.config import NUTRITION_DATABASE_URL
from api.database import create_nutrition_tables, nutrition_engine
from api.models.nutrition import Food, FoodCategory, StandardPortion
from sqlmodel import Session, select


# ---------------------------------------------------------------------------
# Alimenti mancanti — 29 campi per 100g edibile
# (nome, cat_nome, kcal, prot, carb, gras, zucch, satur, fibra, sodio,
#  acqua, colest, calcio, ferro, zinco, mg, P, K, Se, vitA, vitD, vitE,
#  vitC, B1, B2, B3, B6, B9, B12)
# ---------------------------------------------------------------------------

NEW_FOODS = [
    # ── Tuberi ──
    ("Patate, bollite", "Verdure e ortaggi", 86, 1.7, 20.1, 0.1, 0.8, 0.0, 1.8, 4, 77.0, 0,
     5, 0.3, 0.3, 22, 40, 328, 0.3, 0, 0, 0.0, 7.4, 0.11, 0.02, 1.4, 0.30, 9, 0),

    # ── Formaggi (mancanti nei pool) ──
    ("Ricotta di vaccino, fresca", "Latte, yogurt e formaggi", 146, 8.0, 3.5, 11.5, 3.5, 7.2, 0, 78, 75.7, 36,
     207, 0.4, 1.2, 11, 153, 105, 14, 120, 0.3, 0.3, 0, 0.02, 0.19, 0.1, 0.04, 12, 0.5),

    ("Stracchino (crescenza)", "Latte, yogurt e formaggi", 300, 18.5, 0.0, 25.1, 0.0, 16.1, 0, 450, 53.5, 68,
     567, 0.1, 2.2, 14, 285, 117, 8, 288, 0.3, 0.5, 0, 0.03, 0.29, 0.2, 0.06, 14, 1.1),

    ("Scamorza", "Latte, yogurt e formaggi", 334, 25.0, 1.0, 25.6, 0.5, 16.5, 0, 512, 44.0, 73,
     512, 0.2, 3.4, 21, 430, 100, 11, 235, 0.3, 0.5, 0, 0.02, 0.22, 0.1, 0.06, 8, 1.5),

    ("Pecorino romano", "Latte, yogurt e formaggi", 387, 31.8, 0.0, 28.6, 0.0, 18.3, 0, 1200, 30.7, 104,
     1160, 0.5, 3.5, 39, 780, 92, 15, 195, 0.5, 0.6, 0, 0.05, 0.37, 0.2, 0.08, 7, 1.2),

    ("Emmentaler", "Latte, yogurt e formaggi", 403, 28.7, 0.0, 31.8, 0.0, 19.5, 0, 450, 35.7, 100,
     1030, 0.3, 4.6, 37, 637, 119, 12, 310, 1.1, 0.6, 0, 0.06, 0.34, 0.1, 0.08, 20, 3.0),

    # ── Proteine vegetali ──
    ("Tofu al naturale", "Legumi", 76, 8.1, 1.9, 4.8, 0.5, 0.7, 0.3, 7, 84.6, 0,
     350, 5.4, 0.8, 30, 97, 121, 9, 0, 0, 0.0, 0, 0.07, 0.05, 0.2, 0.05, 15, 0),

    ("Tempeh", "Legumi", 192, 20.3, 7.6, 10.8, 0.0, 2.5, 5.0, 9, 59.6, 0,
     111, 2.7, 1.1, 81, 266, 412, 0, 0, 0, 0.0, 0, 0.08, 0.36, 2.6, 0.22, 24, 0.1),

    # ── Verdure mancanti ──
    ("Melanzane, cotte", "Verdure e ortaggi", 33, 0.8, 8.1, 0.2, 3.2, 0.0, 2.5, 1, 89.7, 0,
     6, 0.3, 0.1, 11, 15, 123, 0.1, 1, 0, 0.0, 1.3, 0.08, 0.02, 0.6, 0.09, 14, 0),

    ("Cavolfiore, cotto", "Verdure e ortaggi", 23, 1.8, 4.1, 0.5, 2.1, 0.1, 2.3, 15, 93.0, 0,
     16, 0.3, 0.2, 9, 32, 142, 0.6, 1, 0, 0.1, 44.3, 0.04, 0.05, 0.4, 0.17, 44, 0),

    ("Verza, cotta", "Verdure e ortaggi", 23, 1.3, 5.4, 0.1, 2.6, 0.0, 2.3, 12, 92.6, 0,
     48, 0.2, 0.2, 12, 33, 196, 0.6, 50, 0, 0.1, 37.5, 0.06, 0.04, 0.2, 0.13, 30, 0),

    ("Carciofi, cotti", "Verdure e ortaggi", 50, 2.9, 11.2, 0.3, 0.9, 0.1, 5.7, 60, 84.1, 0,
     21, 0.6, 0.4, 42, 73, 286, 0.2, 1, 0, 0.2, 7.4, 0.05, 0.09, 1.0, 0.08, 89, 0),

    ("Sedano, crudo", "Verdure e ortaggi", 16, 0.7, 3.0, 0.2, 1.3, 0.0, 1.6, 80, 95.4, 0,
     40, 0.2, 0.1, 11, 24, 260, 0.4, 22, 0, 0.3, 3.1, 0.02, 0.06, 0.3, 0.07, 36, 0),

    # ── Frutta mancante ──
    ("Uva, fresca", "Frutta fresca", 69, 0.7, 18.1, 0.2, 15.5, 0.1, 0.9, 2, 80.5, 0,
     10, 0.4, 0.1, 7, 20, 191, 0.1, 3, 0, 0.2, 3.2, 0.07, 0.07, 0.2, 0.09, 2, 0),

    ("Mandarino, fresco", "Frutta fresca", 53, 0.8, 13.3, 0.3, 10.6, 0.0, 1.8, 2, 85.2, 0,
     37, 0.2, 0.1, 12, 20, 166, 0.1, 34, 0, 0.2, 26.7, 0.06, 0.03, 0.4, 0.08, 16, 0),

    ("Albicocca, fresca", "Frutta fresca", 48, 1.4, 11.1, 0.4, 9.2, 0.0, 2.0, 1, 86.4, 0,
     13, 0.4, 0.2, 10, 23, 259, 0.1, 96, 0, 0.9, 10.0, 0.03, 0.04, 0.6, 0.05, 9, 0),

    # ── Pesce mancante ──
    ("Platessa, filetto cotto", "Prodotti ittici", 86, 18.8, 0.0, 1.2, 0.0, 0.3, 0, 296, 79.6, 48,
     22, 0.2, 0.5, 29, 195, 320, 45, 10, 3.8, 0.6, 0, 0.06, 0.07, 2.4, 0.22, 8, 1.5),

    ("Gamberi, cotti", "Prodotti ittici", 99, 20.9, 0.2, 1.1, 0.0, 0.3, 0, 224, 77.3, 195,
     52, 2.4, 1.6, 34, 200, 182, 38, 1, 0, 1.0, 0, 0.02, 0.03, 2.6, 0.10, 3, 1.9),

    ("Sardine, fresche crude", "Prodotti ittici", 169, 20.9, 0.0, 9.2, 0.0, 2.9, 0, 100, 67.5, 65,
     382, 2.5, 1.3, 39, 490, 397, 53, 32, 4.8, 0.6, 0, 0.07, 0.23, 9.7, 0.17, 15, 8.9),

    # ── Carne mancante ──
    ("Maiale, lonza, cruda", "Carne e pollame", 143, 21.2, 0.0, 6.3, 0.0, 2.2, 0, 54, 72.5, 62,
     7, 0.9, 2.3, 24, 223, 355, 33, 2, 0.5, 0.2, 0.6, 0.91, 0.21, 5.0, 0.54, 5, 0.7),

    ("Coniglio, coscia, crudo", "Carne e pollame", 114, 21.9, 0.0, 2.8, 0.0, 0.8, 0, 47, 74.4, 57,
     10, 1.1, 1.5, 22, 221, 330, 15, 0, 0, 0.1, 0, 0.09, 0.15, 6.5, 0.48, 8, 5.4),

    # ── Pane mancante ──
    ("Pane di farro", "Pane e prodotti da forno", 265, 9.5, 50.0, 2.8, 2.0, 0.5, 5.0, 520, 33.0, 0,
     22, 2.0, 1.5, 50, 140, 200, 20, 0, 0, 0.3, 0, 0.20, 0.08, 3.0, 0.15, 25, 0),

    ("Grissini integrali", "Pane e prodotti da forno", 370, 11.0, 63.0, 8.5, 3.0, 1.2, 6.0, 750, 6.0, 0,
     30, 2.5, 1.8, 60, 150, 200, 25, 0, 0, 1.0, 0, 0.15, 0.08, 3.2, 0.12, 20, 0),
]


# Porzioni standard LARN 2014 per i nuovi alimenti
NEW_PORTIONS = [
    ("Patate, bollite", "1 patata media", 200),
    ("Ricotta di vaccino, fresca", "1 porzione", 100),
    ("Stracchino (crescenza)", "1 porzione", 100),
    ("Scamorza", "1 porzione", 50),
    ("Pecorino romano", "1 porzione", 50),
    ("Emmentaler", "1 porzione", 50),
    ("Tofu al naturale", "1 porzione", 100),
    ("Tempeh", "1 porzione", 100),
    ("Platessa, filetto cotto", "1 porzione", 150),
    ("Gamberi, cotti", "1 porzione", 150),
    ("Sardine, fresche crude", "1 porzione", 150),
    ("Maiale, lonza, cruda", "1 porzione", 100),
    ("Coniglio, coscia, crudo", "1 porzione", 100),
    ("Pane di farro", "1 fetta", 50),
    ("Grissini integrali", "1 porzione", 30),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    create_nutrition_tables()

    with Session(nutrition_engine) as session:
        # Cache categorie
        cats = session.exec(select(FoodCategory)).all()
        cat_map = {c.nome: c.id for c in cats}

        added = 0
        skipped = 0

        for row in NEW_FOODS:
            nome = row[0]
            cat_nome = row[1]

            # Check duplicato
            existing = session.exec(
                select(Food).where(Food.nome == nome)
            ).first()
            if existing:
                skipped += 1
                continue

            cat_id = cat_map.get(cat_nome)
            if not cat_id:
                print(f"SKIP: categoria '{cat_nome}' non trovata per '{nome}'")
                skipped += 1
                continue

            if args.dry_run:
                print(f"  [DRY] {nome} -> cat={cat_nome}")
                added += 1
                continue

            food = Food(
                nome=nome,
                categoria_id=cat_id,
                energia_kcal=row[2],
                proteine_g=row[3],
                carboidrati_g=row[4],
                grassi_g=row[5],
                di_cui_zuccheri_g=row[6] if row[6] else None,
                di_cui_saturi_g=row[7] if row[7] else None,
                fibra_g=row[8] if row[8] else None,
                sodio_mg=row[9] if row[9] else None,
                acqua_g=row[10] if row[10] else None,
                colesterolo_mg=row[11] if row[11] else None,
                calcio_mg=row[12] if row[12] else None,
                ferro_mg=row[13] if row[13] else None,
                zinco_mg=row[14] if row[14] else None,
                magnesio_mg=row[15] if row[15] else None,
                fosforo_mg=row[16] if row[16] else None,
                potassio_mg=row[17] if row[17] else None,
                selenio_ug=row[18] if row[18] else None,
                vitamina_a_ug=row[19] if row[19] else None,
                vitamina_d_ug=row[20] if row[20] else None,
                vitamina_e_mg=row[21] if row[21] else None,
                vitamina_c_mg=row[22] if row[22] else None,
                vitamina_b1_mg=row[23] if row[23] else None,
                vitamina_b2_mg=row[24] if row[24] else None,
                vitamina_b3_mg=row[25] if row[25] else None,
                vitamina_b6_mg=row[26] if row[26] else None,
                vitamina_b9_ug=row[27] if row[27] else None,
                vitamina_b12_ug=row[28] if row[28] else None,
                source="crea",
                is_active=True,
            )
            session.add(food)
            added += 1

        if not args.dry_run:
            session.commit()

            # Porzioni standard
            portions_added = 0
            for food_nome, portion_nome, grammi in NEW_PORTIONS:
                food = session.exec(
                    select(Food).where(Food.nome == food_nome)
                ).first()
                if not food:
                    continue
                existing_p = session.exec(
                    select(StandardPortion).where(
                        StandardPortion.alimento_id == food.id,
                        StandardPortion.nome == portion_nome,
                    )
                ).first()
                if not existing_p:
                    session.add(StandardPortion(
                        alimento_id=food.id,
                        nome=portion_nome,
                        grammi=grammi,
                    ))
                    portions_added += 1
            session.commit()
            print(f"Porzioni standard aggiunte: {portions_added}")

        print(f"Alimenti aggiunti: {added}, saltati: {skipped}")
        print(f"Totale alimenti: {session.exec(select(Food).where(Food.is_active == True)).all().__len__()}")


if __name__ == "__main__":
    main()
