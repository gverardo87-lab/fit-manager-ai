# Patch Spec - Multi-Agent Alignment Protocol

## Metadata

- Upgrade ID: UPG-2026-03-03-05
- Date: 2026-03-03
- Owner: gvera + codex
- Area: Process / Governance
- Priority: medium
- Target release: 2026-03-03 (`codex_01`)
- Status: in_progress

## Problem

Con piu agenti AI in parallelo (Codex + Claude Code) manca una fonte operativa unica
per claim task, lock file, handoff e stato lavori.
Questo aumenta il rischio di sovrapposizioni e regressioni.

## Desired Outcome

Definire un protocollo condiviso e un workboard unico, referenziati sia da `codex.md` che da `CLAUDE.md`.

## Scope

- In scope:
  - creazione protocollo `docs/ai-sync/MULTI_AGENT_SYNC.md`
  - creazione board `docs/ai-sync/WORKBOARD.md`
  - integrazione riferimenti in `codex.md` e `CLAUDE.md`
  - allineamento upgrade log
- Out of scope:
  - automazioni CI del workboard
  - lock tecnici via tooling (solo soft lock documentale)

## Impact Map

- Files/modules da toccare:
  - `codex.md`
  - `CLAUDE.md`
  - `docs/ai-sync/MULTI_AGENT_SYNC.md`
  - `docs/ai-sync/WORKBOARD.md`
  - `docs/upgrades/UPGRADE_LOG.md`
- Layer coinvolti: `docs/process`
- Invarianti da preservare:
  - precedenza regole esistenti in `CLAUDE.md`
  - workflow tecnico (build/test/DoD) invariato

## Acceptance Criteria

- Funzionale:
  - esiste un protocollo unico multi-agente con regole di claim/lock/handoff.
  - esiste un workboard operativo con tabella active/completed.
  - `codex.md` e `CLAUDE.md` referenziano il protocollo.
- Tecnico:
  - documenti coerenti e senza conflitti con regole esistenti.

## Test Plan

- Manual checks:
  - aprire `codex.md` e verificare riferimento al protocollo.
  - aprire `CLAUDE.md` e verificare sezione coordinamento multi-agente.
  - aprire `docs/ai-sync/WORKBOARD.md` e verificare template operativo.

## Risks and Mitigation

- Rischio 1: processo percepito come overhead.
  - Mitigazione: protocollo snello, focus solo su lock/handoff essenziali.

## Rollback Plan

- Rimuovere la cartella `docs/ai-sync/` e i riferimenti in `codex.md`/`CLAUDE.md`.

## Notes

- Obiettivo: ridurre conflitti di sviluppo parallelo mantenendo velocita.
