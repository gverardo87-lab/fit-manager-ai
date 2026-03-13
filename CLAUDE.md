# CLAUDE.md — FitManager AI Studio

CRM locale Windows per chinesiologi, personal trainer e professionisti fitness a P.IVA.
Dati sul PC del professionista, zero cloud obbligatorio, privacy-first.

## Stack

```
Python 3.12 + FastAPI + SQLModel + SQLite (WAL)     → api/     (144 file)
Next.js 16 + React 19 + TypeScript 5 + shadcn/ui    → frontend/ (293 file)
Langchain + Ollama (moduli AI dormenti)              → core/    (27 file)
```

Distribuzione: PyInstaller + Next.js standalone + Inno Setup (Windows installer).

## Architettura

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  frontend/  │────>│    api/      │────>│  data/*.db   │
│  Next.js 16 │     │  FastAPI     │     │  SQLite WAL  │
│  porta 3000 │     │  porta 8000  │     └──────────────┘
└─────────────┘     └──────────────┘
                          │
              ┌───────────┼───────────┐
              v           v           v
         crm.db      catalog.db  nutrition.db
        (business)  (tassonomia) (alimenti CREA)
```

- **crm.db**: 22 tabelle business (clienti, contratti, workout, piani alimentari). Tenant-isolated via `trainer_id`.
- **catalog.db**: 7 tabelle tassonomia scientifica (muscoli, articolazioni, condizioni). Read-only, condiviso.
- **nutrition.db**: 8 tabelle catalogo alimenti (CREA 2019 + USDA). Read-only, condiviso. 226 alimenti attivi.
- **Dual env**: prod (porta 8000/3000, crm.db) + dev (porta 8001/3001, crm_dev.db).
- **Formula porte**: `frontend_port - 3000 + 8000 = backend_port`.

## Comandi operativi

```bash
# --- Avvio sviluppo ---
./venv/Scripts/uvicorn api.main:app --port 8001 --host 0.0.0.0    # backend dev
cd frontend && npm run dev                                         # frontend dev (porta 3001)

# --- Test ---
./venv/Scripts/python -m pytest tests/ -v                          # 298 test backend
cd frontend && npm test                                            # 69 vitest (data protection)

# --- Quality gate (obbligatorio prima di commit) ---
bash tools/scripts/check-all.sh                                    # ruff check api/ + next build

# --- Lint singoli ---
./venv/Scripts/ruff check api/                                     # backend lint
cd frontend && npx next build                                      # frontend build (zero errori TS)

# --- Migrazioni ---
./venv/Scripts/alembic upgrade head                                # crm.db
./venv/Scripts/alembic -c alembic_nutrition.ini upgrade head       # nutrition.db

# --- Utility ---
bash tools/scripts/kill-port.sh 8001                               # kill zombie uvicorn
bash tools/scripts/restart-backend.sh                              # restart backend dev
```

## 3 database — 3 session factory

```python
from api.database import get_session            # crm.db (business, tenant-isolated)
from api.database import get_catalog_session    # catalog.db (tassonomia, read-only)
from api.database import get_nutrition_session  # nutrition.db (alimenti, read-only)
```

Tutte con PRAGMA: `journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout=5000`.

## Regole non negoziabili

1. **Privacy-first**: dati clinici e finanziari mai esposti in viste pubbliche.
2. **Multi-tenant safety**: ogni query filtra per `trainer_id`. Mai bypassare ownership.
3. **Bouncer Pattern**: ogni endpoint verifica ownership via bouncer. Non trovato = 404, mai 403.
4. **Mass assignment prevention**: `trainer_id` e `id` mai in schema Create. `extra: "forbid"`.
5. **Atomic transactions**: operazioni multi-tabella = un singolo `session.commit()`.
6. **Determinismo**: flussi business-critical spiegabili, auditabili, prevedibili.
7. **Dati in `data/`**: DB, media, licenza, .env, log — tutto sotto `data/`. Sopravvive a upgrade.
8. **Zero path assoluti hardcoded**: usare `DATA_DIR` da `api/config.py` (gestisce `sys.frozen`).
9. **Italiano nativo**: UI, toast, placeholder in italiano. Codice in inglese.
10. **SSoT scientifica**: backend = unica fonte dati scientifici. Frontend consuma via API, mai duplica costanti.

## Pattern critici

### Backend (dettagli in `api/CLAUDE.md`)
- **Deep Relational IDOR**: catena FK per ownership (Rate → Contract → `trainer_id`).
- **Contract Integrity Engine**: 12 livelli di protezione (residual, chiuso guard, auto-close, overpayment, cascade).
- **Invalidazione simmetrica**: operazioni inverse (pay/unpay) invalidano le stesse query.
- **Audit trail**: `log_audit()` su ogni CREATE/UPDATE/DELETE di entita' business.
- **Soft delete**: `deleted_at` su tutte le tabelle business. SELECT filtra sempre `deleted_at == None`.

### Frontend (dettagli in `frontend/CLAUDE.md`)
- **Hook per dominio**: 24 moduli, uno per dominio. Ogni mutation invalida query correlate + toast.
- **Type sync**: `types/api.ts` = contratto. `Optional[X]` Pydantic → `X | null` TypeScript.
- **toISOLocal()**: MAI `toISOString()` per payload API (perde offset fuso orario).
- **Max 300 LOC** per file di logica, 400 per dati/config.
- **AuthGuard**: MAI leggere browser API (`document`, `window`) in `useState` initializer.

### Cross-layer
- **`extra: "forbid"` su Pydantic**: un campo typo nel payload = 422 silenzioso. Dopo refactor payload, verificare sempre nomi campo vs schema.
- **Proxy Next.js intercetta PRIMA dei rewrite**: `/api` in `PUBLIC_ROUTES` (auth JWT gestita dal backend).
- **Seed data**: 344 esercizi JSON + 426 relazioni + 494 media in `data/exercises/`, seed idempotente al startup.

## Motori scientifici

| Motore | Path | Funzione |
|--------|------|----------|
| Training Science | `api/services/training_science/` (~3500 LOC) | Periodizzazione, EMG, volume MEV/MAV/MRV |
| Safety Engine | `api/services/condition_rules.py` | 47 condizioni, 80 pattern rules |
| Nutrition Science | `api/services/nutrition_science/` (~2100 LOC) | Piano LARN 7gg, scoring 3 assi |
| Clinical Analysis | `frontend/src/lib/clinical-analysis.ts` | Range normativi OMS/ACSM (client-side) |
| Smart Programming | `frontend/src/lib/smart-programming/` | Scoring 14D (consumer del backend SSoT) |

## Agent Skills (quality automation)

Skills installate in `.agents/skills/` — knowledge base attive per audit e code generation.

| Skill | Source | Quando si attiva |
|-------|--------|-----------------|
| `vercel-react-best-practices` | Vercel Labs | Scrittura, review o refactor di codice React/Next.js. 62 regole in 8 categorie, prioritizzate per impatto. Le regole chiave sono codificate in `frontend/CLAUDE.md` sezione "React Performance Rules". |
| `web-design-guidelines` | Vercel Labs | Audit UI on-demand (`/web-design-guidelines <file>`). Scarica linee guida aggiornate da GitHub e controlla conformita' WCAG + UX. |
| `code-review` | Built-in | Review pull request (`/code-review`). Analisi diff, architettura, sicurezza. |
| `frontend-design` | Built-in | Creazione UI production-grade (`/frontend-design`). Design system coerente, no estetica AI generica. |

**Integrazione nel workflow**:
- Le regole Vercel CRITICAL/HIGH sono codificate nei CLAUDE.md come regole operative (non servono invocazioni esplicite).
- `/web-design-guidelines` per audit accessibilita' pre-lancio su componenti specifici.
- `/code-review` su ogni PR verso main.
- `/frontend-design` quando si crea una nuova pagina o componente complesso.

## Struttura file governance

| File | Scopo | Quando leggerlo |
|------|-------|-----------------|
| `CLAUDE.md` (questo) | Entry point, regole cross-layer | Sempre — e' il primo file da leggere |
| `api/CLAUDE.md` | Pattern backend, schema, endpoint, test | Quando tocchi `api/` |
| `frontend/CLAUDE.md` | Pattern frontend, componenti, pitfalls | Quando tocchi `frontend/` |
| `core/CLAUDE.md` | Moduli AI dormenti, stato legacy | Quando tocchi `core/` |
| `MANIFESTO.md` | Missione prodotto, visual identity, principi UX | Quando serve contesto di prodotto |
| `LAUNCH_SCOPE.md` | Cosa e' in scope per il lancio | Quando prioritizzi feature |
| `POSTMORTEMS.md` | Lezioni da errori passati | Quando incontri un pattern sospetto |
| `AGENTS.md` | Delivery loop, quality gates, commit standard | Quando coordini con altri agenti |

## Commit

Formato: `area: descrizione` — es. `api: ...`, `nutrizione: ...`, `dashboard: ...`, `fix: ...`

Quality gate obbligatorio: `bash tools/scripts/check-all.sh` (ruff + next build).
Ogni commit deve lasciare il branch rilasciabile per il proprio scope.

## Pitfalls ricorrenti (top 5)

1. **`toISOString()` perde timezone**: usare `toISOLocal()` da `lib/format.ts` per ogni payload API con date.
2. **`extra: "forbid"` + campo typo = 422**: verificare nomi campo con curl vs schema Pydantic dopo ogni refactor.
3. **PyInstaller `Path(__file__)`**: non funziona in bundle → usare `DATA_DIR` da `config.py`.
4. **Radix: no `<label>` + Checkbox**: causa double-toggle. Usare `<div onClick>` + `stopPropagation`.
5. **`useState(() => browserAPI())`**: hydration mismatch. Usare `useState(false)` + `useEffect`.

## Credenziali sviluppo

- Dev: chiarabassani96@gmail.com / Fitness2026!
- Prod: chiarabassani96@gmail.com / chiarabassani
