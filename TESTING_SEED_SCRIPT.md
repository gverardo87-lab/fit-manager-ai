# 🧪 Testing Guide - Database Seed Script

**Data**: 17 Gennaio 2026  
**Script**: `scripts/seed_data.py`  
**Status**: ✅ Ready for Testing  

---

## 📋 Pre-requisiti

### 1. Installare Dipendenze

```bash
# Se usi pip
pip install -r requirements.txt

# O se usi pyproject.toml
pip install -e .
```

### 2. Verificare Struttura Directory

```bash
fit-manager-ai/
├── core/
│   └── crm_db.py
├── data/              # Verrà creato automaticamente
│   └── crm.db         # Verrà creato automaticamente
└── scripts/
    └── seed_data.py
```

---

## 🚀 Uso del Seed Script

### Comando Base (Aggiungi Dati)

```bash
python scripts/seed_data.py
```

**Output Atteso**:
```
============================================================
🌱 FitManager AI - Database Seed Script
============================================================

📦 Starting data seeding...

👥 Seeding clienti...
   ✓ Created client: Mario Rossi (ID: 1)
   ✓ Created client: Laura Bianchi (ID: 2)
   ✓ Created client: Giuseppe Verdi (ID: 3)
   ✓ Created client: Sofia Romano (ID: 4)
   ✓ Created client: Luca Ferrari (ID: 5)
✅ Created 5 clients

============================================================
✅ SEEDING COMPLETE!
============================================================

📊 Summary:
   • 5 clients

🚀 Ready to test! Run: streamlit run server/app.py
```

### Reset Database (Cancella e Ricrea)

```bash
python scripts/seed_data.py --reset
```

**Output Atteso**:
```
🗑️  Clearing database...
   ✓ Cleared progress_records
   ✓ Cleared workout_plans
   ✓ Cleared client_assessment_followup
   ✓ Cleared client_assessment_initial
   ✓ Cleared misurazioni
   ✓ Cleared agenda
   ✓ Cleared rate_programmate
   ✓ Cleared movimenti_cassa
   ✓ Cleared spese_ricorrenti
   ✓ Cleared contratti
   ✓ Cleared clienti
✅ Database cleared successfully

📦 Starting data seeding...
[... continua con seeding ...]
```

### Solo Clear (Senza Seeding)

```bash
python scripts/seed_data.py --clear
```

---

## 📊 Dati Seed Inclusi (Versione 1.0)

### 5 Clienti

| ID | Nome | Email | Nascita | Sesso | Note |
|----|------|-------|---------|-------|------|
| 1 | Mario Rossi | mario.rossi@example.com | 1985-03-15 | Uomo | Sedentario, vuole tornare in forma |
| 2 | Laura Bianchi | laura.bianchi@example.com | 1990-07-22 | Donna | Ex atleta, mal di schiena cronico |
| 3 | Giuseppe Verdi | giuseppe.verdi@example.com | 1978-11-10 | Uomo | Ipertensione controllata |
| 4 | Sofia Romano | sofia.romano@example.com | 1995-05-05 | Donna | Obiettivo gara bodybuilding |
| 5 | Luca Ferrari | luca.ferrari@example.com | 2000-12-20 | Uomo | Principiante assoluto |

**Anamnesi**: Tutti i clienti hanno anamnesi JSON con patologie, farmaci e note dettagliate.

---

## ✅ Verifica Dati Inseriti

### Opzione 1: Via Streamlit UI

```bash
streamlit run server/app.py
```

1. Naviga a **02_Clienti.py**
2. Verifica che i 5 clienti siano visibili nella lista
3. Clicca su un cliente per vedere dettagli anamnesi

### Opzione 2: Via SQLite CLI

```bash
sqlite3 data/crm.db

# Visualizza clienti
SELECT id, nome, cognome, email FROM clienti;

# Output atteso:
# 1|Mario|Rossi|mario.rossi@example.com
# 2|Laura|Bianchi|laura.bianchi@example.com
# 3|Giuseppe|Verdi|giuseppe.verdi@example.com
# 4|Sofia|Romano|sofia.romano@example.com
# 5|Luca|Ferrari|luca.ferrari@example.com

# Visualizza anamnesi JSON
SELECT nome, cognome, anamnesi_json FROM clienti WHERE id=1;

# Exit
.quit
```

### Opzione 3: Via Python Script

