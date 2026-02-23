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

## Esperienza Utente — Pilastro

> *"Il cliente deve aver piacere nell'usare il programma.
> Un'app che migliora la qualita' del lavoro migliora la qualita' della vita."*

L'UX non e' una feature: e' il motivo per cui il cliente sceglie noi.

1. **Actionable, non informativo** — Ogni schermata guida verso l'azione giusta. Alert con CTA contestuali ("Riscuoti", "Aggiorna stato"), mai "Vai" generico.
2. **Gerarchia visiva** — L'occhio arriva prima dove serve. Critico > Avviso > Informativo. Colori, icone e animazioni comunicano urgenza.
3. **Micro-interazioni** — Hover, transizioni, feedback visivo. L'app deve sentirsi *viva* e reattiva.
4. **Zero frustrazione** — Empty state descrittivi, error message utili, loading state chiari. Mai lasciare l'utente senza contesto.
5. **Italiano impeccabile** — Singolare/plurale, accenti, punteggiatura. L'UI e' la voce del prodotto.
6. **Mobile-first responsive** — Ogni pagina funziona su mobile (375px+), tablet (768px+) e desktop. Breakpoints Tailwind (`sm:`, `md:`, `lg:`), zero librerie extra. Dettagli in `frontend/CLAUDE.md`.

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
  models/          8 modelli ORM (SQLAlchemy table=True)
  routers/         9 router con Bouncer Pattern + Deep IDOR
  schemas/         Pydantic v2 (input/output validation)
       |
       v
SQLite             data/crm.db — 19 tabelle, FK enforced
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
- **Residual validation**: `create_rate` e `update_rate` verificano che `sum(rate attive) + nuova ≤ prezzo - totale_versato`
- **Chiuso guard**: rate, piani, eventi bloccati su contratti chiusi
- **Credit guard**: `create_event` rifiuta assegnazione a contratti con crediti esauriti (400)
- **Auto-close/reopen** (SIMMETRICO):
  - Condizione chiusura: `stato_pagamento == "SALDATO"` AND `crediti_usati >= crediti_totali`
  - **Lato rate**: `pay_rate` chiude, `unpay_rate` riapre (via stato_pagamento)
  - **Lato eventi**: `create_event`, `delete_event`, `update_event(stato)` — tutti usano `_sync_contract_chiuso()`
  - INVARIANTE: ogni operazione che modifica `crediti_usati` o `stato_pagamento` DEVE ricalcolare `chiuso`
- **Overpayment check**: `pay_rate` verifica sia rata-level che contract-level
- **Delete guard**: contratto eliminabile solo se zero rate non-saldate + zero crediti residui
- **Payment history**: `receipt_map` come `dict[int, list[CashMovement]]` — storico completo per rata

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

### 6. Chiavi Univoche per Selezione UI (Frontend)
Quando un `Set<string>` gestisce selezione multipla, la chiave DEVE essere univoca per item.
Se piu' record condividono la stessa chiave (es. `mese_anno_key = "2026-02"` per 3 spese mensili),
il Set li collassa → selezione "tutto o niente". Usare chiavi composte: `${id}::${key}`.

---

## Pitfalls Documentati

Errori reali trovati e corretti. MAI ripeterli.

| Pitfall | Causa | Fix |
|---------|-------|-----|
| `<label>` + Radix Checkbox | Browser propaga click al form control interno → double-toggle | Usare `<div onClick>` + `Checkbox onClick={stopPropagation}` |
| `datetime(y, m, day+N)` con N grande | `day=35` → `ValueError` (mese ha max 31 giorni) | Usare `base_date + timedelta(weeks=N)` |
| `Set<string>` con chiave non-univoca | `mese_anno_key` identica per piu' spese dello stesso mese | Chiave composta `${id}::${key}` |
| Auto-close senza auto-reopen eventi | Contratto chiuso restava bloccato dopo delete/cancel eventi | `_sync_contract_chiuso()` simmetrico su create/delete/update |
| Seed atomico crash a meta' | Transazione unica → rollback → DB vuoto → login impossibile | Validare i dati PRIMA del commit (es. date overflow) |
| Invalidation asimmetrica pay/unpay | `usePayRate` mancava `["movements"]`, `["movement-stats"]` | Operazioni inverse DEVONO avere invalidazione identica |
| Popup inside `.rbc-event` | `overflow:hidden` clippava popup absolute-positioned | `createPortal(popup, document.body)` + `position:fixed` |
| Calendar unmount su navigazione | `onRangeChange` → new query key → `isLoading=true` → unmount → reset | `keepPreviousData` + smart range buffering |
| KPI mese sfasato | react-big-calendar grid start in mese precedente (es. 23 feb per marzo) | `rangeLabel` usa midpoint del range per vista mese |
| KPI esclude ultimo giorno | `visibleRange.end` = mezzanotte 00:00 → eventi quel giorno esclusi | `endOfDay()` su `visibleRange.end` in `handleRangeChange` |
| D&D sposta evento -1h | `toISOString()` converte Date locale in UTC → perde offset fuso orario | `toISOLocal()` centralizzata in `lib/format.ts` — formatta in ora locale senza `Z` |
| 401 interceptor loop su login | Interceptor cattura 401 del login (credenziali errate) → redirect silenzioso → perde errore | Skip redirect se `pathname.startsWith("/login")` |

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

