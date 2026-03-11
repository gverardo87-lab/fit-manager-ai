# Patch Spec - Connectivity Verify v1

## Metadata

- Upgrade ID: UPG-2026-03-11-03
- Date: 2026-03-11
- Owner: Codex
- Area: Launch Readiness + Connectivity + Settings
- Priority: high
- Status: done
- Depends on:
  - `UPG-2026-03-10-21`
  - `UPG-2026-03-11-01`
  - `UPG-2026-03-11-02`

## Problem

La surface `Connettivita` sapeva gia:

- leggere lo stato reale di Tailscale/Funnel;
- applicare `PUBLIC_PORTAL_ENABLED` e `PUBLIC_BASE_URL`;
- spiegare cosa mancava per i tre profili.

Ma restava un gap importante: non distingueva ancora tra configurazione semplicemente
salvata e configurazione davvero verificata end-to-end.

Per il profilo `public_portal`, questo lasciava aperta la domanda piu importante:
"il link pubblico risponde davvero dall'esterno?".

## Desired Outcome

FitManager deve offrire una verifica guidata on-demand che:

- riutilizza il runtime reale gia letto da `connectivity-status`;
- restituisce un verdetto sintetico `ready | partial | blocked`;
- mostra il target verificato (`PUBLIC_BASE_URL/health`) quando rilevante;
- espone il prossimo passo consigliato se la verifica non e completa;
- non introduce ancora persistenza di stato o wizard complesso.

## Scope

- In scope:
  - nuovo endpoint protetto `POST /api/system/connectivity-verify`
  - service backend dedicato alla verifica end-to-end
  - nuovi schema/type sync backend/frontend
  - CTA `Verifica configurazione` in `Impostazioni`
  - pannello UI che separa `configurata` da `verificata`
  - test backend service + endpoint

- Out of scope:
  - wizard stepper completo
  - attivazione automatica di Tailscale/Funnel
  - persistenza storica dell'ultima verifica
  - generazione di token anamnesi reali come parte del test

## Implementation Summary

### Backend

- nuovo service `api/services/connectivity_verify.py`
- verifica guidata basata su:
  - `build_connectivity_status()`
  - probe HTTP dell'origine pubblica `{PUBLIC_BASE_URL}/health`
- nuovo schema `ConnectivityVerifyResponse`
- nuovo endpoint:
  - `POST /api/system/connectivity-verify`

### Frontend

- type sync in `frontend/src/types/api.ts`
- nuovo hook `useVerifyConnectivity()`
- nuova surface `Verifica finale` dentro `ConnectivityStatusSection`
- bottone `Verifica configurazione`
- blocco URL pubblico non verificabile se la bozza non e stata ancora salvata

## Product Decision

La verifica del portale pubblico usa `GET {PUBLIC_BASE_URL}/health` come check minimo
e onesto di end-to-end reachability dell'origine pubblica:

- prova che il frontend origin risponde davvero;
- prova che il rewrite/proxy same-origin verso il backend e vivo;
- evita di generare token o dati business come parte del test.

Questo non sostituisce ancora un test funzionale completo di anamnesi pubblica, ma chiude
il gap fondamentale tra "configurazione scritta" e "origine pubblica realmente raggiungibile".

## Verification

- `venv\Scripts\ruff.exe check api\schemas\system.py api\routers\system.py api\services\connectivity_verify.py tests\test_connectivity_verify.py tests\test_connectivity_verify_endpoint.py`
- `C:\Program Files\nodejs\npm.cmd --prefix frontend run lint -- "src/components/settings/ConnectivityStatusSection.tsx" "src/components/settings/connectivity-status-ui.tsx" "src/components/settings/system-status-utils.ts" "src/hooks/useVerifyConnectivity.ts" "src/types/api.ts"`
- `git diff --check`
- `python -m pytest tests/test_connectivity_verify.py tests/test_connectivity_verify_endpoint.py -q -p no:cacheprovider` -> `5 passed in 0.47s`
- `python -m pytest tests/test_connectivity_runtime.py tests/test_connectivity_status_endpoint.py tests/test_connectivity_config.py tests/test_connectivity_config_endpoint.py tests/test_connectivity_verify.py tests/test_connectivity_verify_endpoint.py -q -p no:cacheprovider` -> `16 passed in 1.54s`

## Risks Found

1. La verifica `PUBLIC_BASE_URL/health` conferma reachability e proxy, ma non sostituisce ancora
   un test funzionale completo di submit anamnesi pubblica.
2. La verifica non e persistita: dopo refresh pagina il verdetto va rieseguito.
3. La `venv` del repo continua ad avere un launcher locale fragile nella shell di Codex; i test
   sono comunque passati nella venv reale del terminale utente e il debt resta da chiudere
   separatamente.

## Next Smallest Step

`Phase C - Wizard Stepper`

1. trasformare la surface `Connettivita` in percorso step-by-step
2. introdurre gating progressivo tra profili
3. aggiungere guidance esplicita per installazione/login Tailscale e attivazione Funnel
