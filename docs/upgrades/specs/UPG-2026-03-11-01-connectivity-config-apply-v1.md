# Patch Spec - Connectivity Config Apply v1

## Metadata

- Upgrade ID: UPG-2026-03-11-01
- Date: 2026-03-11
- Owner: Codex
- Area: Launch Readiness + Connectivity + Settings
- Priority: high
- Status: done
- Related plan: `docs/upgrades/specs/UPG-2026-03-10-20-connectivity-setup-wizard-plan-v1.md`

## Problem

Con `UPG-2026-03-10-21` FitManager sapeva leggere lo stato Tailscale/Funnel, ma non poteva
ancora applicare la propria parte di configurazione. Il trainer vedeva i check e il
prossimo passo, ma doveva ancora:

- modificare `data/.env` a mano;
- ricordarsi quali chiavi impostare;
- capire se fosse necessario un riavvio;
- tradurre il profilo desiderato (`trusted_devices`, `public_portal`) in variabili tecniche.

Questo manteneva il flusso a meta' tra prodotto guidato e runbook da tecnico.

## Desired Outcome

Consentire a FitManager di applicare in sicurezza la sola configurazione applicativa:

- `PUBLIC_PORTAL_ENABLED`
- `PUBLIC_BASE_URL`

senza gestire credenziali Tailscale e senza toccare installazione/Funnel al posto
dell'utente.

## Scope

- In scope:
  - endpoint protetto `POST /api/system/connectivity-config`;
  - scrittura sicura di `data/.env` preservando le altre chiavi;
  - aggiornamento immediato di `os.environ` in-process;
  - prime CTA reali nella card `Connettivita`;
  - invalidazione query coerente di `connectivity-status` e `health`;
  - test backend sul writer e sul contratto endpoint.

- Out of scope:
  - wizard multi-step completo;
  - login Tailscale in-app;
  - attivazione automatica di Funnel;
  - editing generale di qualsiasi chiave `.env` oltre a quelle di connettivita.

## Changes Implemented

### Backend

- Nuovo service [connectivity_config.py](c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/connectivity_config.py)
  con:
  - normalizzazione profilo `local_only` / `trusted_devices` / `public_portal`;
  - scrittura idempotente di `data/.env`;
  - rimozione di `PUBLIC_BASE_URL` quando il portale pubblico e disattivato;
  - aggiornamento di `os.environ` senza riavvio.
- Nuovi schema in [system.py](c:/Users/gvera/Projects/FitManager_AI_Studio/api/schemas/system.py):
  - `ConnectivityConfigRequest`
  - `ConnectivityConfigResponse`
- Esteso il router [system.py](c:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/system.py)
  con `POST /api/system/connectivity-config`

### Frontend

- Type sync in [api.ts](c:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/types/api.ts)
- Nuovo hook mutation [useConnectivityConfig.ts](c:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/hooks/useConnectivityConfig.ts)
- Estesa la card [ConnectivityStatusSection.tsx](c:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/settings/ConnectivityStatusSection.tsx)
  con:
  - input `Base URL pubblica`
  - CTA `Solo locale`
  - CTA `Dispositivi fidati`
  - CTA `Portale pubblico`
  - invalidazione stato connettivita e health dopo il salvataggio

## Verification

- Backend lint:
  - `venv\Scripts\ruff.exe check api\routers\system.py api\schemas\system.py api\services\connectivity_config.py tests\test_connectivity_config.py tests\test_connectivity_config_endpoint.py`
- Frontend lint:
  - `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/components/settings/ConnectivityStatusSection.tsx" "src/hooks/useConnectivityConfig.ts" "src/types/api.ts"`
- Test runtime:
  - `python -m pytest tests/test_connectivity_config.py tests/test_connectivity_config_endpoint.py -q -p no:cacheprovider`
  - **passed** (`2026-03-11`, eseguito in venv locale reale dall'utente)

## Risks / Residual Gaps

- Il prodotto salva ora la propria configurazione, ma non verifica ancora automaticamente
  se Funnel e il portale pubblico siano davvero raggiungibili end-to-end.
- La UI non e ancora un wizard completo: e una prima action surface sulla card esistente.
- La validazione della `PUBLIC_BASE_URL` e volutamente stretta sul minimo sicuro (`https`
  assoluto), ma non forza ancora un hostname `ts.net`.

## Next Smallest Step

`Phase B2 - Guided Verify`

- endpoint `connectivity-verify`;
- test applicativi dopo il salvataggio;
- surface UI che distingua `salvato` da `verificato`;
- prime basi del wizard lineare riapribile.
