# FitManager AI Studio — Manifesto Architetturale

> *"Il codice, in primis, deve essere elegante e facilmente rileggibile.
> L'eleganza non e' un vezzo estetico: e' la base della manutenibilita'."*

Questo file e' la **Costituzione** del progetto. Ogni riga di codice, ogni commit,
ogni decisione tecnica deve rispettarla. Se una regola viene violata, il codice
non e' pronto per il merge — senza eccezioni.

---

## Identita' del Progetto

CRM gestionale per personal trainer e liberi professionisti del fitness.
Il software gestisce la salute fisica e i soldi delle persone reali.
Non tolleriamo approssimazione.

**Stack**: Python 3.9+ / Streamlit 1.54+ / SQLite / Ollama (LLM locale) / LangChain + ChromaDB (RAG)
**Filosofia**: Privacy-first. Tutto gira in locale, zero cloud, zero dati verso terzi.
**Utente**: Non programmatore esperto, sta imparando il coding con l'aiuto dell'AI.

Cosa significa per noi:
- Spiega brevemente il "perche'" delle scelte tecniche quando rilevante
- Non dare per scontata la conoscenza di pattern avanzati
- Proponi soluzioni ambiziose ma implementale in modo completo, mai lasciare "esercizi al lettore"
- Se qualcosa puo' rompersi, previenilo nel codice invece di documentarlo e basta
- Ogni feature deve funzionare end-to-end: modello, repository, UI

---

## La Regola d'Oro: Eleganza e Leggibilita'

Un Senior Engineer deve poter leggere qualsiasi funzione e capire il flusso
in meno di 30 secondi. Questo si ottiene con:

1. **Funzioni corte e focalizzate** — max 25 righe nei repository, max 40 nelle pages
2. **Un livello di astrazione per funzione** — non mescolare logica di business con formattazione UI
3. **Nomi che raccontano l'intenzione** — `calculate_available_credits()`, non `calc()` o `do_stuff()`
4. **Nessun commento che spiega il "cosa"** — il codice deve parlare da solo. I commenti spiegano solo il "perche'"

---

## Architettura

```
server/app.py              Router centrale (st.navigation con sezioni)
       |
server/app_dashboard.py    Dashboard KPI, sessioni, azioni rapide
server/pages/*.py          UI Streamlit — SOLO presentazione
       |
core/ui_components.py      Componenti UI riusabili (badge, card, conferme)
       |
core/constants.py          Enumerazioni e costanti (stati, categorie)
       |
core/repositories/         CRUD, validazione, accesso DB
       |
core/models.py             Pydantic v2 — validazione input
       |
SQLite                     data/crm.db — 17 tabelle attive
```

### Repository

| Repository | Dominio | Tabelle |
|------------|---------|---------|
| ClientRepository | Clienti + misurazioni | clienti, misurazioni |
| ContractRepository | Contratti + rate pagamento | contratti, rate_programmate |
| AgendaRepository | Sessioni/eventi + crediti | agenda |
| FinancialRepository | Cassa + spese ricorrenti | movimenti_cassa, spese_ricorrenti |
| AssessmentRepository | Assessment iniziale + followup | client_assessment_initial, client_assessment_followup |
| WorkoutRepository | Programmi + progressi | workout_plans, progress_records |
| CardImportRepository | Schede importate | imported_workout_cards |
| TrainerDNARepository | Pattern metodologici | trainer_dna_patterns |
| FinancialAnalytics | Metriche avanzate (LTV, CAC, Churn, MRR) | Legge da contratti, movimenti |

Tutti ereditano da `BaseRepository`. Tutti i metodi pubblici decorati con `@safe_operation`.

### Trainer DNA System

```
Schede Excel/Word --> CardParser --> CardImportRepo (DB)
                                          |
                                    PatternExtractor (LLM) --> TrainerDNARepo (DB)
                                                                     |
                                                               MethodologyChain (ChromaDB)
                                                                     |
Assessment + DNA + WorkoutGenerator --> WorkoutAIPipeline --> Programma AI-Enhanced
```

---

## Design Pattern Obbligatori

### 1. Bouncer Pattern (Early Returns)

Ogni funzione inizia verificando le pre-condizioni e uscendo subito se non sono soddisfatte.
Il flusso principale non e' mai annidato piu' di 2 livelli.

