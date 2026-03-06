# UPG-2026-03-06-28 - Dashboard Todo Hero "Next Best Action"

## Metadata

- Upgrade ID: UPG-2026-03-06-28
- Date: 2026-03-06
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: codex_02

## Problem

Con il reminder-first del microstep precedente, i promemoria sono visibili subito ma mancava una
guida operativa primaria: l'utente vede la lista, ma non ha sempre chiaro il "prossimo click migliore".

## Desired Outcome

Trasformare la card promemoria in un blocco decisionale: una sola azione consigliata, prioritaria e
contestuale ai segnali reali della giornata (todo, alert, agenda).

## Scope

- In scope:
  - introduzione hero "Azione consigliata" dentro `TodoCard`;
  - priorita deterministica cross-signal:
    - todo scaduti
    - todo in scadenza oggi
    - alert critici
    - alert warning
    - sessioni imminenti in agenda
    - fallback "giornata libera";
  - CTA contestuali dirette:
    - completa prossimo todo urgente
    - apri alert panel
    - apri agenda
    - crea follow-up rapido;
  - passaggio contatori operativi da dashboard page a `TodoCard` senza modifiche API.
- Out of scope:
  - nuove query backend;
  - persistenza preferenze utente su priorita/hero;
  - redesign completo di tutta la dashboard.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `frontend/src/components/dashboard/TodoCard.tsx`
  - `docs/upgrades/specs/UPG-2026-03-06-28-dashboard-todo-hero-next-best-action.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - dashboard resta privacy-safe (nessun dato finanziario reintrodotto);
  - API contract invariato (`useTodos`, dashboard alerts/summary/events);
  - loading/empty states preservati.

## Acceptance Criteria

- Functional:
  - la card promemoria mostra sempre una "Azione consigliata" primaria;
  - CTA primaria e' coerente con la priorita corrente;
  - se presenti alert, esiste accesso rapido al pannello alert;
  - lista todo resta ordinata per urgenza.
- Technical:
  - nessun uso di funzioni impure in render (`Date.now`) nei nuovi path;
  - lint pulito sui file frontend toccati.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx" "src/components/dashboard/TodoCard.tsx"`
- Manual:
  - verifica scenario con todo scaduti -> CTA "Completa prossimo";
  - verifica scenario senza todo urgenti ma con alert critici -> CTA "Apri alert";
  - verifica scenario pulito con sessioni in programma -> CTA "Apri agenda";
  - verifica scenario vuoto -> CTA "Aggiungi follow-up".

## Risks and Mitigation

- Risk 1: CTA "follow-up rapido" puo generare task duplicati se cliccata ripetutamente.
- Mitigation 1: mutation gia serializzata con stato pending e feedback toast; eventuale dedup in microstep successivo.
- Risk 2: priorita cross-signal percepita come troppo rigida per alcuni utenti.
- Mitigation 2: logica esplicita e deterministica, pronta a futura personalizzazione senza magia.

## Rollback Plan

- Revert dei file frontend di questo microstep:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `frontend/src/components/dashboard/TodoCard.tsx`
