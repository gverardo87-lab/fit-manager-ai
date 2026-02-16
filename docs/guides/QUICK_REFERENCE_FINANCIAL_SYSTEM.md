# 🚀 Quick Reference: Sistema Finanziario Unificato

**TL;DR**: Una sola formula per TUTTE le metriche finanziarie.

---

## 🎯 La Formula Principale

```
MARGINE/ORA = (Entrate - Costi_Fissi - Costi_Variabili) / Ore_Pagate

Dove:
- Entrate = Soldi incassati nel periodo
- Costi_Fissi = Quote affitto, assicurazione, software, ecc
- Costi_Variabili = Spese attrezzature, altro
- Ore_Pagate = Ore di lezioni + allenamenti
```

---

## 🔧 Come Usare il Metodo

### Python
```python
from core.crm_db import CrmDBManager
from datetime import date

db = CrmDBManager()

# Calcola metriche per un mese
primo = date(2026, 1, 1)
ultimo = date(2026, 1, 31)

metriche = db.calculate_unified_metrics(primo, ultimo)

# Accedi ai dati
print(f"Entrate: EUR {metriche['entrate_totali']}")
print(f"Margine/Ora: EUR {metriche['margine_orario']}")
print(f"Costi Totali: EUR {metriche['costi_totali']}")
```

### Streamlit (Nel codice pagina)
```python
import streamlit as st
from core.crm_db import CrmDBManager
from datetime import date

db = CrmDBManager()

# Dashboard
metriche_mese = db.calculate_unified_metrics(primo_mese, ultimo_mese)

st.metric(
    "Margine/Ora",
    f"EUR {metriche_mese['margine_orario']:.2f}",
    "🎯 KPI Principale"
)
```

---

## 📊 Output Metodo

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `entrate_totali` | float | EUR incassati |
| `ore_pagate` | float | Ore fatturate |
| `ore_non_pagate` | float | Ore admin |
| `costi_fissi_periodo` | float | Quota costi fissi |
| `costi_variabili` | float | Costi operativi |
| `costi_totali` | float | Somma tutti costi |
| `margine_lordo` | float | Entrate - Costi |
| **`margine_orario`** | float | **KPI PRINCIPALE** |
| `fatturato_per_ora` | float | Entrate / Ore |

---

## 🎯 Dove Si Usa

### 04_Cassa.py
```
Dashboard → "Analisi Margine (Logica Unificata)" section
4 KPI: Ore | Entrate | Costi | Margine/Ora
```

### 05_Analisi_Margine_Orario.py
```
Dashboard → 4 KPI colonne
Tab1 → Tendenza giornaliera/settimanale/mensile
```

---

## 🛠️ Se Devi Modificare la Formula

1. **Modifica in**: `core/crm_db.py` linea 426
2. **Aggiorna**: `FORMULE_FINANZIARIE.md`
3. **Test**: Riesegui i test
4. **Deploy**: Entrambe le pagine si aggiornano automaticamente

---

## 🧪 Test Quick

```python
from core.crm_db import CrmDBManager
from datetime import date
import calendar

db = CrmDBManager()

# Test metodo principale
oggi = date.today()
primo = date(oggi.year, oggi.month, 1)
ultimo = date(oggi.year, oggi.month, 
              calendar.monthrange(oggi.year, oggi.month)[1])

metriche = db.calculate_unified_metrics(primo, ultimo)
print(f"Margine/Ora: {metriche['margine_orario']}")  # Deve funzionare

# Test range giornaliero
daily = db.get_daily_metrics_range(oggi, oggi)
print(f"Giorni: {len(daily)}")  # Deve essere 1

# Test range settimanale
lunedi = oggi - timedelta(days=oggi.weekday())
domenica = lunedi + timedelta(days=6)
weekly = db.get_weekly_metrics_range(lunedi, domenica)
print(f"Settimane: {len(weekly)}")  # Deve essere 1
```

---

## 📚 Documentazione Completa

Vedi i file:
- **FORMULE_FINANZIARIE.md** - Formule dettagliate
- **IMPLEMENTAZIONE_UNIFICAZIONE_FINANZIARIA.md** - Dettagli tecnici
- **COMPLETION_REPORT.md** - Status e test results

---

## ⚠️ Attenzione!

### Safe Division
```python
# Se ore_pagate = 0:
margine_orario = 0  # Non crasha, ritorna 0
```

### Data Selection
```python
# Usa date_effettiva per movimenti_cassa
# Usa DATE(data_inizio) per agenda
```

### Rounding
```python
# Tutti i valori sono arrotondati a 2 decimali
# Esempio: 433.333... → 433.33
```

---

## 🚀 Ready to Use!

Il sistema è pronto per la produzione.  
Usa `calculate_unified_metrics()` ovunque hai bisogno di metriche finanziarie!

---

**Ultima Modifica**: 17 Gennaio 2026  
**Status**: ✅ Production Ready
