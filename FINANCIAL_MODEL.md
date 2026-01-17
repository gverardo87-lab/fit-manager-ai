# 💰 Modello Finanziario - Revisione Completa

## 🎯 PRINCIPI FONDAMENTALI

### Fonte di Verità Unica: `movimenti_cassa`
- **ENTRATA**: Solo da `movimenti_cassa` con `tipo='ENTRATA'`
- **USCITA**: Solo da `movimenti_cassa` con `tipo='USCITA'`
- **SALDO EFFETTIVO**: Somma di ENTRATE - USCITE (da data_effettiva)

### Cosa NON deve essere contato doppio:
- ❌ Non sommare contratti.totale_versato CON movimenti_cassa
- ✅ I movimenti_cassa contengono tutto: acconto, rate, spese
- ✅ contratti.totale_versato è solo per traccia interna

---

## 📊 CATEGORIE ENTRATE

```
ACCONTO_CONTRATTO        → Acconto iniziale contratto
RATA_CONTRATTO          → Rate dal piano rateale
LEZIONI_ESTEMPORANEE    → Lezioni pagate senza contratto
RIMBORSI                → Rimborsi da clienti/fornitori
ALTRO_ENTRATA           → Altre entrate (prestiti, capitale, ecc)
```

---

## 📊 CATEGORIE USCITE

```
SPESE_AFFITTO           → Affitto locale
SPESE_UTILITIES         → Luce, gas, acqua, internet
SPESE_ATTREZZATURE      → Attrezzi, manutenzione, sostituzione
SPESE_ASSICURAZIONI     → Assicurazioni aziendali
STIPENDI                → Retribuzioni staff
MARKETING               → Pubblicità, social media
SPESE_GENERALI          → Altre spese amministrative
```

---

## 🗓️ GESTIONE DATE

### Tabella: `movimenti_cassa`
```sql
data_movimento       → DATETIME (quando registri, per auditoria)
data_effettiva       → DATE (quando il soldi entrano/escono davvero)
```

**Uso:**
- **Dashboard/Cashflow**: Usa `data_effettiva` (soldi veri)
- **Audit trail**: Usa `data_movimento` (registrazione)

---

## 📅 SPESE RICORRENTI - NUOVA LOGICA

### Tabella: `spese_ricorrenti` (MODIFICATA)
```sql
id
nome                 → es. "Affitto Studio"
categoria            → SPESE_AFFITTO, SPESE_UTILITIES, ecc
importo              → importo mensile
frequenza            → MENSILE, SETTIMANALE, ANNUALE
giorno_inizio        → giorno del mese quando inizia la scadenza
giorno_scadenza      → giorno del mese quando scade
attiva               → boolean
data_prossima_scadenza → DATE (per sapere quando è la prossima)
```

**Esempio:**
- Nome: "Affitto Dicembre"
- Importo: 1000€
- Frequenza: MENSILE
- Giorno scadenza: 1 (primo del mese)
- Data prossima scadenza: 2026-01-01

---

## 💡 CASHFLOW ACCURATO

### Formula Cashflow Effettivo:
```
SALDO = Somma(movimenti_cassa con tipo='ENTRATA' e data_effettiva <= oggi)
      - Somma(movimenti_cassa con tipo='USCITA' e data_effettiva <= oggi)
```

### Formula Cashflow Previsto (30gg):
```
ENTRATE_PROGRAMMATE = Somma(rate_programmate NON pagate e scadenza <= oggi+30)
                    + Somma(spese_ricorrenti prossime scadenze)

SALDO_PREVISTO = SALDO_EFFETTIVO + ENTRATE_PROGRAMMATE - COSTI_PREVISTI
```

---

## 📈 PAGINA CASSA - NUOVA STRUTTURA

### Tab 1: Dashboard Effettivo
- Saldo effettivo (solo movimenti confermati)
- Cashflow del mese (grafico giornaliero)
- KPI: entrate, uscite, saldo netto

### Tab 2: Scadenziario (Cosa DEVE Succedere)
- Rate pendenti per contratto
- Spese ricorrenti prossime
- Avvisi su ritardi

### Tab 3: Previsione (30/60/90gg)
- Saldo previsto
- Entrate previste vs uscite previste
- Analisi rischi

### Tab 4: Dettaglio Spese Ricorrenti
- Lista spese ricorrenti attive
- Prossima scadenza di ognuna
- Modifica importi/date

---

## 🔧 MIGRAZIONI DB NECESSARIE

1. ✅ Aggiunta colonna `data_effettiva` a `movimenti_cassa`
2. ⏳ Aggiunta `data_prossima_scadenza` a `spese_ricorrenti`
3. ⏳ Aggiunta `giorno_inizio`, `giorno_scadenza` a `spese_ricorrenti`

---

## ⚠️ PROBLEMI ATTUALI RISOLTI

| Problema | Soluzione |
|----------|-----------|
| Doppi conteggi | Fonte unica: movimenti_cassa |
| Rate non scalate | Formula cashflow non include rate pagate |
| Spese fisse senza date | Nuovo campo data_prossima_scadenza |
| Confusione date | Separazione data_movimento vs data_effettiva |
| Previsioni imprecise | Rate + spese_ricorrenti con date esplicite |

