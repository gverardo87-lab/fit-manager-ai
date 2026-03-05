# UPG-2026-03-05-24 - Pay Rate Test Date Determinism

## Metadata

- Upgrade ID: UPG-2026-03-05-24
- Date: 2026-03-05
- Owner: Codex
- Area: Backend Tests (Rates/Cash)
- Priority: low
- Target release: codex_02

## Problem

`tests/test_pay_rate.py::test_pay_rate_creates_cash_movement` filtered movements on `anno=2026&mese=2`
but did not pass `data_pagamento` in the payment payload.
Since `RatePayment.data_pagamento` defaults to `date.today()`, the test could fail depending on execution date.

## Desired Outcome

Make the payment movement test deterministic across calendar dates and CI runs.

## Scope

- In scope:
  - set explicit `data_pagamento` in `test_pay_rate_creates_cash_movement`.
  - run targeted backend verification on `tests/test_pay_rate.py`.
- Out of scope:
  - any runtime API behavior change for `/rates/{id}/pay`.
  - schema/router/business logic changes for rates or movements.

## Impact Map

- Files/modules touched:
  - `tests/test_pay_rate.py`
  - `docs/upgrades/specs/UPG-2026-03-05-24-pay-rate-test-date-determinism.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `tests` + `docs`
- Invarianti da preservare:
  - atomicita `pay_rate` invariata;
  - Deep Relational IDOR invariato;
  - ledger/audit runtime invariati.

## Acceptance Criteria

- Functional:
  - `test_pay_rate_creates_cash_movement` passes independently from current date.
- Technical:
  - targeted test passes;
  - full `tests/test_pay_rate.py` passes.

## Test Plan

- `venv\Scripts\python.exe -m pytest -q tests/test_pay_rate.py::test_pay_rate_creates_cash_movement`
- `venv\Scripts\python.exe -m pytest -q tests/test_pay_rate.py`

## Risks and Mitigation

- Risk 1: hidden date-sensitive tests may still exist in other files.
- Mitigation 1: continue launch-hardening microsteps on failing/flaky tests in CI order.

## Rollback Plan

- Revert the single test payload line adding `data_pagamento` if this microstep must be undone.
