---
name: fitmanager-cash-integrity
description: Use when a change touches cash ledger logic in FitManager. Enforces accounting semantics, balance consistency, audit traceability, and regression checks for financial workflows.
---

# FitManager Cash Integrity

## When To Use

Use this skill if the patch touches:

- `api/routers/movements.py`, `api/routers/rates.py`, recurring expenses flow
- cash dashboard aggregates or balance endpoints
- frontend cassa ledger, audit sheet, or balance visualizations

## Accounting Invariants

- ledger semantics must remain consistent across backend and UI;
- storno semantics must not be misclassified as operational revenue;
- `saldo_attuale` and derived views must remain coherent after each mutation;
- critical financial effects must remain audit-traceable.

## Required Risk Scan

1. idempotency of repeated operations;
2. same-route deep-link state behavior (`/cassa?...`);
3. mismatch risk between aggregates and ledger rows;
4. rollback behavior on partial failure.

## Recommended Checks

- `pytest -q tests/test_cash_audit_log.py`
- `pytest -q tests/test_sync_recurring.py`
- `pytest -q tests/test_soft_delete_integrity.py`
- targeted frontend lint on touched cassa files

If a command is unavailable, state it explicitly and run the closest subset.

## Red Flags

- direct balance edits without ledger evidence
- hidden recalculation logic not reflected in API contracts
- financial UI summarizing data from stale caches
