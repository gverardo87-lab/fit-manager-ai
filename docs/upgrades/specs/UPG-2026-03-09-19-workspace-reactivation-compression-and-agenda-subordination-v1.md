# UPG-2026-03-09-19 - Workspace Reactivation Compression and Agenda Subordination v1

## Context

After `UPG-2026-03-09-17` and `UPG-2026-03-09-18`, the main onboarding overload was removed from `Oggi`.

Real payload analysis on the DEV workspace then showed a different residual issue:

- operational work was mostly `payment_overdue` and `session_imminent`
- `client_reactivation` still occupied a large portion of the "later" surface
- the agenda strip duplicated the same session context already visible in the stack

This did not break correctness, but it still diluted the operational hierarchy.

## Problem

Two low-signal patterns were still hurting `Oggi`:

1. `client_reactivation` was still treated as a first-class daily queue item, even when the day already had structural pressure from finance or sessions.
2. The agenda panel repeated session information instead of adding a tighter temporal cue.

`Oggi` needs backlog awareness, but it must not let reactivation or agenda compete visually with work that is already burning today.

## Decision

Apply two deterministic constraints without changing the API contract or adding new case kinds.

### Reactivation compression

- `client_reactivation` never lands in bucket `today`
- it is always synthesized into `upcoming_7d`
- visible reactivation backlog inside `GET /api/workspace/today` is capped dynamically:
  - `1` item if `now` already contains at least one structural case
  - `1` item if `today` already contains at least three structural cases
  - `2` items otherwise

Important:

- the full backlog is still preserved in `GET /api/workspace/cases`
- no reactivation case is deleted, merged away, or reclassified into a new workspace

### Agenda subordination

- `WorkspaceAgendaPanel` becomes a support cue, not a parallel list
- it now shows at most the next relevant slot
- it renders only when:
  - the next slot is `current`, or
  - the next slot starts within the next 120 minutes

If no such slot exists, the panel disappears from `Oggi`.

## Runtime Impact

Touched files:

- `api/services/workspace_engine.py`
- `frontend/src/app/(dashboard)/oggi/page.tsx`
- `frontend/src/components/workspace/WorkspaceAgendaPanel.tsx`
- `tests/test_workspace_today.py`

Backend effects:

- reactivation backlog is compressed by viewport policy instead of polluting the daily queue
- `today` and `cases` remain intentionally different:
  - `today` = curated visible queue
  - `cases` = full searchable backlog

Frontend effects:

- agenda is rendered only when it changes near-term behavior
- the "Puo aspettare" counter now uses section totals, not only visible items

## Verification

### Static gates

- `venv\Scripts\ruff.exe check api\services\workspace_engine.py tests\test_workspace_today.py`
- `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run lint -- "src/app/(dashboard)/oggi/page.tsx" "src/components/workspace/WorkspaceAgendaPanel.tsx"`

Result:

- `ruff`: `PASS`
- `eslint`: `PASS`

### Test coverage added

Added deterministic coverage for:

- reactivation removed from `today`
- reactivation backlog preserved in `workspace=today` case list
- visible `upcoming_7d` reactivation backlog capped under structural pressure

### Environment limitation

- `pytest` remains blocked by the broken local `venv` launcher, which still resolves to the Microsoft Store Python path
- live `8001` health was verified, but authenticated workspace HTTP verification could not be completed non-destructively without a reusable DEV credential

## Risks

- `client_reactivation` is now intentionally much quieter in `Oggi`; if the product later needs a true reactivation workspace, this backlog should move there instead of being promoted again in the daily surface
- `/api/workspace/cases?workspace=today&sort_by=priority` still deserves a separate cleanup pass, because the read-only list contract is broader than the curated `today.sections` ordering

## Next Smallest Step

Do not add new signals yet.

The next mathematically correct step is:

- align `workspace/cases` priority ordering with the curated `today` hierarchy

That would remove the last ranking drift between the searchable backlog and the visible operational queue.
