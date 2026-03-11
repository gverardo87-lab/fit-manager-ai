# Patch Spec - Upgrade Procedure Guide v1

## Metadata

- Upgrade ID: UPG-2026-03-11-06
- Date: 2026-03-11
- Owner: Codex
- Area: Documentation + Launch Readiness + Upgrade UX
- Priority: medium
- Target release: `1.0.0` post-RC supportability

## Problem

Il repository aveva gia un runbook tecnico di supporto e recovery, ma mancava una procedura
utente separata, leggibile e sequenziale per l'aggiornamento del prodotto sul PC del trainer.

Il rischio pratico era chiaro:
- confondere upgrade in-place con reinstallazione distruttiva;
- fare restore inutili;
- toccare manualmente i file DB;
- perdere la `license.key` prima dell'upgrade.

## Desired Outcome

Avere un documento dedicato che spieghi:

- quale strategia usare per l'upgrade (`upgrade in-place` come default);
- cosa mettere in sicurezza prima dell'update;
- quando fare restore e quando non farlo;
- cosa fare se la licenza non viene rilevata;
- come verificare che l'upgrade sia davvero riuscito.

Il documento deve essere abbastanza chiaro da poter diventare base futura della guida utente.

## Scope

- In scope:
  - nuovo documento dedicato `docs/UPGRADE_PROCEDURE.md`
  - collegamento dal runbook tecnico
  - sync di spec, log, README e workboard

- Out of scope:
  - nuove API o nuove feature runtime
  - modifiche all'installer
  - wizard in-app per upgrade automatico

## Impact Map

- Files/modules da toccare:
  - `docs/UPGRADE_PROCEDURE.md`
  - `docs/SUPPORT_RUNBOOK.md`
  - `docs/upgrades/specs/UPG-2026-03-11-06-upgrade-procedure-guide-v1.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `docs`
- Invarianti da preservare:
  - nessuna istruzione che suggerisca overwrite manuale del DB
  - nessuna contraddizione con `SUPPORT_RUNBOOK.md`
  - nessuna contraddizione con il contratto reale dell'installer che preserva `data/`

## Acceptance Criteria

- Funzionale:
  - esiste una procedura completa e leggibile di upgrade
  - la procedura distingue chiaramente tra upgrade standard e fallback reinstallazione
  - la procedura spiega in modo esplicito quando usare il restore

- UX:
  - checklist iniziale e checklist finale presenti
  - linguaggio leggibile da utente non tecnico avanzato
  - struttura lineare e concreta

- Tecnico:
  - allineamento con `installer/fitmanager.iss`
  - allineamento con `docs/SUPPORT_RUNBOOK.md`
  - sync completo su spec/log/workboard

## Test Plan

- Manual checks:
  - review di coerenza con `installer/fitmanager.iss`
  - review di coerenza con `docs/SUPPORT_RUNBOOK.md`
  - `git diff --check`

- Build/Lint gates:
  - non applicabili, microstep docs-only

## Risks and Mitigation

- Rischio 1:
  - la guida utente diverge dal runbook tecnico
- Mitigazione 1:
  - collegamento esplicito dal runbook e review di coerenza sui punti critici

- Rischio 2:
  - il documento suggerisce un reinstall-first troppo aggressivo
- Mitigazione 2:
  - rendere l'upgrade in-place la strategia standard e il reinstall solo fallback

## Rollback Plan

- Se la guida risultasse confusiva o in conflitto:
  - rimuovere il nuovo documento
  - mantenere il solo `SUPPORT_RUNBOOK.md` come fonte operativa

## Notes

- Questo step e' docs-only e prepara il terreno per una futura integrazione nella guida utente.
