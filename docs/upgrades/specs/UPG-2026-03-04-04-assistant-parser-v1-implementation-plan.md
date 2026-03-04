# UPG-2026-03-04-04 - Assistant Implementation Plan (Methodical)

## Metadata

- Upgrade ID: UPG-2026-03-04-04
- Date: 2026-03-04
- Owner: Codex
- Area: Delivery Plan
- Priority: high
- Target release: test_react

## Objective

Eseguire implementazione Assistant V1 in fasi piccole, verificabili e reversibili, mantenendo stabilita' dei moduli esistenti.

## Work Breakdown Structure

### Milestone 1 - Backend Skeleton

- creare `api/schemas/assistant.py` con request/response parse/commit;
- creare `api/routers/assistant.py` con endpoint placeholder;
- includere router in `api/main.py`;
- aggiungere feature flag backend.

Done criteria:

- endpoint rispondono con schema valido;
- nessuna regressione test esistenti.

### Milestone 2 - Parser Core (Read-only)

- creare package `api/services/assistant_parser/`:
  - `normalizer.py`
  - `intent_classifier.py`
  - `entity_extractor.py`
  - `entity_resolver.py`
  - `confidence.py`
  - `orchestrator.py`
- implementare parse per 3 intent pilota:
  - `agenda.create_event`
  - `movement.create_manual`
  - `measurement.create`

Done criteria:

- parse produce `operations[]` coerente;
- unit tests parser pass.

### Milestone 3 - Commit Engine

- implementare dispatch commit verso endpoint dominio interni/service layer;
- garantire validazione payload per dominio;
- implementare result per-item con `operation_id`.

Done criteria:

- commit per 3 intent pilota pass in integration tests;
- side effects corretti su DB di test.

### Milestone 4 - Frontend Integration (Phase 1)

- integrare chiamata parse in `CommandPalette.tsx`;
- render preview card e stati parse;
- gestione `Invio` -> commit;
- invalidazione query minima per 3 intent pilota.

Done criteria:

- UX keyboard-only funzionante;
- no regressioni in apertura/navigazione palette.

### Milestone 5 - Domain Expansion V1

- estendere parser + commit ai restanti intent:
  - `agenda.update_event_status`
  - `client.create`
  - `client.update`
  - `contract.create`
  - `anamnesi.patch`
  - `workout_log.create`
- completare matrice invalidazione query.

Done criteria:

- integration tests per tutti intent V1 pass;
- manual QA checklist completa.

### Milestone 6 - Rollout Controls

- telemetry minima;
- feature flag FE/BE;
- shadow mode parse-only;
- runbook rollback.

Done criteria:

- osservabilita' base attiva;
- rollout pilot pronto.

## Branching and Commits

- branch working: `test_react` (o branch feature dedicata da concordare).
- regola: 1 milestone = 1 o piu' commit atomici + note test.
- aggiornare `docs/upgrades/UPGRADE_LOG.md` a ogni milestone.

## Test Order per Milestone

1. unit parser (se toccato parser);
2. integration assistant;
3. regression test critici esistenti (agenda/cassa/rate);
4. frontend lint/typecheck file modificati.

## Definition of Done (Overall)

- tutte le specifiche V1 rispettate;
- test nuovi + regressivi verdi;
- feature flag attiva/disattiva senza effetti collaterali;
- documentazione allineata a implementazione reale;
- upgrade log aggiornato a `done` con commit references.