## Architettura Dual DB (Produzione + Sviluppo)

Due istanze completamente isolate: DB diversi, porte diverse, dati diversi.
Le modifiche al codice con `--reload` si propagano a entrambe.

```
PRODUZIONE (Chiara — sempre acceso):
  uvicorn api.main:app --host 0.0.0.0 --port 8000       → data/crm.db
  cd frontend && npm run dev -- -H 0.0.0.0 -p 3000      → .env.local punta a :8000
  Chiara accede da: http://192.168.1.23:3000

SVILUPPO (gvera — accende quando serve):
  $env:DATABASE_URL="sqlite:///data/crm_dev.db"; uvicorn api.main:app --reload --port 8001
  $env:NEXT_DIST_DIR=".next-dev"; $env:NEXT_PUBLIC_API_URL="http://localhost:8001"; npm run dev -- -p 3001
  gvera accede da: http://localhost:3001
```

**Regole**:
- `crm.db` = dati reali di Chiara. MAI toccare con seed/reset.
- `crm_dev.db` = dati di test (50 clienti). Libero per esperimenti.
- `seed_dev.py` forza `DATABASE_URL` PRIMA degli import → sicuro.
- `backup.py` usa `DATABASE_URL` dinamico → opera sempre sul DB attivo.
- `next.config.ts` supporta `NEXT_DIST_DIR` per cache separata (`.next` vs `.next-dev`).
- CORS in `api/main.py` include `:3000`, `:3001`, `:5173`, `192.168.1.23:3000`.

---

## Comandi

```bash
# ── Produzione (Chiara) ──
uvicorn api.main:app --host 0.0.0.0 --port 8000
cd frontend && npm run dev -- -H 0.0.0.0 -p 3000

# ── Sviluppo (gvera, PowerShell) ──
$env:DATABASE_URL="sqlite:///data/crm_dev.db"; uvicorn api.main:app --reload --port 8001
$env:NEXT_DIST_DIR=".next-dev"; $env:NEXT_PUBLIC_API_URL="http://localhost:8001"; npm run dev -- -p 3001

# Build check (OBBLIGATORIO prima di ogni commit)
cd frontend && npx next build

# Migrazioni (Alembic)
alembic upgrade head          # applica migrazioni pendenti
alembic revision -m "desc"    # crea nuova migrazione
alembic current               # mostra versione corrente

# Test (pytest — 60 test, tutti i domini)
pytest tests/ -v

# Test (E2E — richiede server avviato)
python tools/admin_scripts/test_crud_idor.py
python tools/admin_scripts/test_financial_idor.py
python tools/admin_scripts/test_agenda_idor.py
python tools/admin_scripts/test_ledger_dashboard.py

# Backup API
# POST /api/backup/create     (richiede JWT)
# GET  /api/backup/export     (JSON dati trainer)

# Reset & Seed (FERMA il server API prima!)
python tools/admin_scripts/reset_production.py      # DB pulito con solo Chiara (produzione)
python -m tools.admin_scripts.seed_dev              # 50 clienti su crm_dev.db (sviluppo)
python -m tools.admin_scripts.seed_realistic        # 50 clienti su DB attivo (attenzione!)
# Credenziali prod: chiarabassani96@gmail.com / chiarabassani
# Credenziali dev:  chiarabassani96@gmail.com / Fitness2026!

# Database
sqlite3 data/crm.db ".tables"

# AI (quando integrato)
ollama list
```

---

## Metriche Progetto

- **api/**: ~5,500 LOC Python — 8 modelli ORM, 9 router, 1 schema module
- **frontend/**: ~15,500 LOC TypeScript — 62 componenti, 8 hook modules, 6 pagine
- **core/**: ~11,100 LOC Python — moduli AI (workout, RAG, DNA) in attesa di API endpoints
- **DB**: 19 tabelle SQLite, FK enforced, multi-tenant via trainer_id
- **Test**: 60 pytest + 67 E2E
- **Sicurezza**: JWT auth, bcrypt, Deep Relational IDOR, 3-layer route protection
- **Cloud**: 0 dipendenze, 0 dati verso terzi

---

*Questo file e' la legge. Il codice che non la rispetta non viene mergiato.*
