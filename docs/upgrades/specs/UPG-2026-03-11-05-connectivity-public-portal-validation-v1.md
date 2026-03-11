# Patch Spec - Connectivity Public Portal Validation v1

## Metadata

- Upgrade ID: UPG-2026-03-11-05
- Date: 2026-03-11
- Owner: Codex
- Area: Launch Readiness + Connectivity + Public Portal
- Priority: high
- Status: done
- Depends on:
  - `UPG-2026-03-10-21`
  - `UPG-2026-03-11-01`
  - `UPG-2026-03-11-02`
  - `UPG-2026-03-11-03`
  - `UPG-2026-03-11-04`

## Problem

Il workstream `Connectivity Setup Wizard` sapeva gia:

- rilevare lo stato Tailscale/Funnel;
- applicare `PUBLIC_PORTAL_ENABLED` e `PUBLIC_BASE_URL`;
- verificare la reachability minima dell'origine pubblica via `{PUBLIC_BASE_URL}/health`;
- guidare il trainer con uno stepper dentro `Impostazioni`.

Mancava pero il test funzionale del link anamnesi pubblico reale. In pratica il prodotto
era in grado di dire "l'origine pubblica risponde", ma non ancora "questo link anamnesi
monouso funziona davvero con pagina pubblica e token".

Per un prodotto local-first pensato per trainer non tecnici, questa differenza e'
critica: il sistema deve poter validare l'esperienza reale del cliente finale, non solo
la reachability infrastrutturale.

## Desired Outcome

Da `Impostazioni -> Connettivita`, il trainer deve poter:

1. scegliere un cliente attivo di prova;
2. generare un link anamnesi monouso reale;
3. copiare o aprire il link;
4. chiedere a FitManager di validare automaticamente:
   - la pagina pubblica Next `/public/anamnesi/{token}`;
   - l'endpoint pubblico `/api/public/anamnesi/validate?token=...`;
   - la coerenza minima del payload pubblico.

Il verdetto finale deve distinguere chiaramente tra:

- `ready`
- `partial`
- `blocked`

## Scope

- In scope:
  - nuovo endpoint protetto `POST /api/system/connectivity-portal-validation`
  - nuovo service backend `connectivity_portal_validation.py`
  - validazione guidata del link anamnesi reale dentro il wizard `Connettivita`
  - nuova panel frontend per generazione/copia/apertura/verifica del link
  - test backend service + endpoint
  - sync docs su runbook e release checklist

- Out of scope:
  - invio automatico WhatsApp/email al cliente
  - test da smartphone reale via rete mobile
  - first-run promotion del wizard fuori da `Impostazioni`
  - attivazione automatica di Funnel o login Tailscale

## Implementation Summary

### Backend

- Nuovo service:
  - `api/services/connectivity_portal_validation.py`
- Nuovo endpoint:
  - `POST /api/system/connectivity-portal-validation`
- Nuovi schema:
  - `ConnectivityPortalValidationRequest`
  - `ConnectivityPortalValidationResponse`

La validazione usa `urllib` stdlib e 3 check:

1. `runtime_profile`
   - il runtime deve risultare su `public_portal`
2. `public_page`
   - la pagina pubblica anamnesi deve rispondere correttamente
3. `public_validate`
   - il token pubblico deve risultare valido e restituire il payload minimo atteso

### Frontend

- Nuova panel:
  - `frontend/src/components/settings/ConnectivityPortalValidationPanel.tsx`
- Nuovo hook:
  - `frontend/src/hooks/usePortalValidation.ts`
- Estensione wizard:
  - `frontend/src/components/settings/ConnectivitySetupWizard.tsx`
- Type sync:
  - `frontend/src/types/api.ts`
- Reuse share token flow:
  - `frontend/src/hooks/useClients.ts`

Il trainer usa un cliente attivo, genera il link di prova, poi lancia la validazione
funzionale direttamente dal prodotto.

## Verification

Static checks:

- `venv\Scripts\ruff.exe check api\schemas\system.py api\routers\system.py api\services\connectivity_portal_validation.py tests\test_connectivity_portal_validation.py tests\test_connectivity_portal_validation_endpoint.py`
- `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/components/settings/ConnectivitySetupWizard.tsx" "src/components/settings/ConnectivityPortalValidationPanel.tsx" "src/hooks/usePortalValidation.ts" "src/hooks/useClients.ts" "src/types/api.ts"`
- `git diff --check`

Runtime checks eseguiti nel terminale utente:

- `python -m pytest tests/test_connectivity_portal_validation.py tests/test_connectivity_portal_validation_endpoint.py -q -p no:cacheprovider`
  - risultato: `5 passed in 0.46s`
- `python -m pytest tests/test_connectivity_runtime.py tests/test_connectivity_status_endpoint.py tests/test_connectivity_config.py tests/test_connectivity_config_endpoint.py tests/test_connectivity_verify.py tests/test_connectivity_verify_endpoint.py tests/test_connectivity_portal_validation.py tests/test_connectivity_portal_validation_endpoint.py -q -p no:cacheprovider`
  - risultato: `21 passed in 1.97s`

## Risks / Residual Gaps

- La validazione guidata avviene dal PC trainer e non sostituisce ancora il test reale da
  smartphone su rete esterna.
- Il probe usa una URL pubblica configurata dal trainer: in contesto single-tenant e'
  accettabile, ma se il prodotto evolvesse verso modelli multi-tenant varra la pena
  limitare gli hostname consentiti.
- Il wizard e ora completo dentro `Impostazioni`, ma il first-run post-installazione non
  lo promuove ancora automaticamente.

## Product Outcome

Con questo step il workstream `Connectivity Setup Wizard` chiude il primo percorso
funzionale completo:

`Rileva -> Applica -> Verifica origine -> Valida link anamnesi reale`

FitManager smette di limitarsi a "diagnosticare la rete" e inizia a validare davvero
l'esperienza cliente finale del portale anamnesi pubblico.
