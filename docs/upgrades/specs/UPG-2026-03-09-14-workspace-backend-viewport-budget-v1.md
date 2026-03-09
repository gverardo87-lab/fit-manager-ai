# UPG-2026-03-09-14 - Workspace backend viewport budget v1

## Context

After the first dominance pass, `Oggi` still owned an important part of the selection logic: the page fetched the full `/api/workspace/cases` list and then sliced it client-side (`2 now / 4 today`).

That meant the visible operational stack was still not a strict function of the workspace engine. The backend decided priorities, but the frontend still decided how many items "deserved" the viewport.

## Objective

Move the viewport budget into the workspace engine so that:

1. `GET /api/workspace/today` becomes the canonical source for the visible stack;
2. `GET /api/workspace/cases` remains the full list surface for exhaustive browsing;
3. the page no longer applies its own slicing policy.

## Microstep

### Backend

- Added deterministic viewport limits in the workspace engine:
  - `now -> 2`
  - `today -> 4`
- Implemented `_apply_today_viewport_budget()`:
  - works on already ranked cases;
  - preserves section totals;
  - limits only the visible `items` returned by `WorkspaceTodaySection`;
  - uses a stable root-entity identity guard to avoid duplicating the same exact root above the fold if it appears twice.
- `focus_case` is now the first **visible** case after budgeting, not just the first raw case from the pre-budget snapshot.

### Frontend

- `/oggi` no longer fetches `/api/workspace/cases` to build the main stack.
- The page now renders directly from `today.sections`, which are already budgeted by the backend.
- Queue section counters still show the full `total`, while the copy makes it explicit when only the first subset is shown.

### Tests

- Added a targeted backend test proving:
  - `GET /today` truncates the visible `today` section to 4 items;
  - the full case list surface still exposes all 5 items through `build_workspace_case_list()`.

## Verification

- `venv\Scripts\ruff.exe check api\services\workspace_engine.py tests\test_workspace_today.py`
- `C:\Program Files\nodejs\npm.cmd --prefix frontend run lint -- "src/app/(dashboard)/oggi/page.tsx"`
- `venv\Scripts\python.exe -m pytest -q tests\test_workspace_today.py -p no:cacheprovider`
  - expected local outcome: blocked by the broken project `venv` launcher already known in this repo

## Residual risks

- The viewport budget is now canonical, but the agenda strip still coexists with the stack and may still feel partially duplicative for some dense days.
- Identity suppression inside the viewport budget is intentionally narrow (`root_entity` only). Cross-entity semantic compression remains the job of dominance rules, not of the budget layer.

## Next smallest step

Apply the same deterministic treatment to `todo_manual` pollution: if many manual todos accumulate, introduce a mathematically explicit rule for when they stay in `today`, when they degrade into `later`, and when they should be grouped instead of rendered one by one.
