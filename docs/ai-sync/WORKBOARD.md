# Multi-Agent Workboard

Tabella operativa condivisa tra agenti AI.
Aggiornare prima di iniziare e alla chiusura di ogni task.

## Active

| Work ID | Owner | Branch | Scope | Locked files | Status | Started (UTC) | Updated (UTC) | Handoff / Notes |
|---|---|---|---|---|---|---|---|---|
| AGT-2026-03-03-06 | Codex | `codex_01` | Protezione Cassa + fix flusso spese fisse (reale vs previsto) | `api/routers/movements.py`, `api/routers/recurring_expenses.py`, `frontend/src/app/(dashboard)/cassa/page.tsx`, `frontend/src/components/movements/RecurringExpensesTab.tsx`, `frontend/src/hooks/useRecurringExpenses.ts`, `frontend/src/types/api.ts`, `tests/test_sync_recurring.py` | in_progress | 2026-03-03 08:16 | 2026-03-03 08:16 | Step 1 cashflow hardening: saldo reale/proiettato, cleanup spese fisse, UX conferma per data |

## Completed

| Work ID | Owner | Branch | Scope | Commit | Checks | Closed (UTC) | Notes |
|---|---|---|---|---|---|---|---|
| AGT-2026-03-03-08 | Claude Code | `codex_01` | Riallineamento Safety Engine — 80 pattern rules, 0 condizioni morte, severity avoid>modify>caution | `43e5010` | check-all.sh green, verify_qa_clinical 150 PASS 0 FAIL | 2026-03-03 | populate_conditions.py + safety_engine.py + RiskBodyMap.tsx + seed/verify QA |

## Quick rules

1. `Locked files` deve riflettere i file realmente in editing.
2. Se la task si blocca, usare stato `blocked` + nota chiara.
3. Alla chiusura, spostare la riga da `Active` a `Completed`.
