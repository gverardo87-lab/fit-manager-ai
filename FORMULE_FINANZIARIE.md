# 📊 Sistema Finanziario Unificato - Formule Ufficiali

**Versione**: 8.1 (Corretta)  
**Data**: 17 Gennaio 2026  
**Fonte di Verità**: `core/crm_db.py` - Metodo `calculate_unified_metrics()`  
**Stato**: ✅ ALLINEATO CON STANDARD INDUSTRIA

---

## 🎯 Obiettivo

Garantire coerenza e trasparenza nelle metriche finanziarie utilizzate in:
- **04_Cassa.py** - Dashboard di contabilità generale
- **05_Analisi_Margine_Orario.py** - Analisi della redditività oraria

**NOTA CRITICA**: A partire da v8.1, le formule sono state corrette per allinearsi con gli standard del settore (Trainerize, Zen Planner, ecc.)

---

## 📐 Formule Base (Versione 8.1 - CORRETTA)

### 1. **ENTRATE TOTALI**
```
ENTRATE = SUM(importo) 
WHERE tipo='ENTRATA' 
  AND data_effettiva BETWEEN [data_inizio] AND [data_fine]
Source: movimenti_cassa
```
**Significato**: Soldi effettivamente incassati nel periodo (solo importi confermati)

### 2. **ORE FATTURATE** ⭐ CORRETTO (v8.1)
```
ORE_FATTURATE = SUM(crediti_totali)
WHERE stato_pagamento != 'PENDENTE'
  AND data_vendita BETWEEN [data_inizio] AND [data_fine]
Source: contratti (crediti acquistati dal cliente)
```
**Significato**: Ore che la PT ha VENDUTO E RICEVUTO PAGAMENTO (indipendentemente se eseguite)  
**Nota**: Questa è la misura di RESPONSABILITÀ della PT verso il cliente  
**Cambiamento v8.1**: Precedentemente era calcolato da agenda (SBAGLIATO)

### 3. **ORE ESEGUITE** ⭐ NUOVO (v8.1)
```
ORE_ESEGUITE = SUM(durata_ore)
WHERE categoria IN ('Lezione', 'Allenamento', 'Sessione')
  AND DATE(data_inizio) BETWEEN [data_inizio] AND [data_fine]
Source: agenda (sessioni fisicamente consegnate)
```
**Significato**: Ore di lezione/allenamento EFFETTIVAMENTE CONSEGNATE (tracking esecuzione)

### 4. **ORE NON PAGATE**
```
ORE_NON_PAGATE = SUM(durata_ore)
WHERE categoria IN ('Admin', 'Formazione', 'Marketing', 'Riunione')
  AND DATE(data_inizio) BETWEEN [data_inizio] AND [data_fine]
Source: agenda
```
**Significato**: Ore di attività non fatturate (amministrative, di formazione, ecc.)

### 5. **COSTI FISSI MENSILI**
```
COSTI_FISSI_MENSILI = SUM(importo)
WHERE attiva=1 
  AND frequenza='MENSILE'
Source: spese_ricorrenti
```
**Significato**: Costi ricorrenti mensili (affitto, assicurazione, software, ecc.)

### 5. **COSTI FISSI DEL PERIODO**
```
GIORNI_PERIODO = (data_fine - data_inizio) + 1

COSTI_FISSI_PERIODO = (COSTI_FISSI_MENSILI / 30) * GIORNI_PERIODO
```
**Significato**: Porzione dei costi fissi corrispondente al periodo analizzato

### 6. **COSTI VARIABILI**
```
COSTI_VARIABILI = SUM(importo)
WHERE tipo='USCITA'
  AND categoria IN ('SPESE_ATTREZZATURE', 'ALTRO')
  AND data_effettiva BETWEEN [data_inizio] AND [data_fine]
Source: movimenti_cassa
```
**Significato**: Costi dipendenti dal volume di attività

### 7. **COSTI TOTALI**
```
COSTI_TOTALI = COSTI_FISSI_PERIODO + COSTI_VARIABILI
```