```python
# CORRETTO — Bouncer Pattern
def confirm_event(self, event_id: int) -> bool:
    event = self.get_event_by_id(event_id)
    if not event:
        raise ClienteNotFound(f"Evento {event_id} non trovato")
    if event.stato != EventStatus.PROGRAMMATO:
        raise ConflictError(f"Evento in stato {event.stato}, non confermabile")

    # Flusso principale: piatto, leggibile
    with self._connect() as conn:
        conn.execute("UPDATE agenda SET stato = ? WHERE id = ?",
                     (EventStatus.COMPLETATO.value, event_id))
    return True

# VIETATO — Arrow Code
def confirm_event(self, event_id: int) -> bool:
    event = self.get_event_by_id(event_id)
    if event:
        if event.stato == "Programmato":
            try:
                with self._connect() as conn:
                    conn.execute(...)
                    return True
            except Exception:
                return False
        else:
            return False
    else:
        return False
```

### 2. Repository Pattern (Consolidato)

- Ogni accesso al DB passa da un repository
- Ogni metodo pubblico ha `@safe_operation(name, severity, fallback_return)`
- I repository restituiscono **modelli Pydantic**, mai dict raw
- Context manager obbligatorio: `with self._connect() as conn:`
- Query sempre parametrizzate: `cursor.execute("... WHERE id = ?", (id,))`
- Foreign keys sempre attive (PRAGMA foreign_keys = ON in BaseRepository)

### 3. Validazione Pydantic-First

```
Input utente --> Modello Pydantic (Create) --> Repository --> DB
                                                   |
DB --> Repository --> Modello Pydantic (Entity) --> UI
```

- Pattern modelli: `EntityCreate` (input) + `Entity` (completo con id)
- Cross-field validation con `@field_validator` e `@model_validator`
- **Mai** scrivere nel DB senza passare da un modello Pydantic

### 4. Separazione UI / Core (Il Muro di Berlino)

Questa regola e' **inviolabile**:

| Zona | Puo' importare | NON puo' importare |
|------|---------------|-------------------|
| `core/` | stdlib, pydantic, sqlite3, langchain, ollama | `streamlit` |
| `core/ui_components.py` | streamlit (unica eccezione nel core) | sqlite3 |
| `server/pages/` | core.repositories, core.models, core.ui_components | sqlite3 |
| `server/pages/` | streamlit | — |

`core/ui_components.py` e' il **ponte** tra core e UI: contiene componenti Streamlit
riusabili (badge, card, conferme) ma **zero logica di business**.

### 5. Conferme su Azioni Distruttive

Ogni delete/cancel nell'UI DEVE avere conferma esplicita:
- **CRITICHE** (delete contratto CASCADE): checkbox + bottone disabilitato → `render_confirm_delete()`
- **MEDIE** (cancel evento, delete rata): warning + 2 bottoni → `render_confirm_action()`
- Componenti in `core/ui_components.py`, gia' adottati su tutte le 7 azioni

### 6. Error Handling Centralizzato

Gerarchia eccezioni: `FitManagerException` → `ValidationError`, `ClienteNotFound`,
`ContratoInvalido`, `DatabaseError`, `ConflictError`, `PermissionDenied`.

- **Nei repository**: SOLO `@safe_operation`. Mai try/except manuale.
- **Nelle pages**: `try/except` SOLO per `ValidationError` sui form di input.
  Per tutto il resto, il fallback di `@safe_operation` gestisce l'errore.
- **Severity**: LOW, MEDIUM, HIGH, CRITICAL — ogni metodo ha la sua.
- Le pages DEVONO gestire il caso `None` (fallback di `@safe_operation`):

```python
# CORRETTO
clienti = client_repo.get_all_active()
if not clienti:
    st.info("Nessun cliente trovato.")
    return

# VIETATO
clienti = client_repo.get_all_active()
for c in clienti:  # Crash se None!
    ...
```

---

## Anti-Pattern Severamente Vietati

### 1. DIVIETO: try/except pigro

```python
# VIETATO — Catch-all che nasconde bug
try:
    risultato = repo.operazione_complessa()
except Exception:
    pass  # Silenzio criminale

# VIETATO — Bare except
try:
    data = parse_date(value)
except:
    data = None

# CORRETTO — Eccezione specifica o nessun try/except
data = parse_date(value) if value else None
# Oppure, se serve gestire l'errore:
try:
    data = parse_date(value)
except ValueError:
    logger.warning(f"Data non parsabile: {value}")
    data = None
```

Le uniche eccezioni ammesse nelle pages sono:
- `except ValidationError` — per form input Pydantic
- `except ValueError` — per conversioni tipo esplicite
- `except (ConnectionError, TimeoutError)` — per chiamate LLM/RAG

