# UPG-2026-03-09-17 - Workspace Readiness Maintenance Degradation v1

## Context

Real validation on `crm_dev.db` showed that `Oggi` was still too heavy even after temporal ordering and viewport-budget fixes.

The main overload source was no longer `todo_manual`, but `onboarding_readiness`:

- `30` readiness worklist items
- all `30` with `anamnesi_state = legacy`
- all `30` with `timeline_status = today`
- `27` onboarding cases visible in `workspace=today` before the patch

The dominant pattern was not true onboarding, but legacy anamnesi maintenance on already operational clients:

- `24` clients had `legacy + measurements present + workout plan present`
- only `6` clients still had missing baseline and missing workout, so they were real onboarding blockers

## Problem

`Oggi` treated all legacy anamnesi items as same-day operational work.

This was mathematically wrong for the workspace:

- a client with `legacy anamnesi + baseline present + workout present` is not blocked
- that case is maintenance backlog, not daily urgency
- promoting all such cases to `today` flattened the queue and made `Oggi` less useful than the dashboard

## Decision

Introduce a workspace-local degradation rule for readiness maintenance cases.

Rule:

`maintenance_only_readiness =`

- `anamnesi_state == legacy`
- `has_measurements == true`
- `has_workout_plan == true`
- `missing_steps == ["anamnesi_legacy"]`

Behavior in workspace runtime:

- degrade bucket from `today` to `waiting`
- degrade severity to `low`
- rename title from `Onboarding da completare: ...` to `Anamnesi da rivedere: ...`

Important scope boundary:

- no change to shared clinical readiness computation
- no change to dashboard readiness worklist
- no new case kind
- no new endpoint

The rule only changes how the workspace interprets readiness for `Oggi` and `Onboarding`.

## Implementation

Touched runtime:

- `api/services/workspace_engine.py`
- `tests/test_workspace_today.py`

New workspace helpers:

- `_is_readiness_maintenance_only(item)`
- `_readiness_case_title(item, client_label)`

Behavior changes:

1. `_readiness_bucket()` now returns `waiting` for maintenance-only readiness.
2. `_readiness_severity()` now returns `low` for maintenance-only readiness.
3. readiness case titles reflect maintenance semantics instead of onboarding semantics.

## Verification

### Static

- `venv\Scripts\ruff.exe check api\services\workspace_engine.py tests\test_workspace_today.py`

Result: `PASS`

### Runtime on real DEV dataset (`crm_dev.db`)

Verified through the running backend on `http://localhost:8001`:

- `workspace=today` onboarding cases dropped from `27` to `6`
- `workspace=onboarding` still exposes `30` readiness cases total
- those same readiness cases are now split as:
  - `6 today`
  - `24 waiting`

This confirms the removed cases were not lost, only reclassified into the correct workspace urgency layer.

## Risks

- `dashboard/clinical-readiness` still labels legacy anamnesi as `today`, by design
- this is acceptable for now because the dashboard worklist is a diagnostic/readiness surface, not the operative `Oggi` queue
- if dashboard and workspace must converge later, the next step should be an explicit shared `readiness_operational_tier` field instead of overloading `timeline_status`

## Next Smallest Step

Do not add new signals yet.

The next mathematically correct step is to apply the same discipline to the remaining `6` onboarding cases in `today`:

- distinguish true same-day blockers from generic incomplete onboarding
- consider session proximity or explicit start pressure before keeping them in `today`
