# UPG-2026-03-06-33 - MyPortal Timeline Deadline Tracking

## Metadata

- Upgrade ID: UPG-2026-03-06-33
- Date: 2026-03-06
- Owner: Codex
- Area: Dashboard API + Clienti UX
- Priority: high
- Target release: codex_02

## Problem

La sola readiness (presenza/assenza) non basta per il problema operativo reale: non riuscire a tenere traccia delle scadenze su anamnesi, misurazioni e schede.

Serve una timeline con date e urgenza, non solo uno stato binario.

## Desired Outcome

Aggiungere nel payload `clinical-readiness` campi timeline deterministici (`next_due_date`, `days_to_due`, `timeline_status`, `timeline_reason`) e visualizzarli in `MyPortal` come board scadenze + colonna scadenza per cliente.

## Scope

- In scope:
  - estensione schema/API readiness con metadati timeline;
  - calcolo scadenze lato backend:
    - gap strutturali (anamnesi/baseline/scheda mancanti): scadenza oggi;
    - profili pronti: review periodiche (misure 30gg, scheda 21gg, anamnesi 180gg);
  - type sync frontend;
  - UI MyPortal con sezione timeline e badge urgenza.
- Out of scope:
  - notifiche push/email;
  - scheduler automatico;
  - logica medico-clinica.

## Impact Map

- Files/modules touched:
  - `api/routers/dashboard.py`
  - `api/schemas/financial.py`
  - `tests/test_dashboard_clinical_readiness.py`
  - `frontend/src/types/api.ts`
  - `frontend/src/app/(dashboard)/clienti/myportal/page.tsx`
  - `docs/upgrades/specs/UPG-2026-03-06-33-myportal-timeline-deadline-tracking.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: API + tests + frontend + docs
- Invariants:
  - endpoint resta read-only;
  - nessun nuovo endpoint;
  - multi-tenant safety invariata.

## Acceptance Criteria

- Functional:
  - ogni item readiness include campi timeline valorizzati;
  - `MyPortal` mostra timeline scadenze e data stato per cliente;
  - ordinamento timeline per data prossima.
- Technical:
  - test readiness backend verdi;
  - ruff/lint verdi sui file toccati.

## Test Plan

- Backend:
  - `venv\Scripts\python.exe -m pytest -q tests/test_dashboard_clinical_readiness.py -p no:cacheprovider`
  - `venv\Scripts\python.exe -m ruff check api/routers/dashboard.py api/schemas/financial.py tests/test_dashboard_clinical_readiness.py`
- Frontend:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/clienti/myportal/page.tsx" "src/types/api.ts" "src/app/(dashboard)/clienti/page.tsx" "src/components/layout/Sidebar.tsx"`

## Risks and Mitigation

- Risk 1: parsing date eterogenee (ISO date/datetime/string).
- Mitigation 1: parser robusto unico `_parse_iso_date`.
- Risk 2: scadenze non disponibili su dati legacy incompleti.
- Mitigation 2: fallback deterministico (`timeline_status=none`, `timeline_reason=monitoring`).

## Rollback Plan

- Revert mirato:
  - `api/routers/dashboard.py`
  - `api/schemas/financial.py`
  - `tests/test_dashboard_clinical_readiness.py`
  - `frontend/src/types/api.ts`
  - `frontend/src/app/(dashboard)/clienti/myportal/page.tsx`
