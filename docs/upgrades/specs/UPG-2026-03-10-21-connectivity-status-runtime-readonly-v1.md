# Patch Spec - Connectivity Status Runtime Read-only v1

## Metadata

- Upgrade ID: UPG-2026-03-10-21
- Date: 2026-03-10
- Owner: Codex
- Area: Launch Readiness + Connectivity + Settings
- Priority: high
- Status: done
- Related plan: `docs/upgrades/specs/UPG-2026-03-10-20-connectivity-setup-wizard-plan-v1.md`

## Problem

Il piano del `Connectivity Setup Wizard` e' formalizzato, ma il prodotto non aveva ancora
una base runtime affidabile da cui partire:

- nessun endpoint read-only per leggere stato Tailscale/Funnel;
- nessun contratto frontend/backend per il profilo di connettivita';
- nessuna surface utente che distinguesse `non installato`, `non connesso` e
  `permessi insufficienti`;
- nessun punto minimo in `Impostazioni` da cui guidare il trainer prima del wizard vero.

Senza questo layer, il futuro wizard rischierebbe di poggiare su euristiche opache o su
runbook esterni invece che sullo stato reale della macchina.

## Desired Outcome

Introdurre il primo microstep runtime reale del workstream connettivita':

- endpoint protetto `GET /api/system/connectivity-status`;
- service backend read-only che legge Tailscale/Funnel senza scrivere `.env`;
- type sync frontend/backend;
- nuova sezione `Connettivita` in `Impostazioni`;
- semafori leggibili, `next action` esplicita e lista dei requisiti mancanti.

## Scope

- In scope:
  - nuovo `api/services/connectivity_runtime.py`;
  - estensione schema `api/schemas/system.py`;
  - endpoint protetto in `api/routers/system.py`;
  - test backend runtime + contratto HTTP;
  - hook frontend dedicato;
  - card read-only in `Impostazioni`.

- Out of scope:
  - scrittura `PUBLIC_PORTAL_ENABLED` / `PUBLIC_BASE_URL`;
  - wizard multi-step completo;
  - login Tailscale in-app;
  - attivazione automatica Funnel;
  - modifiche a DB o launcher.

## Changes Implemented

### Backend

- Nuovo service [connectivity_runtime.py](c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/connectivity_runtime.py)
  con detection read-only di:
  - presenza CLI Tailscale;
  - versione CLI;
  - stato locale `tailscale status --json`;
  - DNS name e IP Tailscale;
  - stato `tailscale funnel status`;
  - coerenza tra `PUBLIC_BASE_URL` e DNS `ts.net`.
- Classificazione esplicita degli errori runtime:
  - `not_installed`
  - `not_connected`
  - `permission_denied`
  - `not_enabled`
  - `error`
- Profili derivati:
  - `local_only`
  - `trusted_devices`
  - `public_portal`
- `next_recommended_action_code` e `next_recommended_action_label` calcolati in modo
  deterministico.

### API Contract

- Estesi gli schema in [system.py](c:/Users/gvera/Projects/FitManager_AI_Studio/api/schemas/system.py):
  - `ConnectivityStatusResponse`
  - `ConnectivityCheck`
  - nuovi literal type per profile/status/action.
- Nuovo endpoint protetto in [system.py](c:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/system.py):
  - `GET /api/system/connectivity-status`

### Frontend

- Type sync in [api.ts](c:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/types/api.ts)
- Nuovo hook [useConnectivityStatus.ts](c:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/hooks/useConnectivityStatus.ts)
- Nuova card [ConnectivityStatusSection.tsx](c:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/settings/ConnectivityStatusSection.tsx)
- Integrazione in [page.tsx](c:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/app/(dashboard)/impostazioni/page.tsx)
- Utility di mapping stato/profilo estese in
  [system-status-utils.ts](c:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/settings/system-status-utils.ts)

## Verification

- Backend lint:
  - `venv\Scripts\ruff.exe check api\routers\system.py api\schemas\system.py api\services\connectivity_runtime.py tests\test_connectivity_runtime.py tests\test_connectivity_status_endpoint.py`
- Frontend lint:
  - `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/app/(dashboard)/impostazioni/page.tsx" "src/components/settings/ConnectivityStatusSection.tsx" "src/components/settings/system-status-utils.ts" "src/hooks/useConnectivityStatus.ts" "src/types/api.ts"`
- Test runtime:
  - `python -m pytest tests/test_connectivity_runtime.py tests/test_connectivity_status_endpoint.py -q -p no:cacheprovider`
  - **passed** (`2026-03-11`, eseguito in venv locale reale dall'utente)

## Risks / Residual Gaps

- Il layer e' ancora solo read-only: nessuna scrittura guidata di `.env`.
- Il rilevamento Tailscale dipende dal client locale e puo restituire `permission_denied`
  anche quando Tailscale e' installato ma non accessibile dall'utente che esegue FitManager.
- Il wizard vero e proprio non esiste ancora: la nuova card spiega lo stato, ma non
  accompagna ancora l'utente attraverso tutti gli step.

## Next Smallest Step

`Phase B - Guided Runtime Apply`

- endpoint write-safe per applicare `PUBLIC_PORTAL_ENABLED` / `PUBLIC_BASE_URL`;
- validazione guidata del profilo desiderato;
- CTA reali dalla card `Connettivita`;
- base del wizard post-installazione.
