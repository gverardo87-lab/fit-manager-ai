# 🔥 HOTFIX: Problemi Critici Ore Fatturate & Rate Mancanti

**Data**: 17 Gennaio 2026 (17:50 UTC)  
**Versione**: v8.1.1 (Hotfix)  
**Stato**: ✅ COMPLETATO

---

## 🐛 Problemi Identificati

### Problema 1: Ore Fatturate = 0 
**Sintomo**: Dashboard Cassa mostrava "Ore Fatturate: 0h" anche se clienti avevano pagato rate

**Root Cause**:
- Pagamenti registrati nel tab4 come semplici movimenti RATA_CONTRATTO
- Il sistema NON aggiornava automaticamente `contratti.totale_versato` e `stato_pagamento`
- La formula cercava `totale_versato >= prezzo_totale` (SOLO contratti COMPLETAMENTE PAGATI)
- Risultato: Contratti con pagamenti parziali restava in PENDENTE e non contava

### Problema 2: Rate Mancanti nel Tab2 Scadenziario
**Sintomo**: Tab "Scadenziario Pagamenti" non mostrava tutte le rate, mancavano alcune clienti

**Root Cause**:
- Query filtrava SOLO `WHERE stato_pagamento != 'SALDATO'`
- Risultato: Non mostrava contratti completamente pagati
- UI non visualizzava tutte le rate associate a tutti i contratti

---

## ✅ Soluzioni Implementate

### Fix 1: Metodo di Sincronizzazione Automatica
**File**: `core/crm_db.py`

Aggiunto metodo `sincronizza_stato_contratti_da_movimenti()`:
```python
def sincronizza_stato_contratti_da_movimenti(self):
    """
    Sincronizza lo stato dei contratti (totale_versato, stato_pagamento) 
    basandosi sui movimenti di RATA_CONTRATTO già registrati.
    """
    # Per ogni contratto, somma i movimenti RATA_CONTRATTO
    # Aggiorna totale_versato e stato_pagamento (PENDENTE -> PARZIALE -> SALDATO)
```

**Cosa fa**:
- Scorre tutti i contratti con movimenti RATA_CONTRATTO
- Calcola il totale versato da quei movimenti
- Aggiorna automaticamente `totale_versato` e `stato_pagamento`

### Fix 2: Correzione della Formula di Ore Fatturate
**File**: `core/crm_db.py` line 468

**PRIMA (SBAGLIATO)**:
```sql
WHERE data_vendita BETWEEN ? AND ?
AND totale_versato >= prezzo_totale  -- SOLO contratti COMPLETAMENTE PAGATI
```

**DOPO (CORRETTO)**:
```sql
WHERE data_vendita BETWEEN ? AND ?
AND totale_versato > 0  -- Qualsiasi contratto che ha ricevuto ALMENO UN PAGAMENTO
```

**Logica**:
- "Ore Fatturate" = Ore per cui il cliente ha INIZIATO a PAGARE
- Non è necessario che paghi TUTTO per contarle come "fatturate"
- Se ha pagato 175€ di 350€, comunque sono ore che PT è responsabile di consegnare

### Fix 3: Sincronizzazione Automatica all'Inizio della Pagina Cassa
**File**: `server/pages/04_Cassa.py` line 50

```python
# IMPORTANTE: Sincronizza lo stato dei contratti da movimenti RATA_CONTRATTO
db.sincronizza_stato_contratti_da_movimenti()
```

**Quando**: Ogni volta che l'utente carica la pagina Cassa

### Fix 4: Miglioramento del Tab2 Scadenziario
**File**: `server/pages/04_Cassa.py` tab2

**Cambiamenti**:
- ✅ Mostra TUTTI i contratti (non solo non-saldati)
- ✅ Aggiunto filtro per stato pagamento (SALDATO, PARZIALE, PENDENTE)
- ✅ Barra di progresso che mostra % pagamento
- ✅ Icone più chiare (✅, ⏳, ❌)
- ✅ Tabella rate meglio formattata

---

## 📊 Risultati