### 2. DIVIETO: Magic Strings

```python
# VIETATO
if evento.stato == "Programmato":
    ...
movimento = {"tipo": "ENTRATA", "categoria": "Sessione"}

# CORRETTO — Usare costanti da core/constants.py
if evento.stato == EventStatus.PROGRAMMATO:
    ...
movimento = {"tipo": MovementType.ENTRATA, "categoria": MovementCategory.SESSIONE}
```

Tutte le stringhe ripetute in piu' file DEVONO essere enumerazioni o costanti in `core/constants.py`.

### 3. DIVIETO: Streamlit nel Core

```python
# VIETATO — in qualsiasi file sotto core/ (tranne ui_components.py)
import streamlit as st
st.error("Qualcosa e' andato storto")

# CORRETTO — Il core solleva eccezioni, la UI le mostra
raise DatabaseError("Connessione DB fallita", context={"db": "crm.db"})
```

### 4. DIVIETO: Arrow Code (Nesting > 3 livelli)

```python
# VIETATO
if client:
    if client.attivo:
        for contratto in client.contratti:
            if contratto.chiuso == 0:
                for rata in contratto.rate:
                    if rata.stato == "PENDENTE":
                        ...

# CORRETTO — Bouncer + list comprehension
if not client or not client.attivo:
    return []

contratti_attivi = [c for c in client.contratti if not c.chiuso]
rate_pendenti = [
    rata
    for contratto in contratti_attivi
    for rata in contratto.rate
    if rata.stato == RateStatus.PENDENTE
]
```

### 5. DIVIETO: print() per logging

```python
# VIETATO
print(f"[WARN] KB non disponibile: {e}")

# CORRETTO
logger.warning(f"Knowledge Base non disponibile: {e}")
```

Usare SEMPRE il `logger` da `core/error_handler.py`. I print finiscono nel vuoto,
i log finiscono in `logs/fitmanager.log` dove possiamo debuggare.

### 6. DIVIETO: Dict raw dai repository

```python
# VIETATO — Restituire dict senza tipo
def get_cash_balance(self) -> dict:
    return {"entrate": 1000, "uscite": 500}

# CORRETTO — Restituire modello Pydantic tipizzato
def get_cash_balance(self) -> Optional[CashBalance]:
    return CashBalance(entrate=1000, uscite=500)
```

Eccezione temporanea: `FinancialRepository` e `CardImportRepository` hanno ancora
metodi che restituiscono dict. Questo e' debito tecnico da risolvere.

---

## Workflow di Sviluppo (I 4 Comandamenti)

Ogni feature, bug fix o refactoring segue questi 4 step **in ordine**.
Il codice NON passa allo step successivo finche' il precedente non e' solido.
Alla fine di ogni step, si chiede conferma prima di proseguire.

### Step 1: Modello e Costanti
- Definire/aggiornare il modello Pydantic in `core/models.py`
- Aggiungere costanti/enum necessarie in `core/constants.py`
- Validazioni cross-field dove servono
- **Checkpoint**: "I modelli sono definiti. Procedo con la logica?"

### Step 2: Repository
- Aggiungere il metodo nel repository appropriato con `@safe_operation`
- Usare Bouncer Pattern: validazioni subito, flusso piatto
- Restituire modelli Pydantic, mai dict
- **Checkpoint**: "La logica core e' pronta. Procedo con la UI?"

### Step 3: UI
- Creare/aggiornare la pagina Streamlit in `server/pages/`
- Usare componenti da `core/ui_components.py`
- Gestire il caso `None` dal repository
- Conferme su azioni distruttive
- **Checkpoint**: "La UI e' funzionante. Testo e verifico."

### Step 4: Verifica e Pulizia
- Testare il flusso end-to-end con `streamlit run server/app.py`
- Verificare che non ci siano import vietati (st.* nel core, sqlite3 nelle pages)
- Rimuovere codice morto, commenti superflui, print di debug
- Commit con messaggio chiaro

---

## Sistema Crediti

Formula a 3 livelli (`CreditSummary` model, calcolato su contratti non chiusi):
- `crediti_totali` = SUM(crediti_totali) da contratti con chiuso=0
- `crediti_completati` = SUM(crediti_usati) da contratti con chiuso=0
- `crediti_prenotati` = COUNT(agenda) con stato=PROGRAMMATO e contratto attivo
- `crediti_disponibili` = totali - completati - prenotati