### 8. **MARGINE LORDO**
```
MARGINE_LORDO = ENTRATE - COSTI_TOTALI
            = ENTRATE - COSTI_FISSI_PERIODO - COSTI_VARIABILI
```
**Significato**: Profitto totale del periodo

### 9. **FATTURATO PER ORA**
```
FATTURATO_PER_ORA = ENTRATE / ORE_FATTURATE  (se ORE_FATTURATE > 0)
                  = 0 altrimenti
```
**Significato**: Entrate medie per ora FATTURATA (non considerando costi)

### 10. **MARGINE PER ORA** ⭐ METRICA PRINCIPALE (CORRETTA v8.1)
```
MARGINE_PER_ORA = MARGINE_LORDO / ORE_FATTURATE  (se ORE_FATTURATE > 0)
                = 0 altrimenti

MARGINE_PER_ORA = (ENTRATE - COSTI_FISSI_PERIODO - COSTI_VARIABILI) / ORE_FATTURATE
```
**Significato**: Profitto medio per ora FATTURATA (responsabilità della PT) - **QUESTO È IL KPI PRINCIPALE**  
**Cambiamento v8.1**: Precedentemente divideva per ORE_PAGATE (che erano le ore eseguite da agenda - SBAGLIATO)  
**Correzione**: Ora divide per ORE_FATTURATE (ore che il cliente ha pagato - CORRETTO)

---

## 📊 Output del Metodo `calculate_unified_metrics()` (v8.1)

```python
{
    # Periodo
    'periodo_inizio': str(date),
    'periodo_fine': str(date),
    'giorni': int,
    
    # ORE (NUOVO SCHEMA v8.1)
    'ore_fatturate': float,    # Ore che il cliente ha PAGATO (da contratti)
    'ore_eseguite': float,      # Ore che la PT ha CONSEGNATO (da agenda)
    'ore_non_pagate': float,    # Ore di attività non fatturate
    'ore_totali': float,        # ore_eseguite + ore_non_pagate
    
    # ENTRATE
    'entrate_totali': float,
    'fatturato_per_ora': float,
    
    # COSTI
    'costi_fissi_mensili': float,
    'costi_fissi_periodo': float,
    'costi_variabili': float,
    'costi_totali': float,
    
    # MARGINE (BASATO SU ORE_FATTURATE)
    'margine_lordo': float,
    'margine_netto': float,  # = margine_lordo per ora
    'margine_orario': float,  # = MARGINE_PER_ORA (il KPI principale)
    'margine_per_ora_costi_variabili': float,
    
    # Metadata
    'formula': str,
    'note': str
}
```

---

## 🔄 Sincronizzazione tra Pagine

### **04_Cassa.py**
**Sezione**: "Analisi Margine (Logica Unificata)"  
**Dati Visualizzati**:
- Ore Pagate (mese corrente)
- Entrate Mese
- Costi Totali
- **Margine/Ora** (KPI principale)

**Codice**:
```python
metriche_mese = db.calculate_unified_metrics(primo_mese, ultimo_mese)
st.metric("Margine/Ora", f"€{metriche_mese['margine_orario']:.2f}")
```

### **05_Analisi_Margine_Orario.py**
**Sezioni**: Dashboard KPI (4 colonne) + 4 Tab di analisi  
**Dati Visualizzati**:
- Ore Pagate
- Entrate Totali
- Margine/Ora
- Margine Lordo

**Codice**:
```python
# Giornaliera
metriche = db.calculate_unified_metrics(data_sel, data_sel)

# Settimanale
metriche = db.calculate_unified_metrics(lunedi, domenica)

# Mensile
metriche = db.calculate_unified_metrics(primo_giorno, ultimo_giorno)
```

---

## ⚠️ Considerazioni Importanti

### Safe Division
Tutte le divisioni che potrebbero causare errori includono controlli:
```python
margine_orario = (margine_lordo / ore_pagate) if ore_pagate > 0 else 0
```

### Data Selection
- **data_effettiva**: Usata per movimenti_cassa (soldi reali)
- **DATE(data_inizio)**: Usata per agenda (date delle attività)

