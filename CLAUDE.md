# FitManager AI Studio — Manifesto Architetturale v2

> *"Il codice, in primis, deve essere elegante e facilmente rileggibile.
> L'eleganza non e' un vezzo estetico: e' la base della manutenibilita'."*

Questo file e' la **Costituzione** del progetto.
Regole dettagliate per backend e frontend: vedi `api/CLAUDE.md` e `frontend/CLAUDE.md`.

---

## Missione

CRM di riferimento per personal trainer e professionisti fitness a P.IVA.
Gestisce salute fisica e contabilita' di persone reali. Zero approssimazione.

**Stack**: FastAPI + SQLModel | Next.js 16 + React 19 + shadcn/ui | SQLite (PostgreSQL-ready) | Ollama + ChromaDB (AI locale)
**Filosofia**: Privacy-first. Tutto in locale, zero cloud, zero dati verso terzi.
**Utente**: Non programmatore esperto, sta imparando il coding con AI.

---

## Architettura

```
frontend/          Next.js 16 + React 19 + TypeScript
  src/hooks/       React Query (server state)
  src/components/  shadcn/ui + componenti dominio
  src/types/       Interfacce TypeScript (mirror Pydantic)
       |
       | REST API (JSON over HTTP, JWT auth)
       v
api/               FastAPI + SQLModel ORM
  models/          7 modelli ORM (SQLAlchemy table=True)
  routers/         8 router con Bouncer Pattern + Deep IDOR
  schemas/         Pydantic v2 (input/output validation)
       |
       v
SQLite             data/crm.db — 17 tabelle, FK enforced
       |
core/              Moduli AI (dormant, non esposti via API — prossima fase)
  exercise_archive, workout_generator, knowledge_chain, card_parser, ...
```

### Separazione dei layer (Il Muro)

| Layer | Puo' importare | NON puo' importare |
|-------|---------------|-------------------|
| `api/` | sqlmodel, pydantic, fastapi, stdlib | `core/`, `streamlit`, `frontend/` |
| `frontend/` | react, next, @tanstack/react-query | `api/`, `core/` (solo REST calls) |
| `core/` | stdlib, pydantic, langchain, ollama | `api/`, `streamlit` |

`api/` e `core/` sono **completamente indipendenti**. Operano sullo stesso DB con ORM diversi.
Il frontend comunica col backend SOLO via HTTP.

---

## Design Pattern Universali

### 1. Bouncer Pattern (Early Returns)
Ogni funzione valida le precondizioni e esce subito. Max 2 livelli di nesting.
```python
# Backend
def update_rate(rate_id, data, trainer, session):
    rate = _bouncer_rate(session, rate_id, trainer.id)  # 404 se non suo
    if rate.stato == "SALDATA":
        raise HTTPException(400, "Rata gia' saldata")   # business rule
    # flusso principale — piatto
```

### 2. Deep Relational IDOR (Backend)
Ogni operazione verifica ownership attraverso la catena FK:
`Rate → Contract.trainer_id` | `Contract → Client.trainer_id` | `Event → trainer_id`

Se non trovato → 404. Mai 403 (non rivelare esistenza di dati altrui).

### 3. Atomic Transactions (Backend)
Operazioni multi-tabella (pay_rate, unpay_rate) usano un singolo `session.commit()`.
Se qualsiasi step fallisce → rollback automatico. Tutto o niente.

### 3b. Contract Integrity Engine (Backend)
Il contratto e' l'entita' centrale: collega pagamenti, crediti, sessioni.
- **Residual validation**: `create_rate` verifica che `sum(rate) ≤ prezzo - acconto`
- **Chiuso guard**: rate, piani, eventi bloccati su contratti chiusi
- **Auto-close**: contratto diventa `chiuso=True` quando SALDATO + crediti esauriti
- **Auto-reopen**: `unpay_rate` riapre automaticamente se non piu' SALDATO
- **Overpayment check**: `pay_rate` verifica sia rata-level che contract-level

### 4. React Query + Toast (Frontend)
Ogni hook: `useQuery` per lettura, `useMutation` per scrittura.
Ogni mutation invalida le query correlate + mostra toast (sonner).

