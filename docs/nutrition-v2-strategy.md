# Nutrizione v2 — Strategia catalogo e delta professionale

## Stato attuale catalogo (2026-03-13)

### nutrition.db — 226 alimenti attivi

| Tipo | Count |
|------|-------|
| ingrediente | 168 |
| pietanza | 49 |
| bevanda | 9 |
| **TOTALE** | **226** |

### Per categoria

| ID | Categoria | Count |
|----|-----------|-------|
| 1 | Cereali e derivati | 7 |
| 2 | Pasta, riso e cereali cotti | 11 |
| 3 | Pane e prodotti da forno | 9 |
| 4 | Legumi | 12 |
| 5 | Verdure e ortaggi | 28 |
| 6 | Frutta fresca | 17 |
| 7 | Frutta secca e semi | 10 |
| 8 | Carne e pollame | 15 |
| 9 | Salumi e affettati | 7 |
| 10 | Prodotti ittici | 17 |
| 11 | Uova | 4 |
| 12 | Latte, yogurt e formaggi | 19 |
| 13 | Oli e condimenti | 7 |
| 14 | Dolci e zuccheri | 6 |
| 15 | Bevande e integratori | 8 |
| 16 | Primi piatti | 10 |
| 17 | Secondi piatti | 14 |
| 18 | Piatti unici e bowl | 7 |
| 19 | Zuppe e minestre | 5 |
| 20 | Contorni composti | 7 |
| 21 | Colazioni composte | 6 |

### Ricette e porzioni

- Pietanze con ricetta: 49 (media 4.3 ingredienti)
- Componenti ricette totali: 211
- Porzioni standard: 63
- Template piani: 8

### Copertura micronutrienti (su 226 alimenti)

| Nutriente | Copertura |
|-----------|-----------|
| Calcio | 222/226 (98%) |
| Ferro | 217/226 (96%) |
| Selenio | 196/226 (87%) |
| Vit.C | 126/226 (56%) |
| Vit.B12 | 118/226 (52%) |
| Vit.D | 100/226 (44%) |

## Delta vs software professionali dell'Albo

### Benchmark concorrenti

| Software | Alimenti | Fonte dati | Target |
|----------|----------|------------|--------|
| MètaDieta | ~3,000+ | CREA + USDA + EFSA | Nutrizionisti clinici |
| Dietosystem / DS Medica | ~2,000+ | CREA completa + USDA | Standard de facto Italia |
| Winfood (Medimatica) | ~1,800 | CREA 2019 + tabelle regionali | SIAN ASL |
| Nutrigeo (Progeo) | ~1,500+ | CREA + IEO + ricettari regionali | Biologi nutrizionisti |
| NUVOLA (CNR) | ~900 | CREA 2019 | Ricerca, gratuito |
| **FitManager** | **226** | CREA 2019 + USDA parziale | PT / chinesiologi |

### Gap identificati

**1. Volume catalogo: 226 vs 1500-3000**
- Tabella CREA completa = ~900 voci. Noi ne abbiamo ~170 ingredienti base.
- Sufficiente per generazione automatica piani, insufficiente per ricerca manuale personalizzata.
- Gap critico: ~700 alimenti CREA mancanti.

**2. Porzioni standard: 63 vs ~500+**
- Mancano porzioni casalinghe ("1 cucchiaio raso", "1 tazza da te'").
- Mancano porzioni fotografiche LARN (atlante INRAN/CREA).
- Mancano porzioni industriali (codice EAN).

**3. Copertura micronutrienti: parziale**
- Vit.D al 44% (nei professionali: 90%+ grazie a USDA completa).
- Vit.C al 56%, B12 al 52%: carenza dati sulle pietanze calcolate.
- Mancano fattori di ritenzione cottura (USDA Retention Factors).

**4. Feature mancanti vs professionali**
- Ricettario regionale italiano (500+ ricette IEO / Artusi / regionali)
- Atlante fotografico delle porzioni (INRAN/CREA)
- Fattori di conversione crudo → cotto (coefficienti INRAN)
- Indice glicemico / carico glicemico per alimento
- Allergeni (14 allergeni Reg. UE 1169/2011)
- Etichette industriali (integrazione barcode/EAN)
- Composizione aminoacidica (PDCAAS/DIAAS)
- Acidi grassi dettaglio (omega-3 EPA/DHA, omega-6, trans)

**5. Vantaggi competitivi FitManager**
- Generazione automatica piano LARN-compliant (7gg x 5 pasti) — i professionali sono manuali
- Scoring composito 3 assi (macro 25% + micro 35% + frequenze CREA 40%)
- Rotazione proteica settimanale automatica allineata a CREA 2018
- Integrazione CRM (piano nel dossier cliente) — i software nutrizionali sono standalone
- Nutrienti con fonte limitata (Vit.D) con penalita' attenuata (innovativo)

## Risultati generatore v2

| Profilo | Score | Kcal target | Kcal ottenute | Warning |
|---------|-------|-------------|---------------|---------|
| Donna 25, 55kg | 91/100 | 1600 | 1600 | 4 |
| Donna 30, 60kg | 93/100 | 1800 | 1761 | 4 |
| Donna 45, 70kg | 93/100 | 2000 | 1873 | 6 |
| Uomo 28, 75kg | 94/100 | 2600 | 2114 | 4 |
| Uomo 35, 80kg | 95/100 | 2400 | 2039 | 4 |

Warning strutturali (dieta mediterranea):
- Grassi 36-38%: fisiologico con olio EVO (range LARN 20-35% conservativo)
- Calcio ~665-714mg vs 1000mg: latticini limitati nel piano
- Sodio basso: clinicamente positivo (sotto 2000mg OMS)

## Roadmap espansione catalogo

### P0 — Raggiungere parità NUVOLA (~900 alimenti)
- Import tabella CREA 2019 completa (CSV ufficiale)
- 226 → ~900 alimenti
- Prerequisito: CSV CREA o scraping tabelle CREA online

### P1 — Raggiungere livello Nutrigeo (~1200 alimenti)
- Merge USDA FoodData Central (top 500 alimenti italiani)
- Porzioni LARN complete + casalinghe (63 → ~400)
- ~900 → ~1200 alimenti

### P2 — Qualità scientifica
- Fattori ritenzione cottura USDA → score micro +10-15%
- 200+ ricette italiane regionali → catalogo pietanze competitivo
- Completamento micronutrienti Vit.D/C/B12 su pietanze

### P3 — Feature premium differenzianti
- Allergeni EU (14 categorie Reg. 1169/2011)
- Indice glicemico per alimento
- Acidi grassi dettaglio (omega-3/6, trans)

## Note architetturali

- nutrition.db e' read-only, condiviso tra tutti i trainer (no trainer_id)
- crm.db contiene i piani alimentari trainer-owned (Bouncer Pattern)
- Cross-DB: `MealComponent.alimento_id` → `Food.id` (application-level integrity)
- Alembic separato: `alembic_nutrition.ini` + `alembic_nutrition/`
- Seed pipeline: `seed_nutrition_gaps.py` → `seed_pietanze.py` (idempotenti)