### Rounding
Tutti i valori finali sono arrotondati a 2 decimali:
```python
'margine_orario': round(margine_orario, 2)
```

### Periodo dei Costi Fissi
I costi fissi mensili sono proporzionali al numero di giorni nel periodo:
```
30 giorni = 100% dei costi fissi
15 giorni = 50% dei costi fissi
1 giorno = 3.33% dei costi fissi
```

---

## 🧪 Test di Validazione

### Esempio: Gennaio 2026 (31 giorni)

| Metrica | Valore | Fonte |
|---------|--------|-------|
| Entrate | €675.00 | movimenti_cassa |
| Ore Pagate | 0h | agenda (nessuna sessione) |
| Costi Fissi Mensili | €200.00 | spese_ricorrenti |
| Costi Fissi Periodo | €206.67 | (200 / 30) * 31 |
| Costi Variabili | €35.00 | movimenti_cassa |
| **Costi Totali** | €241.67 | 206.67 + 35 |
| **Margine Lordo** | €433.33 | 675 - 241.67 |
| **Margine/Ora** | €0.00 | 433.33 / 0 = N/A |

---

## 📝 Changelog

### v8.1 (17 Gennaio 2026) - CORREZIONE CRITICA
- 🔧 **BREAKING**: Rinominato `ore_pagate` → `ore_fatturate` e aggiunto `ore_eseguite`
- 🔧 **FIX**: Ore Fatturate ora calcolate da `contratti` (crediti_totali), non da `agenda`
- 🔧 **FIX**: Margine/Ora ora basato su ORE_FATTURATE (ore pagate), non ore eseguite
- 📊 **ADD**: Tracking separato di ore_eseguite (per monitorare compliance esecuzione)
- 📈 **IMPROVEMENT**: Allineamento con standard industria (Trainerize, Zen Planner, etc.)
- 📖 **UPDATE**: Documentazione FORMULE_FINANZIARIE.md

### v1.0 (17 Gennaio 2026 - Early)
- ✅ Implementazione metodo `calculate_unified_metrics()`
- ✅ Sincronizzazione Cassa + Margine Orario
- ✅ Documentazione formule ufficiali
- ⚠️ NOTA: Formule v1.0 erano SCORRETTE per ore_pagate

---

## ⚠️ BREAKING CHANGES (v8.1)

| Aspetto | v1.0 (SBAGLIATO) | v8.1 (CORRETTO) |
|---------|-----------------|-----------------|
| **Chiave**: Ore Pagate | `ore_pagate` | `ore_fatturate` + `ore_eseguite` |
| **Calcolo**: Ore Pagate | `SUM(durata) FROM agenda` | `SUM(crediti_totali) FROM contratti WHERE stato_pagamento != PENDENTE` |
| **Margine/Ora**: Formula | `Entrate / ore_pagate` | `Entrate / ore_fatturate` |
| **Significato**: Ore Pagate | Ore ESEGUITE | Ore FATTURATE AL CLIENTE |
| **Impatto**: KPI | ❌ SBAGLIATO | ✅ CORRETTO |

---

## 🔄 Migrazione da v1.0 a v8.1

Se stai usando i dati della v1.0, **IMPORTANTE**:

```python
# PRIMA (v1.0 - SBAGLIATO)
metriche = db.calculate_unified_metrics(...)
ore_pagate = metriche['ore_pagate']  # ← SBAGLIATO (era da agenda)
margine_orario = metriche['margine_orario']  # ← SBAGLIATO (basato su ore_pagate errate)

# DOPO (v8.1 - CORRETTO)
metriche = db.calculate_unified_metrics(...)
ore_fatturate = metriche['ore_fatturate']  # ← CORRETTO (da contratti)
ore_eseguite = metriche['ore_eseguite']    # ← NUOVO (da agenda, per tracking)
margine_orario = metriche['margine_orario']  # ← CORRETTO (basato su ore_fatturate)
```

---

## 📞 Contatti / Domande

Tutti gli aggiornamenti alle formule devono essere documentati in questo file per mantenere la tracciabilità e la trasparenza.

**Ultima modifica**: 17 Gennaio 2026
