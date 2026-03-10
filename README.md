# FitManager AI Studio

CRM locale per personal trainer e professionisti fitness.
Obiettivo attuale: trasformare il repository da "prodotto in sviluppo" a baseline affidabile per il lancio.

## Cosa copre oggi

- Clienti, contratti, rate, agenda e cassa
- Schede allenamento, libreria esercizi e monitoraggio cliente
- Workspace operativi `Oggi` e `Rinnovi & Incassi`
- Backup, setup, licenza e portale pubblico anamnesi
- Guida integrata e componenti CRM per uso desktop/tablet

## Snapshot reale del repository (2026-03-10)

| Area | Snapshot |
|---|---|
| `api/` | 123 file Python, 21 router module, 21 model module, 115 handler REST annotati |
| `frontend/src/` | 250 file TS/TSX, 24 page route, 151 componenti, 22 hook file |
| `tests/` | 27 file pytest |
| `core/` | 27 file Python, moduli AI/legacy fuori dal percorso critico di lancio |
| `tools/` | 63 script, di cui 48 in `tools/admin_scripts/` |
| `data/` | `crm.db`, `crm_dev.db`, `catalog.db` |

Questi numeri sono stati riallineati con `rg` sul repo. Evitare di reintrodurre conteggi manuali non verificati.

## Avvio locale

Prerequisiti minimi:

- Node.js 20+
- npm
- Python 3.12
- un virtualenv funzionante per il progetto
- SQLite disponibile in PATH se si usano i check manuali DB

### Sviluppo (PowerShell)

```powershell
# Terminale 1 - Backend su crm_dev.db
$env:DATABASE_URL = "sqlite:///data/crm_dev.db"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8001

# Terminale 2 - Frontend
cd frontend
npm run dev
```

Apri `http://localhost:3001`.

### Produzione da sorgente

Per il lancio reale preferire installer e `installer/launcher.bat`.
Se il backend viene avviato manualmente da sorgente, il gate licenza va esplicitamente attivato:

```powershell
$env:LICENSE_ENFORCEMENT_ENABLED = "true"
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Il frontend di produzione usa:

```powershell
cd frontend
npm run build
npm run prod
```

## Topologia runtime

| Ambiente | Frontend | Backend | Database |
|---|---|---|---|
| Dev | `3001` | `8001` | `data/crm_dev.db` |
| Prod | `3000` | `8000` | `data/crm.db` |

Il frontend deduce la base URL API dal `window.location` e usa la coppia di porte corretta.

## Struttura del progetto

```text
frontend/      Next.js 16 + React 19 + TypeScript
  src/app/     App Router con route dashboard, setup, licenza e public portal
  src/components/
  src/hooks/
  src/types/api.ts

api/           FastAPI + SQLModel + Pydantic
  routers/     Domini REST, auth, backup, workspace, training science
  models/      ORM business e supporto licenza/public portal
  schemas/     Contratti API e DTO
  services/    Workspace engine, training science, readiness, auditing

core/          Moduli AI/legacy non obbligatori per il CRM core
tools/         Seed, smoke test, build, migration, admin script
data/          Database SQLite, checksum e asset runtime locali
docs/          Governance upgrade, workboard, specifiche
installer/     Launcher e packaging Windows
```

## Domini principali

- `Clienti`: anagrafica, anamnesi, misurazioni e monitoraggio
- `Contratti + Rate`: integrita pagamenti, stato contratto, storico incassi
- `Agenda`: sessioni, drag and drop, consumo crediti e sincronizzazione contratto
- `Cassa`: ledger, spese ricorrenti, previsioni, aging
- `Schede + Esercizi`: builder, libreria, media, analisi smart
- `Workspace`: code operative specializzate per lavoro giornaliero e finanza

## Quality gate minimi

```powershell
# Backend static check
venv\Scripts\ruff.exe check api tests

# Frontend lint completo
& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- src

# Build frontend
& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run build

# Backend tests
python -m pytest -q tests

# Frontend tests
& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run test
```

Baseline verificata il 2026-03-10:

- `ruff check api tests`: verde
- lint frontend globale: rosso (`29` errori, `57` warning)
- build frontend: compile OK, poi bloccato dall'ambiente con `spawn EPERM`
- pytest backend: bloccato da virtualenv locale misconfigurato

## Stato pre-lancio

La documentazione autoritativa ora descrive il repository reale, ma il prodotto non e ancora "release-ready".
La sequenza minima di hardening raccomandata e:

1. Ripristinare toolchain e virtualenv in modo ripetibile.
2. Portare `eslint src` a zero errori, iniziando da hook order e render-phase side effects.
3. Ripristinare una suite backend critica eseguibile su pagamenti, workspace e readiness.
4. Eseguire smoke reali su setup, licenza, backup/restore, LAN/Tailscale e public portal.
5. Congelare la baseline con checklist di rilascio e rollback pack.

Dettaglio operativo: `docs/upgrades/specs/UPG-2026-03-10-05-documentation-baseline-and-launch-readiness-plan.md`.

## Documentazione

- `ARCHITECTURE.md`: fotografia tecnica e piano di hardening
- `CLAUDE.md`: regole di progetto, runbook e riferimenti operativi estesi
- `AGENTS.md`: workflow microstep, quality gate e policy di sync
- `docs/upgrades/`: specifiche, log upgrade e allineamento release

**Maintained by**: G. Verardo
