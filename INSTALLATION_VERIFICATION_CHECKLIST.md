# ✅ Installation & Verification Checklist

**Sistema Finanziario Unificato - Guida Verifica Installazione**

---

## 📋 Pre-Requisiti

- [ ] Python 3.12+ installato
- [ ] Streamlit installato (`pip install streamlit`)
- [ ] Database SQLite presente (`data/crm.db`)
- [ ] Virtual environment attivo

---

## 🔧 Verifiche Backend

### Step 1: Import Test
```bash
python -c "from core.crm_db import CrmDBManager; print('OK')"
```
**Atteso**: `OK`  
**Status**: [ ] Pass [ ] Fail

### Step 2: Metodo Principale
```python
from core.crm_db import CrmDBManager
from datetime import date

db = CrmDBManager()
metriche = db.calculate_unified_metrics(date(2026, 1, 1), date(2026, 1, 31))
print(metriche['margine_orario'])
```
**Atteso**: Un numero (anche 0)  
**Status**: [ ] Pass [ ] Fail

### Step 3: Range Giornaliero
```python
from core.crm_db import CrmDBManager
from datetime import date

db = CrmDBManager()
daily = db.get_daily_metrics_range(date.today(), date.today())
print(len(daily))  # Deve essere 1
```
**Atteso**: `1`  
**Status**: [ ] Pass [ ] Fail

### Step 4: Range Settimanale
```python
from core.crm_db import CrmDBManager
from datetime import date, timedelta

db = CrmDBManager()
lunedi = date.today() - timedelta(days=date.today().weekday())
domenica = lunedi + timedelta(days=6)
weekly = db.get_weekly_metrics_range(lunedi, domenica)
print(len(weekly))  # Deve essere >= 1
```
**Atteso**: `>= 1`  
**Status**: [ ] Pass [ ] Fail

---

## 🖥️ Verifiche Frontend - Cassa

### Step 1: Pagina Carica
```bash
streamlit run server/app.py
# Vai a: Cassa
```
**Atteso**: Pagina carica senza errori  
**Status**: [ ] Pass [ ] Fail

### Step 2: Sezione Margine Presente
**Atteso**: Sezione "Analisi Margine (Logica Unificata)" visibile  
**Status**: [ ] Pass [ ] Fail

### Step 3: 4 KPI Visibili
**Atteso**:
- [ ] Ore Pagate
- [ ] Entrate Mese
- [ ] Costi Totali
- [ ] Margine/Ora

**Status**: [ ] Pass [ ] Fail

### Step 4: Info Box Visibile
**Atteso**: Box con spiegazione della formula  
**Status**: [ ] Pass [ ] Fail

---

## 📊 Verifiche Frontend - Margine Orario

### Step 1: Pagina Carica
```bash
# Nella stessa sessione Streamlit
# Vai a: Analisi Margine Orario
```
**Atteso**: Pagina carica senza errori  
**Status**: [ ] Pass [ ] Fail

### Step 2: Dashboard KPI (4 colonne)
**Atteso**: Sono visibili:
- [ ] Ore Pagate
- [ ] Entrate Totali
- [ ] Margine/Ora
- [ ] Margine Lordo

**Status**: [ ] Pass [ ] Fail

### Step 3: Tab1 Giornaliera
**Azione**: Seleziona "Giornaliera" dal sidebar  
**Atteso**: Grafico con ultimi 30 giorni + 3 KPI (Max/Media/Min)  
**Status**: [ ] Pass [ ] Fail

### Step 4: Tab1 Settimanale
**Azione**: Seleziona "Settimanale" dal sidebar  
**Atteso**: Grafico con ultimi 12 settimane + 3 KPI  
**Status**: [ ] Pass [ ] Fail

### Step 5: Tab1 Mensile
**Azione**: Seleziona "Mensile" dal sidebar  
**Atteso**: Info message (in sviluppo)  
**Status**: [ ] Pass [ ] Fail

---

## 🔐 Coerenza Dati (CRITICO)

### Test Coerenza
**Azione**: Apri Cassa e Margine Orario side-by-side  
**Atteso**: Stessi numeri per lo stesso periodo

| Metrica | Cassa | Margine | Match |
|---------|-------|---------|-------|
| Entrate | XXX | XXX | [ ] |
| Ore Pagate | XXX | XXX | [ ] |
| Costi Totali | XXX | XXX | [ ] |
| Margine/Ora | XXX | XXX | [ ] |

**Status**: [ ] Pass [ ] Fail

---

## 📄 Verifiche Documentazione

### File Presenti
- [ ] FORMULE_FINANZIARIE.md (exists)
- [ ] IMPLEMENTAZIONE_UNIFICAZIONE_FINANZIARIA.md (exists)
- [ ] UNIFICAZIONE_FINANZIARIA_SUMMARY.md (exists)
- [ ] COMPLETION_REPORT.md (exists)
- [ ] QUICK_REFERENCE_FINANCIAL_SYSTEM.md (exists)
- [ ] DOCUMENTAZIONE_INDEX.md (exists)

### File Leggibili
- [ ] Puoi aprire FORMULE_FINANZIARIE.md senza errori
- [ ] Contiene le 10 formule documentate
- [ ] Contiene esempio di dati reali

**Status**: [ ] Pass [ ] Fail

---

## 🚀 Deployment Checklist

### Produzione
- [ ] Tutti i test di verifica sono passati (PASS)
- [ ] Nessun errore nel log di Streamlit
- [ ] Dati sono coerenti tra le pagine
- [ ] Documentazione è accessibile

### Se Tutto OK
```bash
# Commit a git
git add .
git commit -m "feat: unified financial metrics system"
git push

# Deploy su server
# (procedure specifiche per il tuo ambiente)
```

### Se Qualcosa Fallisce
Vedi la sezione **Troubleshooting** sotto

---

## 🛠️ Troubleshooting

### Errore: "calculate_unified_metrics not found"
**Causa**: Il file core/crm_db.py non è stato aggiornato  
**Soluzione**:
1. Verifica che hai i file modificati
2. Ricarica il modulo: `importlib.reload(crm_db)`
3. Restart Streamlit

### Errore: "date_sel not defined"
**Causa**: Variabile non dichiarata in Margine Orario  
**Soluzione**: Aggiorna il file 05_Analisi_Margine_Orario.py dalle modifiche

### Errore: "KeyError margine_orario"
**Causa**: Il metodo non ritorna la chiave attesa  
**Soluzione**: 
1. Verifica che `calculate_unified_metrics()` sia completo in crm_db.py
2. Riesegui il test: `db.calculate_unified_metrics(...)`

### Dati Incoerenti tra Pagine
**Causa**: Due pagine usano metodi diversi  
**Soluzione**: Assicurati che ENTRAMBE le pagine usino `calculate_unified_metrics()`

---

## ✅ Sign-Off

Quando hai completato TUTTI i check:

```
Data: _______________
Tester: _______________
Risultato Finale: 
  [ ] PASS - Sistema operativo e pronto per produzione
  [ ] FAIL - Vedi sezione Troubleshooting
```

---

## 📞 Supporto

Se hai problemi:
1. Leggi FORMULE_FINANZIARIE.md (chiarimenti concettuali)
2. Leggi IMPLEMENTAZIONE_UNIFICAZIONE_FINANZIARIA.md (dettagli tecnici)
3. Riesegui i test python per verificare il backend
4. Restart Streamlit per ricaricare i moduli

---

**Status Finale**: Ready for Production  
**Last Updated**: 17 Gennaio 2026
