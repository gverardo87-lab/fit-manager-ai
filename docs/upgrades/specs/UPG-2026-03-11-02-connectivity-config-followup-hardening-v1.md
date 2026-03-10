# Patch Spec - Connectivity Config Follow-up Hardening v1

## Metadata

- Upgrade ID: UPG-2026-03-11-02
- Date: 2026-03-11
- Owner: Codex
- Area: Launch Readiness + Connectivity + Settings
- Priority: medium
- Status: done
- Related spec: `docs/upgrades/specs/UPG-2026-03-11-01-connectivity-config-apply-v1.md`

## Problem

Il primo step write-safe della `Phase B` era corretto sul piano del contratto API, ma lasciava
tre debiti piccoli e reali:

- write diretto del `.env`, con rischio di file parziale se il processo si interrompe nel mezzo;
- assenza di un guardrail esplicito sul fatto che il binary Tailscale deve restare risolto solo
  da path trusted;
- field `Base URL pubblica` sempre visibile nella card `Connettivita`, troppo presto per un
  utente che sta ancora lavorando in `local_only`.

Il rischio non era un bug bloccante, ma un drift verso UX piu opaca e runtime meno difendibile.

## Desired Outcome

Rendere il microstep `connectivity-config` piu robusto senza cambiare il contratto API:

- write del `.env` meno fragile;
- codice piu esplicito sui confini di sicurezza del probe Tailscale;
- UI che mostri la base URL pubblica solo quando l'utente sta davvero preparando il portale.

## Scope

- In scope:
  - write temporanea + `os.replace()` nel writer `.env`;
  - commento guardrail nel runner Tailscale;
  - affinamento UX della card `Connettivita`;
  - test backend aggiuntivo su `.env` mancante;
  - sync docs/gov.

- Out of scope:
  - locking completo cross-request del `.env`;
  - verify end-to-end di Funnel;
  - wizard multi-step;
  - cambio del contratto `ConnectivityConfigResponse`.

## Changes Implemented

### Backend

- In [connectivity_config.py](c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/connectivity_config.py)
  il write del `.env` passa da `write_text()` diretto a file temporaneo + `os.replace()`,
  riducendo il rischio di file parziale/corrotto.
- Aggiunto test focused in
  [test_connectivity_config.py](c:/Users/gvera/Projects/FitManager_AI_Studio/tests/test_connectivity_config.py)
  per il caso `.env` inesistente.
- In [connectivity_runtime.py](c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/connectivity_runtime.py)
  aggiunto commento esplicito: il binary `tailscale` viene risolto solo da fonti trusted
  (`PATH` di sistema + percorsi hardcoded Windows), non da input utente.

### Frontend

- In [ConnectivityStatusSection.tsx](c:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/settings/ConnectivityStatusSection.tsx)
  il blocco `Base URL pubblica` non e piu sempre visibile.
- Nuovo helper UI in
  [connectivity-status-ui.tsx](c:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/settings/connectivity-status-ui.tsx)
  per invitare l'utente a espandere la configurazione del portale pubblico solo quando serve.
- Il componente principale resta sotto il limite progetto (`278` LOC).

## Verification

- Backend lint:
  - `venv\Scripts\ruff.exe check api\services\connectivity_runtime.py api\services\connectivity_config.py tests\test_connectivity_config.py`
- Frontend lint:
  - `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/components/settings/ConnectivityStatusSection.tsx" "src/components/settings/connectivity-status-ui.tsx"`
- Backend runtime:
  - `python -m pytest tests/test_connectivity_runtime.py tests/test_connectivity_status_endpoint.py tests/test_connectivity_config.py tests/test_connectivity_config_endpoint.py -q -p no:cacheprovider`
  - **passed** (`2026-03-11`, eseguito in venv locale reale dall'utente)
- Patch hygiene:
  - `git diff --check`

## Risks / Residual Gaps

- Il write con `os.replace()` riduce il rischio di file troncato, ma non introduce ancora un
  lock completo contro lost update in caso di richieste simultanee.
- La UI e meno confusa, ma non e ancora uno stepper guidato con gating.
- Il verify end-to-end del portale pubblico resta il prossimo microstep corretto.

## Next Smallest Step

`Phase B2 - Guided Verify`

- endpoint `POST /api/system/connectivity-verify`;
- test della reachability del portale pubblico;
- surface UI che distingua esplicitamente tra `configurato` e `verificato`.
