# UPG-2026-03-11-15 — CLAUDE Layer Alignment: Connectivity + Launch State

## Context

Dopo il blocco `launch hardening + connectivity setup wizard`, il root `CLAUDE.md` era quasi
allineato, ma `api/CLAUDE.md` e `frontend/CLAUDE.md` descrivevano ancora un perimetro precedente:

- `api/routers/system.py` ridotto al solo support snapshot
- servizi backend connettivita' non elencati
- `frontend/Impostazioni` senza wizard `Connettivita`
- dashboard senza promozione onboarding
- hooks e component tree frontend incompleti rispetto allo stato reale

In parallelo, `docs/upgrades/UPGRADE_LOG.md` e `docs/upgrades/README.md` risultano lockati
da `AGT-2026-03-11-14` su branch diverso; questo microstep quindi aggiorna i `CLAUDE.md`,
crea questa spec e annota il defer nel `WORKBOARD.md`, senza toccare i file lockati.

## Scope

1. Allineare `CLAUDE.md` root allo stato reale `1.0.2` e del workstream connettivita'
2. Allineare `api/CLAUDE.md` ai contratti runtime/system correnti
3. Allineare `frontend/CLAUDE.md` a wizard, onboarding dashboard e hooks connettivita'
4. Tracciare il defer di `UPGRADE_LOG.md` / `README.md` per rispetto del lock parallelo

## Changes

### Root `CLAUDE.md`

- aggiunta una sezione esplicita `Connectivity Setup Wizard — Profili Guidati`
- chiariti i 3 profili `local_only`, `trusted_devices`, `public_portal`
- elencate le fasi chiuse A/B/B2/C/D + promozione dashboard
- collegati i documenti operativi (`TAILSCALE_FUNNEL_SETUP`, `SUPPORT_RUNBOOK`, `RUNTIME_DIAGNOSTICS_PLAYBOOK`)
- aggiornato il blocco architettura/metriche per riflettere hooks/components/router attuali

### `api/CLAUDE.md`

- `routers/system.py` non e piu descritto solo come support snapshot
- `schemas/system.py` aggiornato ai contratti connectivity/runtime
- `services/` aggiornato con:
  - `connectivity_runtime.py`
  - `connectivity_config.py`
  - `connectivity_verify.py`
  - `connectivity_portal_validation.py`

### `frontend/CLAUDE.md`

- `impostazioni/` aggiornato con wizard `Connettivita`
- dashboard aggiornata con `ConnectivityOnboardingCard`
- `components/settings/` aggiornato ai moduli reali del wizard
- `hooks/` aggiornato a `useConnectivityStatus`, `useConnectivityConfig`,
  `useVerifyConnectivity`, `usePortalValidation`
- count/descrizioni frontend riallineati a hooks/components attuali

## Verification

- review manuale `CLAUDE.md`
- review manuale `api/CLAUDE.md`
- review manuale `frontend/CLAUDE.md`
- `rg -n "Connectivity|Connettivita|connectivity_status|connectivity_config|connectivity_verify|connectivity_portal_validation|ConnectivityOnboardingCard|trusted_devices|public_portal|RUNTIME_DIAGNOSTICS_PLAYBOOK|1.0.2" CLAUDE.md api/CLAUDE.md frontend/CLAUDE.md`
- `git diff --check`

## Deferred Sync

Per rispetto del parallelismo attivo:

- `docs/upgrades/UPGRADE_LOG.md` — deferred
- `docs/upgrades/README.md` — deferred

Motivo: lock esplicito in `docs/ai-sync/WORKBOARD.md` da `AGT-2026-03-11-14` su branch `fit_launch_01`.

Follow-up minimo quando il lock si libera:

1. aggiungere una riga `UPG-2026-03-11-15` in `UPGRADE_LOG.md`
2. aggiungere un bullet nell'`Ultimo allineamento` di `README.md`
3. sostituire `_pending_` nel `WORKBOARD.md` con il commit reale
