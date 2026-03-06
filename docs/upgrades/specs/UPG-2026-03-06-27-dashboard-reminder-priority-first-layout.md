# UPG-2026-03-06-27 - Dashboard Reminder-First Layout + Priority Todo Hardening

## Metadata

- Upgrade ID: UPG-2026-03-06-27
- Date: 2026-03-06
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: codex_02

## Problem

La dashboard risultava ancora poco utile nei primi secondi di scansione operativa:

- i promemoria erano troppo in basso nel flusso mobile/tablet;
- la lista todo non esplicitava la priorita giornaliera;
- il calcolo "oggi/scaduto" in `TodoCard` usava `toISOString()` (UTC), con rischio mismatch locale.

## Desired Outcome

Rendere i promemoria una superficie operativa primaria e chiarire subito le priorita della giornata
per il chinesiologo/PT, senza cambiare logica backend.

## Scope

- In scope:
  - board reordering: colonna promemoria/alert mostrata prima su mobile/tablet;
  - promemoria sopra gli alert nella colonna destra;
  - `TodoCard` con ordinamento per bucket di priorita (scaduti, oggi, prossimi, senza data, completati);
  - contatori rapidi di priorita (`Scaduti`, `Oggi`, `Prossimi`);
  - hardening data locale in `TodoCard` (`YYYY-MM-DD` locale, no UTC shift).
- Out of scope:
  - cambi API/backend;
  - redesign completo tipografico/cromatico della dashboard;
  - nuove query o nuove entita dati.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `frontend/src/components/dashboard/TodoCard.tsx`
  - `docs/upgrades/specs/UPG-2026-03-06-27-dashboard-reminder-priority-first-layout.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - dashboard resta privacy-safe (nessun KPI economico esposto);
  - hook/api todo invariati (`useTodos`, CRUD, invalidazioni);
  - loading/error/empty state preservati.

## Acceptance Criteria

- Functional:
  - su mobile/tablet la board promemoria/alert viene renderizzata prima della board agenda/settimana;
  - nella colonna destra `Promemoria` appare sopra `Alert operativi`;
  - i todo risultano ordinati per urgenza operativa;
  - i contatori `Scaduti/Oggi/Prossimi` riflettono i todo attivi.
- Technical:
  - niente uso di `toISOString().slice(0, 10)` nel `TodoCard` per la logica di urgenza;
  - lint pulito sui file frontend toccati.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx" "src/components/dashboard/TodoCard.tsx"`
- Manual:
  - verifica ordine board a 390px, 768px, 1024px;
  - verifica evidenza promemoria nel primo viewport;
  - verifica bucket urgenza con combinazione di todo scaduti/oggi/futuri/completati.

## Risks and Mitigation

- Risk 1: reordering mobile/tablet puo cambiare abitudini di scansione utente.
- Mitigation 1: cambiamento limitato a priorita operativa (promemoria/alert), senza alterare i flussi di modifica dati.
- Risk 2: bucket "senza data" percepito meno urgente di "prossimi".
- Mitigation 2: bucket separato ma visivamente neutro, mantenendo scaduti/oggi in testa.

## Rollback Plan

- Revert dei file dashboard/todo se emergono regressioni di usabilita:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `frontend/src/components/dashboard/TodoCard.tsx`
