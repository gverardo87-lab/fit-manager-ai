# UPG-2026-03-09-18 - Workspace Readiness Operational Pressure v1

## Context

After `UPG-2026-03-09-17`, the major readiness overload in `Oggi` was reduced, but the remaining onboarding cases still needed stricter discipline.

The remaining `today` cases followed a uniform pattern:

- `anamnesi_legacy`
- missing baseline
- missing workout
- no same-day session absorption

On real `crm_dev.db` inspection, these clients were not necessarily active-day priorities. They were mostly historical backlog, not true daily blockers.

## Problem

The workspace was still promoting incomplete onboarding to `today` based only on readiness incompleteness.

That is not sufficient for `Oggi`.

`Oggi` should show readiness only when there is measurable operational pressure, not just a missing state in the CRM.

## Decision

Introduce a workspace-local operational pressure rule for onboarding readiness.

`onboarding_readiness` stays in `today` only when at least one of these is true:

1. the client has an event scheduled within the next 7 days
2. the client has a recent active contract

Otherwise, the case degrades to `waiting`.

Important scope:

- no change to shared `clinical_readiness` service
- no change to dashboard clinical worklist
- no new case kind
- no new endpoint

This is a workspace-only triage rule for `Oggi` and `Onboarding`.

## Runtime Rule

### Upcoming event pressure

Client is considered pressured if:

- has at least one non-cancelled event
- with `data_inizio >= reference_dt`
- and `data_inizio <= reference_dt + 7 days`

### Recent contract pressure

Client is considered pressured if it has an active contract where:

- `chiuso == false`
- and `data_inizio >= reference_date - 7 days`
- fallback: if `data_inizio` is null, use `data_vendita`

### Bucket rule

If a readiness case:

- is not already absorbed by a same-day session case
- is not `maintenance_only`
- has base bucket `today`
- and has no operational pressure

then:

- bucket becomes `waiting`

Severity stays unchanged for these incomplete onboarding cases, because they are still important in the dedicated onboarding workspace.

## Implementation

Touched files:

- `api/services/workspace_engine.py`
- `tests/test_workspace_today.py`

New helpers:

- `_recent_readiness_contract_client_ids()`
- `_upcoming_readiness_event_client_ids()`

`_build_readiness_cases()` now computes `operational_pressure_client_ids` and degrades stale, pressure-free onboarding out of `today`.

## Verification

### Static

- `venv\Scripts\ruff.exe check api\services\workspace_engine.py tests\test_workspace_today.py`

Result: `PASS`

### Test coverage added

Added deterministic tests for:

- stale incomplete onboarding -> excluded from `workspace=today`
- incomplete onboarding with recent active contract -> still visible in `workspace=today`
- previously shipped maintenance-only legacy case -> still degraded correctly

### Environment limitation

Backend `pytest` is still blocked by the broken local `venv` launcher, which resolves to the Microsoft Store Python path instead of a real interpreter.

The running DEV backend on port `8001` also did not hot-reload this pass during validation, so live HTTP still reflected the previous step.

## Risks

- this rule relies on contract dates being reasonably populated (`data_inizio` or `data_vendita`)
- if seeded/imported datasets omit both fields, only upcoming-event pressure applies
- if future real workflows require stronger pre-session activation, the next pressure source can be explicit contract-start reminders rather than generic client recency

## Next Smallest Step

If `Oggi` still feels too passive after this pass, the next mathematically correct step is:

- add contract-start pressure as a third readiness pressure source

Only do that after observing real data again.
