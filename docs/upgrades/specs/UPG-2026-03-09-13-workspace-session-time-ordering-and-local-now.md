# UPG-2026-03-09-13 - Workspace session time ordering and local-now alignment

## Context

`Oggi` had a credibility bug on real `crm_dev.db` data: session cases on the same day were ordered alphabetically by title instead of by actual start time. The root cause was that `OperationalCase` only carried `due_date`, while `session_imminent` sorting needed the full event datetime.

In the same path, the workspace snapshot still used `datetime.utcnow()` even though the CRM stores agenda datetimes as local naive values. That made the operational day boundary (`Adesso` vs `Oggi`) inconsistent with the rest of the product.

## Objective

Fix only the temporal trust issues of `Oggi` without expanding the workspace surface:

1. preserve the existing case model and API family;
2. make session ordering follow real event time;
3. align workspace "now" with the local-naive datetime convention already used by agenda.

## Microstep

### Backend contract

- Added `due_at` to `OperationalCase`.
- `session_imminent` now sets `due_at=event.data_inizio`.
- No new endpoint, no new case kinds, no frontend behavior expansion.

### Workspace engine

- Replaced `_now_utc()` with local-naive `_now_local()`.
- Introduced `_case_due_moment()` to derive the real sortable datetime for a case.
- Updated priority sort:
  - `session_imminent` now sorts by `bucket -> due_at -> severity -> title`;
  - other cases keep the existing priority-first behavior, but use `due_at` when available.
- Updated `sort_by=due_date` list sorting to honor `due_at` as tie-breaker / primary moment when present.

### Tests

- Added a targeted backend test proving that three PT sessions on the same day are returned in chronological order (`10:00 -> 11:00 -> 16:00`) instead of alphabetically.
- Updated test event helper to use local-naive `datetime.now()` semantics, matching the runtime convention.

## Verification

- `venv\Scripts\ruff.exe check api\schemas\workspace.py api\services\workspace_engine.py tests\test_workspace_today.py`
- `C:\Program Files\nodejs\npm.cmd --prefix frontend run lint -- "src/types/api.ts"`
- `venv\Scripts\python.exe -m pytest -q tests\test_workspace_today.py -p no:cacheprovider`
  - expected local outcome: blocked by the broken project `venv` launcher already known in this repo

## Residual risks

- `Oggi` still duplicates some temporal context between agenda strip and stack; this microstep only restores correct trust in ordering.
- The workspace remains local-time aligned by server machine clock. That is correct for the current local-first desktop model, but would need an explicit timezone strategy if a remote multi-timezone deployment is introduced later.

## Next smallest step

Move the viewport budget (`2 now / 4 today`) from the frontend shell into the workspace engine, so the API itself decides the visible operational slice and the UI stops owning selection policy.
