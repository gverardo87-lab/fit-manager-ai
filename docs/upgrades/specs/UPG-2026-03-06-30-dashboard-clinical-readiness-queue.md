# UPG-2026-03-06-30 - Dashboard Clinical Readiness Queue

## Metadata

- Upgrade ID: UPG-2026-03-06-30
- Date: 2026-03-06
- Owner: Codex
- Area: Dashboard + API
- Priority: medium
- Target release: codex_02

## Problem

In fase di adozione iniziale, i trainer con clienti legacy faticano a ricordare chi deve ancora:

- compilare/migrare anamnesi;
- registrare baseline misurazioni;
- ricevere una scheda assegnata.

Il rischio operativo e' perdita di continuita clinica durante il passaggio da workflow esterni a FitManager.

## Desired Outcome

Fornire in dashboard una coda operativa deterministica, read-only e privacy-safe che:

- ordina i clienti per priorita onboarding clinico;
- suggerisce una next-action diretta per ogni cliente;
- minimizza click e lavoro manuale nella migrazione iniziale.

## Scope

- In scope:
  - nuovo endpoint backend `GET /api/dashboard/clinical-readiness`;
  - schema API tipizzato backend/frontend per readiness queue;
  - pannello dashboard "Coda readiness clinica" con KPI e CTA dirette;
  - test backend dedicati su priorita e isolamento multi-tenant.
- Out of scope:
  - migrazione dati automatica (OCR/import file anamnesi/schede);
  - scritture automatiche su dati clinici;
  - redesign completo del modulo clienti.

## Impact Map

- Files/modules touched:
  - `api/routers/dashboard.py`
  - `api/schemas/financial.py`
  - `frontend/src/types/api.ts`
  - `frontend/src/hooks/useDashboard.ts`
  - `frontend/src/app/(dashboard)/page.tsx`
  - `tests/test_dashboard_clinical_readiness.py`
  - `docs/upgrades/specs/UPG-2026-03-06-30-dashboard-clinical-readiness-queue.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: API + frontend + tests + docs
- Invariants:
  - nessuna scrittura dati dal nuovo endpoint (solo read);
  - filtri multi-tenant rigidi su trainer autenticato;
  - dashboard resta privacy-safe (nessun importo economico introdotto).

## Acceptance Criteria

- Functional:
  - l'endpoint restituisce `summary` + `items` ordinati per priorita;
  - ogni item espone next action coerente (`anamnesi`, `baseline`, `scheda`, `ready`);
  - la dashboard mostra contatori readiness e lista clienti actionable con CTA dirette.
- Technical:
  - type sync backend/frontend coerente;
  - test backend dedicati verdi;
  - lint frontend verde sui file toccati.

## Test Plan

- Backend:
  - `venv\Scripts\python.exe -m pytest -q tests/test_dashboard_clinical_readiness.py -p no:cacheprovider`
- Frontend:
  - `npm --prefix frontend run lint -- "src/hooks/useDashboard.ts" "src/types/api.ts" "src/app/(dashboard)/page.tsx"`

## Risks and Mitigation

- Risk 1: rilevazione `legacy` anamnesi basata su heuristic (chiavi minime) puo classificare casi borderline.
- Mitigation 1: regola allineata al wizard attuale; hardening incrementale in microstep successivo con marker esplicito.
- Risk 2: backlog iniziale molto ampio puo generare overload visivo.
- Mitigation 2: pannello limita la lista ai primi clienti prioritari mantenendo contatori aggregati.

## Rollback Plan

- Revert dei file del microstep:
  - `api/routers/dashboard.py`
  - `api/schemas/financial.py`
  - `frontend/src/types/api.ts`
  - `frontend/src/hooks/useDashboard.ts`
  - `frontend/src/app/(dashboard)/page.tsx`
  - `tests/test_dashboard_clinical_readiness.py`
