# UPG-2026-03-06-29 - Dashboard Operational Density Layout

## Metadata

- Upgrade ID: UPG-2026-03-06-29
- Date: 2026-03-06
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: codex_02

## Problem

La dashboard aveva ancora ridondanza visiva e operativa:

- barra "Focus operativo" duplicata rispetto alla nuova Hero Promemoria;
- KPI duplicati (`Sessioni Imminenti`, `Alert Operativi`);
- orologio live e agenda del giorno separati in due card distinte;
- densita operativa non ottimale nel primo viewport.

## Desired Outcome

Concentrare il primo viewport in una dashboard operativa ad alta densita:

- KPI essenziali senza ridondanza;
- layout 50/50 con promemoria a sinistra e operativita giornata a destra;
- un unico pannello destro con orologio live, stato operativo e sedute scrollabili.

## Scope

- In scope:
  - rimozione `ActionFocusBar`;
  - riduzione KPI a due card (`Clienti Attivi`, `Appuntamenti Oggi`);
  - riorganizzazione layout top in due meta larghezza (`xl:grid-cols-2`);
  - unificazione di live clock + sedute in `TodayAgenda` (card unica);
  - aggiornamento estetico `TodoCard` in stile post-it (sinistra).
- Out of scope:
  - nuove API/query backend;
  - cambi business logic su alert/todo/events;
  - redesign di pagine non dashboard.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `frontend/src/components/dashboard/TodoCard.tsx`
  - `docs/upgrades/specs/UPG-2026-03-06-29-dashboard-operational-density-layout.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - dashboard resta privacy-safe (no KPI finanziari);
  - flow update stato eventi inline preservato;
  - hook/api contracts invariati.

## Acceptance Criteria

- Functional:
  - barra focus operativo non visibile;
  - KPI visualizzati: solo 2 card operative;
  - promemoria a sinistra in card post-it;
  - card destra unica con ora live, stato e sedute scrollabili.
- Technical:
  - nessun errore lint nei file frontend toccati.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx" "src/components/dashboard/TodoCard.tsx"`
- Manual:
  - verifica densita e ordine blocchi a 390px, 768px, 1024px;
  - verifica aggiornamento countdown live e stato operativo;
  - verifica scroll interno sedute in presenza di lista lunga.

## Risks and Mitigation

- Risk 1: maggiore densita nel pannello destro puo aumentare carico cognitivo iniziale.
- Mitigation 1: gerarchia tipografica e micro-copy orientata a "azione adesso".
- Risk 2: estensione layout può richiedere ulteriore taratura su viewport piccoli.
- Mitigation 2: prossimo microstep dedicato a rifiniture responsive 390/768.

## Rollback Plan

- Revert dei due file frontend:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `frontend/src/components/dashboard/TodoCard.tsx`