### 5. Type Synchronization
Pydantic schema (backend) == TypeScript interface (frontend).
Se cambi uno, DEVI aggiornare l'altro. File: `api/schemas/` ↔ `frontend/src/types/api.ts`.

---

## Anti-Pattern Vietati

1. **Arrow code** — Nesting > 3 livelli. Usare Bouncer + list comprehension.
2. **Catch-all** — `except Exception: pass` e bare `except:`. Solo eccezioni specifiche.
3. **Magic strings** — Usare Enum/costanti. Mai `"PENDENTE"` inline.
4. **print() per logging** — Usare `logger` (core) o `console.error` (frontend).
5. **Dict raw** — I repository/router restituiscono modelli Pydantic tipizzati.
6. **any** — TypeScript: mai `any`. Definire interfacce in `types/api.ts`.
7. **N+1 queries** — Batch fetch con `IN (...)` o `selectinload`. Mai loop di query.
8. **Mass Assignment** — Input schema SENZA campi protetti (trainer_id, id dal JWT).

---

## Sicurezza (Non Negoziabile)

1. **Multi-tenancy**: trainer_id da JWT, iniettato server-side, mai dal body
2. **Query parametrizzate**: `WHERE id = ?` (core/) o `select().where()` (api/)
3. **3 layer auth**: Edge Middleware → AuthGuard client → JWT API validation
4. **Niente PII nei prompt LLM**: usare attributi anonimi
5. **Solo LLM locale** (Ollama): mai inviare dati a cloud senza consenso

---

## Workflow di Sviluppo

Ogni feature segue 4 step in ordine. Il codice non passa al successivo finche' il precedente e' solido.

### Step 1: Schema + Types
- Backend: Pydantic schema in `api/schemas/` + SQLModel in `api/models/`
- Frontend: TypeScript interface in `frontend/src/types/api.ts`

### Step 2: Router / Endpoint
- Endpoint in `api/routers/` con Bouncer Pattern + Deep IDOR
- Atomic transactions dove serve (pagamenti, revoche)

### Step 3: Hook + UI
- Custom hook in `frontend/src/hooks/`
- Componente React in `frontend/src/components/`
- Pagina in `frontend/src/app/(dashboard)/`

### Step 4: Build + Verifica
- `npx next build` (frontend) — zero errori TypeScript
- Test end-to-end: avvia API → avvia frontend → login → verifica flusso
- Commit con messaggio chiaro

---

## Comandi

```bash
# Backend API
uvicorn api.main:app --reload --port 8000

# Frontend React
cd frontend && npm run dev

# Build check (OBBLIGATORIO prima di ogni commit)
cd frontend && npx next build

# Migrazioni (Alembic)
alembic upgrade head          # applica migrazioni pendenti
alembic revision -m "desc"    # crea nuova migrazione
alembic current               # mostra versione corrente

# Test (pytest — 48 test, tutti i domini)
pytest tests/ -v

# Test (E2E — richiede server avviato)
python tools/admin_scripts/test_crud_idor.py
python tools/admin_scripts/test_financial_idor.py
python tools/admin_scripts/test_agenda_idor.py
python tools/admin_scripts/test_ledger_dashboard.py

# Backup API
# POST /api/backup/create     (richiede JWT)
# GET  /api/backup/export     (JSON dati trainer)

# Database
sqlite3 data/crm.db ".tables"

# AI (quando integrato)
ollama list
```

---

## Metriche Progetto

- **api/**: ~3,700 LOC Python — 8 modelli ORM, 9 router, 1 schema module
- **frontend/**: ~10,400 LOC TypeScript — 51 componenti, 7 hook modules, 6 pagine
- **core/**: ~11,100 LOC Python — moduli AI (workout, RAG, DNA) in attesa di API endpoints
- **DB**: 19 tabelle SQLite, FK enforced, multi-tenant via trainer_id
- **Test**: 48 pytest + 67 E2E
- **Sicurezza**: JWT auth, bcrypt, Deep Relational IDOR, 3-layer route protection
- **Cloud**: 0 dipendenze, 0 dati verso terzi

---

*Questo file e' la legge. Il codice che non la rispetta non viene mergiato.*