Selezione contratto FIFO: il piu' vecchio con disponibilita' viene usato per primo.
Macchina a stati eventi: Programmato → Completato | Cancellato | Rinviato.

**Debito tecnico**: logica crediti distribuita in 3 file (ClientRepository.get_by_id,
AgendaRepository.get_credit_summary, AgendaRepository.create_event).
Da unificare in un CreditService.

---

## AI / RAG

- LLM locale via Ollama (default: llama3:8b-instruct-q4_K_M)
- Embedding: nomic-embed-text
- Cross-encoder: ms-marco-MiniLM-L-6-v2 (re-ranking)
- Dual RAG:
  - `knowledge_base/vectorstore/` → teoria, anatomia, nutrizione
  - `knowledge_base/methodology_vectorstore/` → pattern metodologici trainer
- Fallback: se KB vuota, usa ExerciseArchive (174 esercizi in SQLite)
- Mai inviare PII (nomi, email, dati salute) nei prompt LLM
- Trainer DNA confidence: `min(0.95, 0.3 + evidence_count * 0.15)`

---

## Debito Tecnico (Stato Attuale)

### Critico (da risolvere prima di nuove feature)
- ~~`core/error_handler.py` importa `streamlit`~~ → RISOLTO (rimosso import + eliminato dead code)
- ~~`core/document_manager.py` importa `streamlit`~~ → RISOLTO (sostituito con logger)
- ~~`core/knowledge_chain.py` usa `@st.cache_resource` e `print()`~~ → RISOLTO (lru_cache + logger)
- ~~Magic strings ovunque~~ → RISOLTO (core/constants.py con 6 enum centralizzate)
- Pages non gestiscono sempre `None` da `@safe_operation`

### Alto (da pianificare)
- `FinancialRepository`: 15+ metodi restituiscono dict raw invece di Pydantic
- `CardImportRepository`: tutti i getter restituiscono dict raw
- Logica crediti distribuita in 3 file senza CreditService
- `04_Cassa.py` (1140 LOC) e `07_Programma_Allenamento.py` (1099 LOC) troppo grandi
- Silent failures: `except: continue` e `except Exception: pass` in dashboard e agenda

### Medio (backlog)
- Nessuna infrastruttura pytest (no conftest.py, no pytest.ini)
- `methodology_vectorstore/` non in .gitignore (dati generati)
- Paginazione mancante su `get_all_active()`

### Codice morto (eliminato)
- ~~`core/schedule_db.py` (92 LOC)~~ → ELIMINATO
- ~~`core/services/dashboard_service.py` (115 LOC)~~ → ELIMINATO
- ~~`@handle_streamlit_errors`, `@safe_streamlit_dialog`, `@safe_db_operation`~~ → ELIMINATI

---

## Sicurezza (Non Negoziabile)

1. **Solo LLM locale** — Mai inviare dati a cloud senza consenso esplicito
2. **Query parametrizzate** — `cursor.execute("... WHERE id = ?", (id,))`, sempre
3. **Niente PII nei prompt** — Usare attributi anonimi (eta', livello, obiettivo)
4. **Backup crittografato** — .fitbackup con Fernet/PBKDF2

---

## Comandi Utili

```bash
streamlit run server/app.py      # Avvia app
ollama list                      # Controlla modelli LLM
sqlite3 data/crm.db ".tables"   # Ispeziona DB
sqlite3 data/crm.db ".schema clienti"
pytest tests/ -v                 # Run tests (quando configurato)
```

---

## Metriche Progetto

- ~18.400 LOC produzione (core + server)
- 17 tabelle DB attive, FK enforced
- 9 repository + 1 analytics, 86 metodi totali (76 con @safe_operation)
- 21 modelli Pydantic con cross-field validation
- 9 pagine Streamlit + dashboard, navigazione st.navigation()
- 0 dipendenze cloud, 0 dati verso terzi

---

## Completato

- Repository Pattern (tutte le pagine migrate, CrmDBManager eliminato)
- Trainer DNA (import schede, estrazione pattern, dual RAG, pipeline AI)
- Conferme azioni distruttive (7 azioni protette, 4 file)
- Backup crittografato (.fitbackup)
- Streamlit 1.54 + theming (Inter, palette estesa)
- Navigazione st.navigation() con sezioni + KPI unificati
- Workout System riscritto: ExerciseArchive + SessionTemplate + WorkoutGenerator unico

---

*Questo file e' la legge. Il codice che non la rispetta non viene mergiato.*