### Prima dei Fix
```
Contratto 1 (Giacomo): 175€ / 350€ pagato
  Stato: PENDENTE (SBAGLIATO!)
  Ore Fatturate: 0h (SBAGLIATO!)

Contratto 3 (Francesca): 500€ / 1100€ pagato
  Stato: PENDENTE (SBAGLIATO!)
  Ore Fatturate: 0h (SBAGLIATO!)

DASHBOARD: Ore Fatturate = 0h TOTALE (CRITICO!)
```

### Dopo dei Fix
```
Contratto 1 (Giacomo): 175€ / 350€ pagato
  Stato: PARZIALE (CORRETTO!)
  Ore Fatturate: 10h (CORRETTO!)

Contratto 3 (Francesca): 500€ / 1100€ pagato
  Stato: PARZIALE (CORRETTO!)
  Ore Fatturate: 20h (CORRETTO!)

DASHBOARD: Ore Fatturate = 30h TOTALE (CORRETTO!)
Margine/Ora = 14.44 EUR/h (CORRETTO!)
```

---

## 🔄 Flusso Correttivo

### Scenario: Registrazione Pagamento Cliente

**PRIMA (Rotto)**:
1. Utente accede a tab4 "Registrazione Manuale"
2. Registra movimento: ENTRATA € 175, categoria RATA_CONTRATTO, id_contratto = 1
3. Movimento creato ✓
4. Contratto ID 1: **totale_versato rimane 0** ❌
5. Contratto ID 1: **stato_pagamento rimane PENDENTE** ❌
6. ore_fatturate = 0 ❌

**DOPO (Corretto)**:
1. Utente accede a tab4 "Registrazione Manuale"
2. Registra movimento: ENTRATA € 175, categoria RATA_CONTRATTO, id_contratto = 1
3. Movimento creato ✓
4. Pagina Cassa si carica
5. Sincronizzazione automatica:
   - Contratto ID 1: **totale_versato = 175** ✓
   - Contratto ID 1: **stato_pagamento = PARZIALE** ✓
6. ore_fatturate = 10 ✓

---

## 📝 Tecnico: Dettagli Implementazione

### Sincronizzazione Smart
Il metodo `sincronizza_stato_contratti_da_movimenti()` è **idempotente**:
- Può essere chiamato infinite volte senza problemi
- Non duplica dati
- È sicuro eseguirlo ad ogni caricamento pagina

### Non è invasivo
- Modifica SOLO contratti che hanno movimenti RATA_CONTRATTO
- Non tocca contratti senza pagamenti
- Non cancella dati, solo aggiorna

### Integrazione Armoniosa
Il sistema ora ha due modi di registrare pagamenti:

**Metodo 1** (Consigliato): Usa `registra_rata()`
```python
db.registra_rata(id_contratto, importo, metodo, data_pagamento, note)
# Aggiorna automaticamente contratto e crea movimento
```

**Metodo 2** (Fallback): Registra movimento + Sincronizza
```python
# Nel tab4 registra movimento RATA_CONTRATTO manualmente
# La sincronizzazione aggiorna il contratto automaticamente
```

---

## 🧪 Testing Effettuato

✅ Sincronizzazione converte PENDENTE → PARZIALE  
✅ Sincronizzazione converte PARZIALE → SALDATO (se pagato tutto)  
✅ Ore Fatturate = 30h (10 + 20 crediti da 2 contratti con pagamenti)  
✅ Margine/Ora calcolato correttamente  
✅ Tab2 mostra tutti i contratti con filtri  
✅ Barra di progresso mostra % pagamento  

---

## 📋 Prossime Azioni (Opzionali)

1. **Migliorare UX del tab4**
   - Aggiungere selector per scegliere il contratto
   - Pre-compilare id_contratto quando registri pagamento

2. **Audit storico**
   - Controllare se altri pagamenti sono stati registrati senza sincronizzazione
   - Applicare sincronizzazione se necessario

3. **Documentazione per utenti**
   - Spiegare il flusso di registrazione pagamenti
   - Consigliare quando usare tab4 vs registra_rata()

---

## 🎓 Lezione Imparata

**Il database può contenere dati "incoerenti" se il flusso di registrazione non è coordinato.**

Soluzione: Implementare sincronizzazione periodica (al caricamento pagina) che assicuri coerenza senza richiedere cambiamenti ai flussi esistenti.

