# Patch Spec - Connectivity Wizard Stepper v1

## Metadata

- Upgrade ID: UPG-2026-03-11-04
- Date: 2026-03-11
- Owner: Codex
- Area: Launch Readiness + Connectivity + Settings
- Priority: high
- Status: done

## Goal

Chiudere il primo vero passo UX del `Connectivity Setup Wizard` senza ancora introdurre
un first-run globale: la card `Connettivita` in `Impostazioni` deve diventare un percorso
guidato, con gating esplicito sui prerequisiti gia disponibili (`status`, `apply`,
`verify`).

## Scope

- In scope:
  - nuovo componente `ConnectivitySetupWizard`
  - state machine frontend pura per gli step del wizard
  - stepper visivo con stati `complete | current | upcoming`
  - pannelli guidati per:
    - scelta profilo
    - preparazione Tailscale
    - apply config FitManager
    - attivazione Funnel
    - verifica finale
  - test Vitest focused sulla logica di gating
  - sync docs/workboard

- Out of scope:
  - first-run onboarding globale
  - nuove API backend
  - test funzionale completo del link anamnesi pubblico

## Impact Map

- Frontend:
  - `frontend/src/components/settings/ConnectivityStatusSection.tsx`
  - `frontend/src/components/settings/ConnectivitySetupWizard.tsx`
  - `frontend/src/components/settings/connectivity-wizard-state.ts`
  - `frontend/src/components/settings/connectivity-wizard-ui.tsx`
  - `frontend/src/components/settings/connectivity-wizard-panels.tsx`
  - `frontend/src/__tests__/settings/connectivity-wizard-state.test.ts`

- Docs:
  - `docs/upgrades/specs/UPG-2026-03-10-20-connectivity-setup-wizard-plan-v1.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`

## Design Decision

Il wizard non diventa una seconda fonte di verita.

La sorgente di stato resta:

1. `GET /api/system/connectivity-status`
2. `POST /api/system/connectivity-config`
3. `POST /api/system/connectivity-verify`

Il frontend aggiunge solo orchestrazione guidata:

- sceglie il profilo target
- calcola lo step corrente con una state machine pura
- mostra una sola CTA principale per volta
- mantiene comunque accessibile il fallback `Solo locale`

## Delivered

- `ConnectivityStatusSection` torna a fare orchestration e non contiene piu l'intero
  flusso `apply + verify`.
- Nuovo `ConnectivitySetupWizard` con:
  - selezione profilo
  - stepper a 5 step
  - pannello corrente contestuale
  - stato finale positivo quando il percorso e verificato
- Nuovo helper puro `buildConnectivityWizardState(...)` per determinare:
  - step richiesti
  - step corrente
  - completamento complessivo
- Nuovi pannelli UI separati per mantenere i file sotto i limiti progetto.

## Verification

- `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/components/settings/ConnectivityStatusSection.tsx" "src/components/settings/ConnectivitySetupWizard.tsx" "src/components/settings/connectivity-wizard-ui.tsx" "src/components/settings/connectivity-wizard-panels.tsx" "src/components/settings/connectivity-wizard-state.ts" "src/__tests__/settings/connectivity-wizard-state.test.ts"`
- `& 'C:\Program Files\nodejs\npm.cmd' exec -- vitest run src/__tests__/settings/connectivity-wizard-state.test.ts --pool=threads` (workdir `frontend`) -> `5 passed`
- `git diff --check`

## Residual Risks

- Il wizard vive ancora solo dentro `Impostazioni`; non e ancora agganciato al first-run
  post-installazione.
- La verifica finale conferma `PUBLIC_BASE_URL` e reachability dell'origine pubblica, ma
  non sostituisce ancora un test funzionale guidato del link anamnesi pubblico.
- La scelta profilo e guidata lato UX, ma non impedisce all'utente di fermarsi a meta
  percorso: serve ancora una `Phase D` per onboarding piu prescrittivo.

## Next Smallest Step

`Phase D - Portal Validation`

- guidare un test funzionale del link anamnesi pubblico
- esplicitare l'esito finale come "portale pronto / non pronto"
- poi valutare l'integrazione first-run del wizard
