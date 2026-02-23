# FitManager AI Studio

**CRM professionale per personal trainer e professionisti fitness a P.IVA.**

Gestione clienti, contratti, agenda, contabilita' e (prossimamente) programmazione allenamenti con AI locale.

---

## Stack

| Layer | Tecnologia |
|-------|-----------|
| **Frontend** | Next.js 16, React 19, TypeScript 5, shadcn/ui, Tailwind CSS 4, Recharts |
| **Backend** | FastAPI, SQLModel (SQLAlchemy), Pydantic v2 |
| **Database** | SQLite (PostgreSQL-ready), Alembic migrations |
| **Auth** | JWT (bcrypt), 3-layer: Edge Middleware + AuthGuard + API validation |
| **AI** (dormiente) | Ollama + LangChain + ChromaDB — moduli in `core/`, non ancora esposti via API |

**Privacy-first**: tutto gira in locale, zero cloud, zero dati verso terzi.

---

## Quick Start

### Prerequisiti

- Python 3.9+
- Node.js 18+
- (Opzionale) Ollama per moduli AI futuri

### Installazione

```bash
# 1. Clone
git clone <repo-url>
cd FitManager_AI_Studio

# 2. Backend
python -m venv venv
.\venv\Scripts\Activate.ps1          # Windows
pip install -e .

# 3. Frontend
cd frontend
npm install
cd ..

# 4. Database (prima volta)
alembic upgrade head

# 5. Seed dati demo (opzionale)
python tools/admin_scripts/reset_and_seed.py
# Credenziali demo: chiarabassani96@gmail.com / Fitness2024!
```

### Avvio

```bash
# Terminal 1 — Backend
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Apri `http://localhost:3000`

---

## Architettura

```
frontend/               Next.js 16 + React 19 + TypeScript
  src/app/              App Router (6 pagine + login)
  src/components/       56 componenti (shadcn/ui + dominio)
  src/hooks/            7 hook modules (React Query)
  src/types/api.ts      Interfacce TypeScript (mirror Pydantic)
       |
       | REST API (JSON, JWT auth)
       v
api/                    FastAPI + SQLModel ORM
  models/               7 modelli ORM
  routers/              9 router (Bouncer Pattern + Deep IDOR)
  schemas/              Pydantic v2 DTOs
       |
       v
SQLite                  data/crm.db — 19 tabelle, FK enforced
       |
core/                   Moduli AI (dormant — prossima fase)
  workout_generator     Generazione programmi allenamento (RAG)
  exercise_archive      Archivio 72 esercizi
  knowledge_chain       Q&A su documenti PDF
```

### Separazione dei layer

| Layer | Importa | Non importa mai |
|-------|---------|-----------------|
| `api/` | fastapi, sqlmodel, pydantic | `core/`, `frontend/` |
| `frontend/` | react, next, @tanstack/react-query | `api/`, `core/` (solo REST) |
| `core/` | stdlib, langchain, ollama | `api/`, `frontend/` |

---

## Funzionalita'

### Attive

- **Dashboard** — KPI in tempo reale (clienti attivi, entrate mensili, rate in scadenza)
- **Clienti** — CRUD completo, ricerca, anagrafica
- **Contratti** — Gestione contratti con piano pagamenti, pagamenti parziali, storico, auto-close/reopen
- **Agenda** — Calendario interattivo (react-big-calendar), drag & drop, colori per categoria e stato, credit engine
- **Cassa** — Libro mastro, spese ricorrenti (conferma manuale), split entrate/uscite, aging report scadenze
- **Impostazioni** — Configurazione profilo trainer

### Sicurezza

- **Multi-tenancy**: `trainer_id` da JWT, iniettato server-side, mai dal client
- **Deep Relational IDOR**: ownership verificata attraverso catena FK
- **Bouncer Pattern**: ogni endpoint valida precondizioni con early return
- **Atomic Transactions**: operazioni multi-tabella con singolo commit
- **Soft Delete**: `deleted_at` su tutte le tabelle business
- **Audit Trail**: ogni CREATE/UPDATE/DELETE loggato con diff JSON

### Prossima fase (AI locale)

- Generazione programmi allenamento personalizzati via RAG + Ollama
- Q&A su documenti PDF (manuali, ricerche scientifiche)
- Archivio esercizi con pattern di movimento

---

## Comandi

```bash
# Backend
uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Build check (obbligatorio prima di ogni commit)
cd frontend && npx next build

# Test (pytest — 60 test)
pytest tests/ -v

# Migrazioni
alembic upgrade head
alembic revision -m "descrizione"

# Seed dati demo
python tools/admin_scripts/reset_and_seed.py

# Database
sqlite3 data/crm.db ".tables"
```

---

## Documentazione tecnica

Le regole architetturali e i design pattern sono documentati nei file CLAUDE.md:

- [CLAUDE.md](CLAUDE.md) — Manifesto architetturale (root)
- [api/CLAUDE.md](api/CLAUDE.md) — Backend rules (pattern, sicurezza, test)
- [frontend/CLAUDE.md](frontend/CLAUDE.md) — Frontend rules (componenti, hook, visual design)
- [core/CLAUDE.md](core/CLAUDE.md) — AI modules (dormant)

---

## Metriche

| Layer | LOC | Componenti |
|-------|-----|-----------|
| `api/` | ~4,900 | 7 modelli, 9 router, 60 test |
| `frontend/` | ~12,600 | 56 componenti, 7 hook, 7 pagine |
| `core/` | ~11,100 | Moduli AI (dormant) |
| **DB** | — | 19 tabelle, FK enforced |

---

**Maintained by**: G. Verardo
