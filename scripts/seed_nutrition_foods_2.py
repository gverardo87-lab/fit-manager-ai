"""
Secondo blocco seed — da ~562 a ~900 alimenti.
Eseguire DOPO seed_nutrition_foods.py.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "nutrition.db"

FOODS = [
    # ── CAT 1: Cereali (ancora) ───────────────────────────────────────────────
    ("Frumento tenero, farina 0", "Wheat flour type 0", 1, 342, 11.5, 72.5, 1.2, 1.5, 0.2, 3.5, 2, 13.8, "crea"),
    ("Frumento tenero, farina 1", "Wheat flour type 1", 1, 339, 12.0, 71.5, 1.4, 1.2, 0.3, 4.5, 2, 13.5, "crea"),
    ("Frumento tenero, farina 2 (semintegrale)", "Semi-wholemeal wheat flour type 2", 1, 337, 12.5, 70.0, 1.7, 1.0, 0.4, 7.0, 2, 13.3, "crea"),
    ("Fiocchi di quinoa", "Quinoa flakes", 1, 368, 14.0, 64.0, 6.0, 1.5, 0.8, 7.0, 5, 9.5, "usda"),
    ("Orzo mondo (integrale), crudo", "Hulled barley, raw", 1, 351, 10.8, 73.5, 2.1, 0.5, 0.4, 17.3, 6, 9.9, "crea"),
    ("Farina di lupini", "Lupin flour", 1, 382, 40.0, 40.0, 9.0, 5.5, 1.2, 34.0, 34, 8.0, "usda"),
    ("Farina di soia sgrassata", "Defatted soy flour", 1, 330, 47.0, 38.0, 1.0, 8.0, 0.2, 17.5, 20, 8.5, "usda"),
    ("Farina di grano saraceno", "Buckwheat flour", 1, 353, 12.6, 70.6, 3.1, 0.0, 0.7, 10.0, 11, 12.0, "crea"),
    ("Semolino di frumento", "Wheat semolina (fine)", 1, 349, 10.8, 75.2, 0.9, 0.5, 0.1, 3.5, 1, 12.5, "crea"),
    ("Pop corn (sgonfio, senza grassi)", "Plain popcorn (air-popped)", 1, 387, 12.0, 78.0, 4.5, 0.9, 0.8, 14.5, 8, 4.1, "usda"),

    # ── CAT 2: Cereali cotti (ancora) ────────────────────────────────────────
    ("Riso parboiled, cotto", "Parboiled rice, cooked", 2, 125, 2.6, 26.8, 0.3, 0.1, 0.1, 0.7, 1, 71.0, "crea"),
    ("Pasta gluten-free riso/mais, cotta", "Gluten-free rice/corn pasta, cooked", 2, 130, 1.8, 28.5, 0.8, 0.5, 0.1, 1.0, 5, 68.0, "usda"),
    ("Spätzle (gnocchetti tirolesi), cotti", "Cooked Spätzle (Tirolean egg noodles)", 2, 145, 5.5, 25.0, 2.8, 0.5, 0.8, 0.5, 180, 65.0, "crea"),
    ("Trofie, cotte", "Cooked trofie pasta", 2, 130, 4.5, 26.0, 1.0, 0.5, 0.2, 0.8, 2, 68.5, "crea"),
    ("Penne integrali, cotte", "Cooked wholemeal penne", 2, 139, 5.5, 27.5, 1.1, 0.6, 0.2, 3.5, 3, 65.5, "crea"),
    ("Lasagne fresche, cotte", "Cooked fresh lasagne sheets", 2, 135, 5.2, 25.0, 1.8, 0.5, 0.5, 0.8, 4, 67.0, "crea"),

    # ── CAT 3: Pane e prodotti da forno (ancora) ─────────────────────────────
    ("Pane di kamut, biologico", "Organic kamut bread", 3, 278, 10.5, 55.0, 1.8, 1.5, 0.3, 4.5, 450, 31.0, "crea"),
    ("Pane con noci", "Walnut bread", 3, 320, 9.5, 52.0, 9.5, 3.0, 1.4, 3.5, 420, 30.0, "crea"),
    ("Pane all'olio", "Olive oil bread", 3, 295, 8.5, 56.0, 4.5, 1.5, 0.8, 2.5, 480, 29.0, "crea"),
    ("Focaccia genovese", "Ligurian focaccia", 3, 310, 7.5, 46.5, 11.0, 1.8, 1.8, 2.8, 560, 32.0, "crea"),
    ("Schiacciata toscana", "Tuscan schiacciata flatbread", 3, 298, 7.8, 50.0, 8.5, 1.5, 1.5, 2.5, 540, 33.0, "crea"),
    ("Crespelle (crêpes, neutre)", "Neutral crêpes", 3, 178, 6.5, 24.0, 6.5, 3.5, 2.0, 0.9, 190, 61.0, "crea"),
    ("Waffle (neutro base)", "Plain waffle (base recipe)", 3, 291, 7.9, 40.5, 11.5, 9.0, 3.5, 1.0, 360, 38.0, "usda"),
    ("Muffin all'avena (senza latticini)", "Oat muffin (dairy-free)", 3, 310, 7.0, 45.0, 11.5, 16.0, 2.0, 4.5, 250, 34.0, "usda"),
    ("Fetta biscottata alla frutta", "Fruit rusk", 3, 390, 9.0, 77.0, 4.5, 20.0, 1.5, 4.0, 210, 5.5, "crea"),
    ("Pane azzimo integrale", "Wholemeal unleavened bread", 3, 375, 12.0, 75.0, 3.5, 0.5, 0.7, 8.5, 15, 5.5, "crea"),
    ("Baguette francese", "French baguette", 3, 270, 9.0, 55.5, 1.5, 2.0, 0.3, 2.5, 500, 32.0, "crea"),
    ("Naan indiano", "Indian naan bread", 3, 310, 9.0, 50.5, 7.5, 3.5, 2.5, 2.0, 490, 31.0, "usda"),

    # ── CAT 4: Legumi (ancora) ────────────────────────────────────────────────
    ("Fagioli di Lamon, cotti", "Lamon beans, cooked", 4, 127, 8.0, 22.5, 0.5, 0.5, 0.1, 7.5, 3, 68.0, "crea"),
    ("Fagiolini piattoni, cotti", "Flat green beans, cooked", 4, 28, 2.0, 5.5, 0.2, 2.0, 0.0, 3.4, 4, 91.0, "crea"),
    ("Ceci neri, cotti", "Black chickpeas, cooked", 4, 130, 9.0, 22.5, 2.5, 0.5, 0.3, 8.0, 5, 65.0, "crea"),
    ("Fagioli all'occhio, cotti", "Black-eyed peas, cooked", 4, 116, 7.7, 20.8, 0.5, 3.3, 0.1, 8.3, 4, 70.0, "usda"),
    ("Fave fresche, crude", "Fresh fava beans, raw", 4, 88, 7.9, 15.7, 0.4, 1.5, 0.1, 8.0, 3, 75.0, "crea"),
    ("Lenticchie beluga (nere), cotte", "Beluga lentils (black), cooked", 4, 116, 9.0, 20.0, 0.4, 1.5, 0.1, 7.9, 2, 69.9, "usda"),
    ("Piselli spezzati gialli, cotti", "Yellow split peas, cooked", 4, 118, 8.3, 21.1, 0.4, 2.9, 0.1, 8.3, 2, 69.5, "usda"),
    ("Soia, granuli texturizzati secchi (TVP)", "Textured soy protein (TVP), dry", 4, 345, 51.5, 33.0, 1.2, 8.0, 0.2, 17.5, 270, 7.5, "usda"),

    # ── CAT 5: Verdure (ancora) ───────────────────────────────────────────────
    ("Pomodoro secco (sun-dried)", "Sun-dried tomato", 5, 258, 14.1, 55.8, 2.9, 37.6, 0.4, 12.3, 2095, 14.6, "usda"),
    ("Pomodoro, passata (senza sale)", "Tomato passata (salt-free)", 5, 25, 1.7, 5.0, 0.2, 3.5, 0.0, 1.5, 10, 92.0, "crea"),
    ("Pomodoro, concentrato (doppio)", "Double tomato concentrate", 5, 82, 4.8, 18.0, 0.5, 12.0, 0.1, 4.5, 230, 74.0, "crea"),
    ("Insalata mista (mix lattuga/radicchio)", "Mixed salad (lettuce/radicchio)", 5, 14, 1.2, 2.5, 0.2, 1.5, 0.0, 1.5, 20, 94.5, "crea"),
    ("Misticanza (mix erbe e foglie)", "Misticanza (mixed herbs & leaves)", 5, 20, 2.0, 3.5, 0.3, 1.0, 0.0, 2.0, 35, 93.0, "crea"),
    ("Broccoletti (cime di broccolo)", "Broccoli florets", 5, 34, 2.8, 6.6, 0.4, 1.7, 0.1, 2.6, 33, 89.3, "usda"),
    ("Verza (cavolo savoia)", "Savoy cabbage", 5, 27, 2.0, 5.8, 0.1, 2.3, 0.0, 3.1, 28, 91.0, "crea"),
    ("Indivia riccia", "Curly endive", 5, 17, 1.3, 3.4, 0.2, 0.5, 0.0, 3.1, 22, 94.0, "crea"),
    ("Puntarelle (radici di catalogna)", "Puntarelle chicory shoots", 5, 22, 1.8, 3.8, 0.2, 0.5, 0.1, 3.8, 50, 93.0, "crea"),
    ("Senape, foglie fresche", "Mustard greens, fresh", 5, 26, 2.9, 4.7, 0.4, 1.4, 0.0, 3.2, 25, 90.7, "usda"),
    ("Okra (gombo), cruda", "Okra, raw", 5, 33, 1.9, 7.5, 0.2, 1.5, 0.0, 3.2, 8, 89.6, "usda"),
    ("Taro (colocasia), cotto", "Taro (colocasia), cooked", 5, 142, 0.5, 35.0, 0.1, 0.5, 0.0, 4.1, 18, 64.0, "usda"),
    ("Radice di loto, cruda", "Lotus root, raw", 5, 74, 2.6, 17.2, 0.1, 0.5, 0.0, 4.9, 45, 79.1, "usda"),
    ("Germogli di bambù, in scatola", "Bamboo shoots, canned", 5, 11, 1.5, 2.0, 0.2, 1.8, 0.0, 2.2, 5, 95.9, "usda"),
    ("Zucchine, crude a fettine", "Raw zucchini slices", 5, 17, 1.2, 3.1, 0.3, 2.5, 0.1, 1.0, 8, 94.8, "crea"),
    ("Pomodori verdi, crudi", "Green tomatoes, raw", 5, 21, 1.0, 4.6, 0.2, 3.0, 0.0, 1.1, 13, 93.7, "usda"),
    ("Avocado, polpa", "Avocado flesh", 5, 160, 2.0, 8.5, 14.7, 0.7, 2.1, 6.7, 7, 73.2, "crea"),
    ("Edamame (baccelli cotti interi)", "Edamame pods, cooked", 5, 121, 11.9, 8.9, 5.2, 2.2, 0.8, 5.2, 63, 72.8, "usda"),
    ("Cavolo cappuccio viola", "Red (purple) cabbage", 5, 31, 1.4, 7.4, 0.2, 3.8, 0.0, 2.1, 27, 90.4, "crea"),
    ("Rucola, cotta", "Cooked arugula (rocket)", 5, 20, 2.0, 3.3, 0.4, 0.5, 0.0, 1.5, 60, 92.5, "crea"),
    ("Bietole colorate (arcobaleno), cotte", "Rainbow chard, cooked", 5, 20, 1.9, 4.1, 0.1, 1.1, 0.0, 2.1, 180, 92.7, "crea"),
    ("Topinambur, cotto", "Jerusalem artichoke, cooked", 5, 76, 2.0, 17.4, 0.0, 9.6, 0.0, 1.6, 6, 78.0, "crea"),
    ("Mais dolce in scatola, sgocciolato", "Canned sweet corn, drained", 5, 86, 3.0, 18.7, 1.2, 6.3, 0.2, 2.7, 15, 76.9, "usda"),
    ("Finocchi, crudi", "Raw fennel bulb", 5, 31, 1.2, 7.3, 0.2, 3.9, 0.0, 3.1, 52, 90.2, "crea"),
    ("Peperonata (peperoni cotti in olio/pomodoro)", "Peperonata (cooked peppers in oil/tomato)", 5, 75, 1.5, 8.5, 4.0, 5.5, 0.6, 2.0, 280, 84.0, "crea"),
    ("Passata di verdure mista", "Mixed vegetable puree", 5, 40, 2.0, 8.0, 0.3, 4.0, 0.0, 2.5, 35, 88.0, "crea"),
    ("Capperi sotto sale (dissalati)", "Desalted capers", 5, 23, 2.4, 4.9, 0.9, 0.4, 0.2, 3.2, 200, 84.0, "crea"),
    ("Funghi secchi (porcini reidratati)", "Rehydrated dried porcini mushrooms", 5, 28, 3.5, 5.0, 0.5, 0.5, 0.1, 2.5, 12, 89.0, "crea"),
    ("Cachi (persimon) secchi", "Dried persimmon", 5, 274, 1.4, 71.3, 0.6, 59.0, 0.1, 14.5, 1, 25.0, "usda"),
    ("Zucca butternut, cotta", "Butternut squash, cooked", 5, 40, 0.9, 9.7, 0.1, 2.0, 0.0, 1.5, 2, 88.0, "usda"),

    # ── CAT 6: Frutta (ancora) ────────────────────────────────────────────────
    ("Pompelmo rosa, fresco", "Pink grapefruit, fresh", 6, 42, 0.7, 10.7, 0.1, 8.5, 0.0, 1.4, 0, 88.1, "usda"),
    ("Nettarina (pesca noce), fresca", "Nectarine, fresh", 6, 44, 1.1, 10.6, 0.3, 7.7, 0.0, 1.7, 0, 87.6, "crea"),
    ("Cocomero (anguria) a fette", "Watermelon slices", 6, 30, 0.6, 7.6, 0.2, 6.2, 0.0, 0.4, 1, 91.5, "crea"),
    ("Melone cantalupo, polpa", "Cantaloupe melon flesh", 6, 34, 0.8, 8.2, 0.2, 7.9, 0.0, 0.9, 16, 90.2, "crea"),
    ("Mora di gelso, fresca", "Mulberry, fresh", 6, 43, 1.4, 9.8, 0.4, 8.1, 0.0, 1.7, 10, 87.7, "usda"),
    ("Carambola (star fruit)", "Star fruit (carambola)", 6, 31, 1.0, 6.7, 0.3, 3.1, 0.0, 2.8, 2, 91.4, "usda"),
    ("Mela cotogna, cruda", "Quince, raw", 6, 57, 0.4, 15.3, 0.1, 6.3, 0.0, 1.9, 4, 83.8, "crea"),
    ("Giuggiole secche", "Dried jujube", 6, 287, 3.7, 73.3, 1.1, 66.8, 0.0, 0.0, 9, 20.0, "usda"),
    ("Kiwi verde, sbucciato", "Green kiwi, peeled", 6, 61, 1.1, 14.7, 0.5, 9.0, 0.0, 3.0, 3, 83.1, "crea"),
    ("Kiwi giallo (golden), sbucciato", "Golden kiwi, peeled", 6, 63, 1.1, 15.0, 0.5, 10.5, 0.0, 1.4, 3, 82.4, "usda"),
    ("Banana plantano, cotta", "Cooked plantain banana", 6, 122, 1.3, 31.9, 0.4, 14.8, 0.2, 2.3, 5, 65.3, "usda"),
    ("Pera abate, fresca", "Abate pear, fresh", 6, 58, 0.4, 15.5, 0.1, 9.8, 0.0, 3.1, 1, 83.7, "crea"),
    ("Fragoline di bosco, fresche", "Wild strawberries, fresh", 6, 40, 0.8, 9.2, 0.4, 4.9, 0.0, 2.0, 1, 89.9, "crea"),
    ("Ananas essiccato", "Dried pineapple", 6, 341, 2.0, 83.5, 0.5, 67.5, 0.0, 8.0, 5, 10.0, "usda"),
    ("Mango essiccato", "Dried mango", 6, 319, 2.5, 78.0, 1.0, 66.0, 0.2, 2.4, 162, 15.0, "usda"),
    ("Papaya essiccata", "Dried papaya", 6, 295, 1.0, 74.0, 0.5, 52.5, 0.2, 5.5, 190, 20.0, "usda"),

    # ── CAT 7: Frutta secca e semi (ancora) ───────────────────────────────────
    ("Noci di macadamia tostate (salate)", "Roasted salted macadamia", 7, 730, 7.9, 14.0, 76.0, 4.6, 12.1, 8.0, 310, 1.2, "usda"),
    ("Arachidi bollite", "Boiled peanuts", 7, 318, 13.5, 21.5, 22.0, 4.5, 3.0, 8.5, 330, 45.0, "usda"),
    ("Mix di frutta secca e semi", "Nut and seed mix", 7, 600, 18.0, 18.0, 53.0, 7.5, 7.0, 8.5, 120, 3.0, "usda"),
    ("Cocco, latte in polvere", "Coconut milk powder", 7, 530, 5.5, 50.0, 34.0, 35.0, 30.0, 7.0, 90, 4.0, "usda"),
    ("Noci pecan tostate", "Roasted pecans", 7, 715, 9.5, 14.5, 73.5, 4.2, 6.2, 9.6, 1, 3.0, "usda"),
    ("Semi di sesamo tostati", "Toasted sesame seeds", 7, 565, 17.0, 23.4, 48.0, 0.3, 6.7, 11.5, 8, 4.0, "crea"),
    ("Semi di lino tostati", "Toasted flaxseed", 7, 534, 18.3, 28.9, 42.2, 1.6, 3.7, 27.3, 30, 6.9, "usda"),
    ("Burro di girasole", "Sunflower seed butter", 7, 614, 20.0, 20.0, 53.0, 3.5, 5.6, 9.0, 165, 1.7, "usda"),

    # ── CAT 8: Carne (ancora) ──────────────────────────────────────────────────
    ("Pollo, arrosto con pelle", "Roast chicken with skin", 8, 239, 25.0, 0.0, 15.2, 0.0, 4.3, 0.0, 87, 58.0, "crea"),
    ("Anatra, petto crudo (senza pelle)", "Duck breast, raw (skinless)", 8, 140, 23.5, 0.0, 4.8, 0.0, 1.5, 0.0, 74, 71.5, "usda"),
    ("Anatra, coscia cotta", "Duck leg, cooked", 8, 217, 21.0, 0.0, 14.5, 0.0, 5.5, 0.0, 76, 62.0, "usda"),
    ("Oca, petto crudo", "Goose breast, raw", 8, 161, 22.8, 0.0, 7.8, 0.0, 2.7, 0.0, 70, 68.3, "usda"),
    ("Fagiano, petto crudo", "Pheasant breast, raw", 8, 133, 24.4, 0.0, 3.6, 0.0, 1.1, 0.0, 41, 72.0, "usda"),
    ("Quaglia, intera cotta", "Whole quail, cooked", 8, 234, 25.1, 0.0, 14.1, 0.0, 4.0, 0.0, 58, 58.0, "usda"),
    ("Tacchino, petto macinato crudo", "Turkey breast, ground raw", 8, 120, 22.0, 0.0, 3.0, 0.0, 0.8, 0.0, 60, 74.0, "crea"),
    ("Manzo, fianco (flank steak), crudo", "Beef flank steak, raw", 8, 159, 21.4, 0.0, 8.0, 0.0, 3.3, 0.0, 60, 69.5, "usda"),
    ("Manzo, girello (topside), crudo", "Beef topside, raw", 8, 122, 21.0, 0.0, 4.0, 0.0, 1.6, 0.0, 60, 74.0, "crea"),
    ("Vitello, fettina al limone (cotta)", "Veal escalope with lemon (cooked)", 8, 162, 25.0, 2.5, 5.5, 0.5, 2.0, 0.0, 320, 65.0, "crea"),
    ("Agnello, coscio cotto al forno", "Lamb leg, roasted", 8, 218, 24.5, 0.0, 13.5, 0.0, 6.0, 0.0, 76, 60.0, "crea"),
    ("Capretto, carne cruda", "Goat kid meat, raw", 8, 109, 20.6, 0.0, 2.6, 0.0, 0.8, 0.0, 82, 76.0, "usda"),
    ("Bisonte (bufalo americano), macinato crudo", "Bison ground, raw", 8, 146, 20.2, 0.0, 7.2, 0.0, 2.9, 0.0, 57, 72.0, "usda"),
    ("Maiale, arrosto al forno cotto", "Pork roast, oven cooked", 8, 231, 25.5, 0.0, 14.5, 0.0, 5.3, 0.0, 68, 58.0, "crea"),
    ("Maiale, salsiccia fresca cruda", "Fresh pork sausage, raw", 8, 339, 12.9, 0.8, 31.2, 0.0, 11.3, 0.0, 758, 53.0, "crea"),
    ("Manzo, stinco cotto in umido", "Beef shin, braised", 8, 195, 28.0, 0.0, 9.5, 0.0, 3.5, 0.0, 78, 61.0, "crea"),
    ("Pollo, petto marinato alla griglia", "Grilled marinated chicken breast", 8, 155, 29.5, 1.5, 3.2, 0.8, 0.9, 0.0, 250, 65.0, "crea"),
    ("Vitello, fegato cotto in padella", "Pan-cooked veal liver", 8, 175, 25.5, 4.5, 6.5, 0.0, 2.0, 0.0, 80, 63.0, "crea"),

    # ── CAT 9: Salumi (ancora) ────────────────────────────────────────────────
    ("Soppressata calabrese", "Calabrian soppressata salami", 9, 415, 24.0, 1.0, 36.5, 0.5, 13.0, 0.0, 1550, 35.0, "crea"),
    ("Porchetta (arrosto di maiale)", "Porchetta (Italian roast pork)", 9, 350, 22.5, 1.0, 29.0, 0.0, 10.5, 0.0, 900, 46.0, "crea"),
    ("Mortadella di Bologna IGP", "Mortadella di Bologna IGP", 9, 311, 14.7, 0.2, 28.1, 0.2, 10.5, 0.0, 860, 53.0, "crea"),
    ("Salame di Varzi DOP", "Varzi salami DOP", 9, 420, 24.0, 0.5, 37.0, 0.3, 13.5, 0.0, 1480, 33.0, "crea"),
    ("Prosciutto di San Daniele DOP", "San Daniele DOP ham", 9, 187, 27.5, 0.5, 8.5, 0.0, 3.0, 0.0, 2250, 59.0, "crea"),
    ("Finocchiona (salame al finocchio)", "Finocchiona (fennel salami)", 9, 415, 22.5, 1.2, 37.0, 0.5, 13.5, 0.0, 1580, 35.0, "crea"),
    ("Chorizo (salame spagnolo)", "Spanish chorizo", 9, 455, 24.1, 1.9, 38.5, 1.0, 14.0, 0.0, 1780, 35.0, "usda"),
    ("Jamón ibérico (prosciutto iberico)", "Spanish Jamón ibérico", 9, 375, 33.0, 0.5, 27.5, 0.0, 9.5, 0.0, 2070, 39.0, "usda"),
    ("Prosciutto di Norcia", "Norcia cured ham", 9, 176, 27.0, 0.0, 7.5, 0.0, 2.7, 0.0, 2000, 62.0, "crea"),
    ("Spianata romana piccante", "Spicy Roman spianata salami", 9, 465, 21.0, 1.5, 43.0, 0.5, 15.5, 0.0, 1650, 30.0, "crea"),

    # ── CAT 10: Prodotti ittici (ancora) ──────────────────────────────────────
    ("Mormora (sparo), cruda", "Striped sea bream, raw", 10, 86, 17.5, 0.0, 1.8, 0.0, 0.4, 0.0, 65, 79.5, "crea"),
    ("Luccio, crudo", "Pike, raw", 10, 88, 19.3, 0.0, 1.1, 0.0, 0.2, 0.0, 51, 78.0, "crea"),
    ("Carpa, cruda", "Carp, raw", 10, 127, 17.8, 0.0, 5.6, 0.0, 1.1, 0.0, 54, 76.0, "crea"),
    ("Anguilla di fiume, cruda", "Freshwater eel, raw", 10, 184, 18.4, 0.0, 11.7, 0.0, 2.4, 0.0, 51, 68.0, "crea"),
    ("Pesce gatto (siluro), crudo", "Catfish, raw", 10, 95, 16.4, 0.0, 2.8, 0.0, 0.7, 0.0, 50, 80.0, "usda"),
    ("Acciughe sotto sale (lavate)", "Salt-packed anchovies, rinsed", 10, 145, 22.0, 0.0, 6.5, 0.0, 1.8, 0.0, 1700, 70.0, "crea"),
    ("Bottarga di muggine", "Mullet bottarga (cured roe)", 10, 318, 40.0, 0.0, 18.0, 0.0, 4.5, 0.0, 1400, 40.0, "crea"),
    ("Tonno rosso (bluefin), crudo", "Bluefin tuna, raw", 10, 144, 23.3, 0.0, 5.7, 0.0, 1.5, 0.0, 39, 69.0, "usda"),
    ("Rana pescatrice (coda di rospo), cruda", "Monkfish tail, raw", 10, 76, 16.3, 0.0, 1.0, 0.0, 0.1, 0.0, 18, 81.7, "crea"),
    ("Grongo, crudo", "Conger eel, raw", 10, 108, 19.0, 0.0, 3.5, 0.0, 0.8, 0.0, 47, 76.0, "crea"),
    ("Salmone coho, crudo", "Coho salmon, raw", 10, 146, 21.6, 0.0, 6.4, 0.0, 1.5, 0.0, 46, 71.5, "usda"),
    ("Trota iridea, cotta", "Cooked rainbow trout", 10, 168, 22.9, 0.0, 8.5, 0.0, 2.5, 0.0, 56, 66.0, "crea"),
    ("Surimi (bastoncini di granchio)", "Surimi crab sticks", 10, 99, 12.0, 9.5, 1.5, 4.0, 0.4, 0.5, 840, 74.0, "usda"),
    ("Polpo, in umido", "Braised octopus", 10, 105, 18.5, 3.0, 2.5, 0.0, 0.6, 0.0, 350, 74.0, "crea"),
    ("Totano, crudo", "Flying squid (totano), raw", 10, 75, 16.4, 0.8, 0.7, 0.0, 0.2, 0.0, 260, 81.0, "crea"),

    # ── CAT 11: Uova (ancora) ─────────────────────────────────────────────────
    ("Uovo di struzzo, crudo", "Ostrich egg, raw", 11, 143, 13.9, 0.7, 9.4, 0.5, 3.0, 0.0, 130, 75.3, "usda"),
    ("Frittata proteica (2 uova+albume)", "Protein omelette (2 eggs+egg white)", 11, 135, 16.0, 1.0, 7.5, 0.5, 2.2, 0.0, 290, 74.0, "crea"),

    # ── CAT 12: Latticini (ancora) ────────────────────────────────────────────
    ("Parmigiano Reggiano 24 mesi", "Parmigiano Reggiano 24 months aged", 12, 402, 33.5, 0.0, 30.0, 0.0, 19.3, 0.0, 1600, 29.0, "crea"),
    ("Asiago pressato (fresco)", "Fresh pressed Asiago cheese", 12, 345, 28.5, 2.0, 25.5, 1.5, 16.5, 0.0, 570, 43.0, "crea"),
    ("Asiago d'allevo (stagionato)", "Aged Asiago d'allevo cheese", 12, 380, 32.0, 1.0, 27.5, 0.8, 18.0, 0.0, 860, 34.0, "crea"),
    ("Scamorza affumicata", "Smoked scamorza cheese", 12, 334, 24.5, 1.5, 26.0, 1.0, 17.0, 0.0, 980, 44.0, "crea"),
    ("Montasio DOP", "Montasio DOP cheese", 12, 368, 30.0, 1.5, 27.0, 0.9, 17.0, 0.0, 790, 37.0, "crea"),
    ("Stracchino (crescenza fresca)", "Fresh crescenza stracchino", 12, 198, 15.5, 2.0, 14.8, 1.5, 9.5, 0.0, 495, 65.0, "crea"),
    ("Squacquerone di Romagna DOP", "Squacquerone di Romagna DOP", 12, 160, 9.0, 1.5, 13.0, 1.2, 8.5, 0.0, 520, 72.0, "crea"),
    ("Latte d'asina (equino)", "Donkey milk", 12, 43, 1.8, 6.9, 0.5, 6.9, 0.3, 0.0, 40, 90.4, "crea"),
    ("Burro di cacao (cosmesi/food)", "Cocoa butter", 12, 884, 0.0, 0.0, 100.0, 0.0, 59.7, 0.0, 0, 0.0, "usda"),
    ("Panna da cucina (18% grassi)", "Cooking cream (18% fat)", 12, 180, 3.0, 3.5, 18.0, 3.5, 11.2, 0.0, 43, 74.0, "crea"),
    ("Panna fresca (35% grassi)", "Fresh heavy cream (35% fat)", 12, 337, 2.1, 3.5, 35.0, 3.5, 21.8, 0.0, 30, 58.0, "crea"),
    ("Gelato proteico (alto prot, basso grassi)", "High-protein low-fat ice cream", 12, 130, 12.0, 16.0, 2.5, 8.0, 1.5, 2.5, 95, 67.0, "usda"),
    ("Yogurt di capra, intero", "Whole goat yogurt", 12, 75, 4.1, 4.7, 4.5, 4.5, 2.9, 0.0, 40, 86.0, "crea"),
    ("Ayran (bevanda yogurt turca)", "Ayran (Turkish yogurt drink)", 12, 45, 3.0, 3.5, 2.0, 3.5, 1.3, 0.0, 480, 91.0, "usda"),
    ("Lassi dolce (bevanda yogurt indiana)", "Sweet lassi (Indian yogurt drink)", 12, 68, 3.0, 9.0, 2.0, 8.5, 1.2, 0.0, 42, 85.0, "usda"),

    # ── CAT 13: Condimenti (ancora) ───────────────────────────────────────────
    ("Salsa romesco (pomodoro/mandorle)", "Romesco sauce (tomato/almonds)", 13, 178, 4.0, 9.5, 14.5, 5.5, 1.8, 2.0, 480, 66.0, "usda"),
    ("Salsa verde (prezzemolo/acciughe)", "Salsa verde (parsley/anchovies)", 13, 195, 4.5, 2.5, 19.5, 0.5, 3.0, 0.5, 680, 72.0, "crea"),
    ("Salsa chimichurri", "Chimichurri sauce", 13, 210, 1.5, 3.0, 22.0, 0.5, 3.0, 0.5, 350, 72.0, "usda"),
    ("Salsa aglio, olio e peperoncino (condimento)", "Garlic, oil and chili dressing", 13, 385, 1.5, 6.0, 40.0, 0.5, 5.5, 0.5, 380, 48.0, "crea"),
    ("Soffritto di cipolla-sedano-carota (base)", "Soffritto (onion-celery-carrot base)", 13, 68, 1.8, 10.5, 2.5, 5.5, 0.4, 2.5, 35, 83.0, "crea"),
    ("Aceto di lampone", "Raspberry vinegar", 13, 35, 0.1, 6.0, 0.0, 5.5, 0.0, 0.0, 12, 92.0, "usda"),

    # ── CAT 14: Dolci (ancora) ────────────────────────────────────────────────
    ("Colomba pasquale", "Easter colomba cake", 14, 365, 7.5, 56.5, 12.5, 23.5, 4.0, 2.5, 270, 21.0, "crea"),
    ("Panettone milanese", "Milan panettone", 14, 390, 8.0, 55.5, 15.5, 23.0, 6.5, 2.0, 335, 22.0, "crea"),
    ("Pandoro veronese", "Verona pandoro", 14, 410, 8.5, 57.5, 16.5, 25.5, 7.0, 2.0, 280, 19.0, "crea"),
    ("Cantucci (biscotti di Prato)", "Cantucci (Prato almond cookies)", 14, 460, 12.5, 66.0, 17.5, 24.0, 2.5, 3.5, 210, 5.5, "crea"),
    ("Biscotti di avena e cioccolato", "Oat and chocolate chip cookies", 14, 452, 6.5, 63.0, 19.5, 29.5, 8.5, 4.0, 200, 5.0, "usda"),
    ("Brownie al cioccolato", "Chocolate brownie", 14, 420, 5.5, 56.5, 20.5, 37.0, 8.0, 2.0, 190, 15.0, "usda"),
    ("Madeleine (pasticcino francese)", "French madeleine", 14, 404, 6.5, 57.5, 17.5, 25.5, 4.5, 1.0, 240, 16.0, "crea"),
    ("Crostino dolce con miele e ricotta", "Sweet crostino with honey and ricotta", 14, 260, 8.5, 37.5, 8.5, 12.5, 3.5, 0.8, 230, 35.0, "crea"),
    ("Polenta dolce alla bergamasca", "Sweet Bergamo-style polenta cake", 14, 360, 6.0, 52.0, 15.5, 18.5, 4.5, 1.5, 185, 25.0, "crea"),
    ("Chewing gum senza zucchero (1 pezzo)", "Sugar-free chewing gum (1 piece)", 14, 7, 0.0, 2.5, 0.0, 0.0, 0.0, 0.0, 0, 0.3, "usda"),
    ("Caramelle gommose (jelly candy)", "Jelly gummy candies", 14, 330, 5.5, 76.5, 0.2, 52.0, 0.0, 0.0, 45, 14.0, "usda"),
    ("Meringa secca", "Dry meringue", 14, 381, 4.5, 91.5, 0.0, 86.5, 0.0, 0.0, 60, 2.5, "crea"),
    ("Semifreddo al caffè", "Coffee semifreddo", 14, 235, 4.0, 28.5, 12.5, 22.0, 7.0, 0.0, 65, 52.0, "crea"),
    ("Zabaione (zabaglione)", "Zabaione", 14, 196, 5.5, 18.5, 11.0, 18.5, 3.5, 0.0, 38, 62.0, "crea"),

    # ── CAT 15: Bevande e integratori (ancora) ────────────────────────────────
    ("Tè matcha in polvere (1 cucchiaino)", "Matcha green tea powder (1 tsp)", 15, 324, 30.0, 38.0, 5.0, 0.0, 0.0, 35.0, 13, 5.0, "usda"),
    ("Tè bianco, infuso", "White tea, brewed", 15, 1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 1, 99.9, "usda"),
    ("Tisana di camomilla", "Chamomile herbal tea", 15, 1, 0.1, 0.2, 0.0, 0.0, 0.0, 0.0, 1, 99.7, "crea"),
    ("Tisana di zenzero e limone", "Ginger lemon herbal tea", 15, 3, 0.1, 0.7, 0.0, 0.3, 0.0, 0.0, 1, 99.0, "usda"),
    ("Latte proteico (1.5% grassi, 5% prot)", "Protein milk (1.5% fat, 5% prot)", 15, 55, 5.0, 5.5, 1.5, 5.5, 1.0, 0.0, 55, 87.0, "usda"),
    ("Frullato proteico base (latte+whey)", "Basic protein shake (milk+whey)", 15, 95, 12.5, 8.5, 1.5, 7.5, 1.0, 0.0, 100, 76.0, "usda"),
    ("Succo di barbabietola, puro", "Pure beetroot juice", 15, 45, 1.7, 10.5, 0.2, 7.0, 0.0, 0.9, 78, 87.5, "usda"),
    ("Succo di aloe vera (puro, senza zucchero)", "Pure aloe vera juice (unsweetened)", 15, 4, 0.0, 1.0, 0.0, 0.5, 0.0, 0.0, 5, 99.0, "usda"),
    ("Birra artigianale (IPA 6.5%)", "Craft IPA beer (6.5%)", 15, 60, 0.7, 5.0, 0.0, 0.0, 0.0, 0.0, 11, 91.0, "usda"),
    ("Vino rosé secco (11%)", "Dry rosé wine (11%)", 15, 74, 0.2, 2.3, 0.0, 1.2, 0.0, 0.0, 8, 87.5, "usda"),
    ("Prosecco DOC", "Prosecco DOC sparkling wine", 15, 68, 0.1, 1.3, 0.0, 1.2, 0.0, 0.0, 7, 90.0, "crea"),
    ("Sciroppo di proteine + frutta (meal prep)", "Protein fruit syrup (meal prep)", 15, 110, 10.0, 15.0, 1.0, 12.0, 0.3, 0.5, 80, 72.0, "usda"),
    ("Electrolyte drink (zero kcal)", "Zero calorie electrolyte drink", 15, 3, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0, 350, 99.5, "usda"),
    ("Nespresso (capsula espresso ristretto)", "Espresso ristretto (Nespresso-style)", 15, 4, 0.1, 0.7, 0.0, 0.0, 0.0, 0.0, 1, 99.5, "usda"),
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
    conn.close()

    print(f"Inseriti: {inserted} | Saltati (duplicati): {skipped} | Totale DB: {total}")


if __name__ == "__main__":
    seed()
