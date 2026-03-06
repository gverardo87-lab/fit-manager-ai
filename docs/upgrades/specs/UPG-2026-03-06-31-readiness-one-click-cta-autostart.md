# UPG-2026-03-06-31 - Readiness One-Click CTA Autostart

## Metadata

- Upgrade ID: UPG-2026-03-06-31
- Date: 2026-03-06
- Owner: Codex
- Area: Dashboard + Client UX
- Priority: medium
- Target release: codex_02

## Problem

La coda readiness clinica mostrava CTA corrette, ma ancora con attrito operativo:

- click su "Compila/Rivedi anamnesi" portava alla pagina ma richiedeva click extra per aprire il wizard;
- click su "Assegna scheda" apriva il profilo tab Schede ma richiedeva click extra su "Nuova Scheda".

## Desired Outcome

Rendere le CTA della readiness realmente one-click:

- anamnesi: apertura automatica del wizard;
- scheda: apertura automatica del TemplateSelector nel tab Schede.

## Scope

- In scope:
  - update deep-link readiness backend con flag URL:
    - `startWizard=1` per anamnesi;
    - `startScheda=1` per schede;
  - consumo frontend dei flag con auto-open e pulizia querystring;
  - test backend aggiornati sulle nuove URL.
- Out of scope:
  - modifica logica di priorita readiness;
  - nuovi endpoint o nuove entita persistenti.

## Impact Map

- Files/modules touched:
  - `api/routers/dashboard.py`
  - `frontend/src/app/(dashboard)/clienti/[id]/anamnesi/page.tsx`
  - `frontend/src/app/(dashboard)/clienti/[id]/page.tsx`
  - `tests/test_dashboard_clinical_readiness.py`
  - `docs/upgrades/specs/UPG-2026-03-06-31-readiness-one-click-cta-autostart.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: API + frontend + tests + docs
- Invariants:
  - nessuna scrittura automatica non richiesta;
  - ownership/multi-tenant invariata;
  - fallback manuale invariato (utente puo comunque aprire i wizard via UI).

## Acceptance Criteria

- Functional:
  - CTA anamnesi da readiness apre direttamente wizard su pagina anamnesi;
  - CTA scheda da readiness apre direttamente TemplateSelector nel profilo cliente;
  - flag URL consumati dopo uso (no riapertura su refresh/back).
- Technical:
  - lint frontend file toccati senza errori;
  - test readiness backend verdi con href aggiornati.

## Test Plan

- Backend:
  - `venv\Scripts\python.exe -m pytest -q tests/test_dashboard_clinical_readiness.py -p no:cacheprovider`
- Frontend:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/clienti/[id]/anamnesi/page.tsx" "src/app/(dashboard)/clienti/[id]/page.tsx"`

## Risks and Mitigation

- Risk 1: auto-open ripetuto su reload/back.
- Mitigation 1: consumare e rimuovere flag dalla querystring subito dopo il trigger.
- Risk 2: setState in effect in conflitto con lint rules del progetto.
- Mitigation 2: pattern `requestAnimationFrame` per apertura modal/dialog.

## Rollback Plan

- Revert mirato:
  - `api/routers/dashboard.py`
  - `frontend/src/app/(dashboard)/clienti/[id]/anamnesi/page.tsx`
  - `frontend/src/app/(dashboard)/clienti/[id]/page.tsx`
  - `tests/test_dashboard_clinical_readiness.py`
