# UPG-2026-03-03-06 - Cash Protection + Recurring Hardening

## Metadata

- Upgrade ID: UPG-2026-03-03-06
- Date: 2026-03-03
- Owner: Codex
- Area: Cassa / Spese Ricorrenti
- Priority: high
- Target release: test_react

## Problem

Il saldo attuale confonde flusso reale e flusso previsto:
- i movimenti futuri confermati possono impattare subito il saldo mostrato all'utente;
- la conferma spese ricorrenti del mese non protegge abbastanza da conferme premature;
- se una spesa ricorrente viene inserita per errore, la rimozione dal solo catalogo non guida la pulizia del libro mastro.

## Desired Outcome

Il chinesiologo/PT deve vedere chiaramente:
- saldo reale disponibile oggi;
- saldo previsto (includendo movimenti futuri gia' registrati);
- stato di protezione cassa con soglia di sicurezza comprensibile.

Inoltre deve poter:
- eliminare una spesa ricorrente errata e, opzionalmente, rimuovere anche i movimenti gia' registrati;
- confermare spese ricorrenti con UX meno rischiosa rispetto alle date future.

## Scope

- In scope:
  - Distinzione backend saldo reale vs previsto su `GET /movements/balance`.
  - KPI `Protezione Cassa` calcolato da uscite fisse stimate + burn rate variabile.
  - Hardening endpoint delete spesa ricorrente con opzione cleanup movimenti collegati.
  - UX pending banner per selezione predefinita date-dipendente.
  - Type sync frontend + aggiornamento Hero Cassa con reale/previsto.
  - Test backend mirati.
- Out of scope:
  - Fatturazione elettronica.
  - Automazioni reminder/solleciti multicanale.
  - Nuove migrazioni DB (salvo necessarie).

## Impact Map

- Files/modules da toccare:
  - `api/routers/movements.py`
  - `api/routers/recurring_expenses.py`
  - `frontend/src/types/api.ts`
  - `frontend/src/hooks/useRecurringExpenses.ts`
  - `frontend/src/components/movements/RecurringExpensesTab.tsx`
  - `frontend/src/app/(dashboard)/cassa/page.tsx`
  - `tests/test_sync_recurring.py`
- Layer coinvolti: `api`, `frontend`, `tests`
- Invarianti da preservare:
  - Bouncer pattern multi-tenant.
  - Ledger integrity (movimenti contrattuali protetti).
  - Query invalidation simmetrica.
  - Nessun side effect su endpoint read-only non previsto.

## Acceptance Criteria

- Funzionale:
  - `balance` espone saldo reale e saldo previsto distinti.
  - `balance` espone stato protezione cassa con soglia/margine/copertura.
  - delete spesa ricorrente puo' includere cleanup movimenti collegati.
  - conferma pending non ha pre-selezione aggressiva su voci future.
- UX:
  - Cassa mostra reale vs previsto in modo esplicito.
  - Eliminazione spesa errata guida anche la pulizia ledger (opzione chiara).
- Tecnico:
  - Type sync completo in `types/api.ts`.
  - Invalidazioni query corrette per mutate recurring.
  - Test backend aggiornati/verdi sui nuovi casi.

## Test Plan

- Unit/Integration:
  - pytest mirati su `test_sync_recurring.py` (balance reale vs previsto, delete+cleanup).
- Manual checks:
  - conferma spese mese corrente con voci future: selezione default corretta.
  - verifica hero cassa con differenza reale/previsto.
- Build/Lint gates:
  - `bash tools/scripts/check-all.sh`

## Risks and Mitigation

- Rischio 1: regressione semantica su `saldo_attuale`.
- Mitigazione 1: mantenere campo esistente e allineare UI/documentazione al nuovo significato (reale).

- Rischio 2: cleanup movimenti troppo aggressivo su delete recurring.
- Mitigazione 2: opzione esplicita opt-in lato UI/backend (default senza cleanup).

## Rollback Plan

- Revert del commit UPG-2026-03-03-06.
- Ripristino comportamento precedente di balance e delete recurring.

## Notes

- Link commit: _pending_