```python
from core.crm_db import CrmDBManager

db = CrmDBManager()

with db._connect() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM clienti")
    print(f"Total clients: {cursor.fetchone()['count']}")
    
    cursor.execute("SELECT nome, cognome, email FROM clienti")
    for row in cursor.fetchall():
        print(f"  • {row['nome']} {row['cognome']} ({row['email']})")
```

**Output Atteso**:
```
Total clients: 5
  • Mario Rossi (mario.rossi@example.com)
  • Laura Bianchi (laura.bianchi@example.com)
  • Giuseppe Verdi (giuseppe.verdi@example.com)
  • Sofia Romano (sofia.romano@example.com)
  • Luca Ferrari (luca.ferrari@example.com)
```

---

## 🔄 Estensioni Future (TODO)

### Versione 2.0 del Seed Script

Il seed script attuale (v1.0) include solo **clienti**. Le prossime versioni includeranno:

#### Aggiungere Contratti
```python
def seed_contratti(db, client_ids):
    # 5 contratti esempio
    # - Mario: 10 PT (€500, saldato)
    # - Laura: 20 PT Premium (€900, parziale)
    # - Giuseppe: Mensile Open Gym (€60, saldato)
    # - Sofia: 30 PT Competition Prep (€1200, parziale)
    # - Luca: 5 PT Trial (€200, pendente)
```

#### Aggiungere Misurazioni
```python
def seed_misurazioni(db, client_ids):
    # 6 misurazioni totali
    # - Mario: 2 misurazioni (inizio + progresso)
    # - Laura: 1 misurazione
    # - Giuseppe: 1 misurazione
    # - Sofia: 2 misurazioni (prep contest tracking)
```

#### Aggiungere Workout Plans
```python
def seed_workout_plans(db, client_ids):
    # 2 workout plans
    # - Mario: Full Body Progressivo (12 settimane)
    # - Sofia: PPL Competition Prep (16 settimane)
```

#### Aggiungere Assessments
```python
def seed_assessments(db, client_ids):
    # 2 assessment iniziali
    # - Mario: Assessment completo (43 campi)
    # - Laura: Assessment con focus mobilità
```

#### Aggiungere Spese Ricorrenti
```python
def seed_spese_ricorrenti(db):
    # 3 spese ricorrenti
    # - Affitto Palestra: €1500/mese
    # - Utenze: €200/mese
    # - Assicurazione: €600/anno
```

---

## 🐛 Troubleshooting

### Errore: `ModuleNotFoundError: No module named 'pandas'`

**Soluzione**:
```bash
pip install pandas
# O reinstalla tutte le dipendenze:
pip install -e .
```

### Errore: `FileNotFoundError: [Errno 2] No such file or directory: 'data/crm.db'`

**Soluzione**: La directory `data/` viene creata automaticamente. Se l'errore persiste:
```bash
mkdir -p data
python scripts/seed_data.py --reset
```

### Errore: `sqlite3.OperationalError: table clienti already exists`

**Soluzione**: Questo NON è un errore critico. Lo schema viene creato solo se non esiste.

### Errore: `sqlite3.IntegrityError: UNIQUE constraint failed: clienti.email`

**Causa**: Stai eseguendo il seed script più volte senza `--reset`

**Soluzione**:
```bash
# Reset database e ricrea dati
python scripts/seed_data.py --reset
```

### Il database è vuoto dopo il seed

**Debug**:
```bash
# Verifica che il file esista
ls -lh data/crm.db

# Verifica tabelle
sqlite3 data/crm.db ".tables"

# Verifica record
sqlite3 data/crm.db "SELECT COUNT(*) FROM clienti;"
```

Se vedi `0`, il seed script potrebbe non aver committato le transazioni. Verifica errori nell'output del comando.

---

## 📊 Metriche di Successo

### ✅ Il seed script funziona correttamente se:

1. **Nessun errore** durante l'esecuzione
2. **5 clienti** presenti nel database
3. **Streamlit UI** mostra i clienti nella pagina 02_Clienti
4. **Anamnesi JSON** correttamente formattata e parsabile
5. **Puoi eseguire `--reset`** senza errori

---

## 🔗 Risorse Correlate

- **Schema Database**: `ANALISI_DATI_DATABASE.md` (sezioni 1-12)
- **Codice Seed**: `scripts/seed_data.py`
- **Database Manager**: `core/crm_db.py`
- **Validazione Dati**: `core/models.py`

---

**Documento**: TESTING_SEED_SCRIPT.md  
**Autore**: Copilot Analysis Agent  
**Data**: 17 Gennaio 2026  
**Versione**: 1.0  
**Status**: ✅ Ready for Use  
