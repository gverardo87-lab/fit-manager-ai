# UPG-2026-03-05-09 - Dashboard Inline Appointment Status Updates

## Metadata

- Upgrade ID: UPG-2026-03-05-09
- Date: 2026-03-05
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: codex_02

## Problem

Dashboard had agenda visibility but lacked direct action on appointment state.
Operators had to open full Agenda to mark sessions as completed, postponed, or cancelled.

## Desired Outcome

Enable inline state updates for today appointments directly from dashboard rows.

## Scope

- In scope:
  - add status selector on each appointment row in dashboard agenda;
  - update event state via existing `useUpdateEvent` mutation (no API change);
  - show lightweight per-row updating feedback.
- Out of scope:
  - bulk status updates;
  - historical timeline/status audit UI.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `docs/upgrades/specs/UPG-2026-03-05-09-dashboard-inline-appointment-status-updates.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - privacy-safe dashboard preserved (no financial data);
  - API contract unchanged (`useUpdateEvent` reused).

## Acceptance Criteria

- Functional:
  - each dashboard agenda appointment exposes selectable states:
    - `Programmato`
    - `Completato`
    - `Rinviato`
    - `Cancellato`
  - selecting a state triggers mutation and refreshes agenda/dashboard data.
  - while updating, the touched row shows a visual pending hint.
- Technical:
  - lint passes on modified dashboard file.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"`
- Manual:
  - set an appointment `Programmato -> Completato`;
  - set `Programmato -> Rinviato`;
  - set `Programmato -> Cancellato` and verify disappearance from today list.

## Risks and Mitigation

- Risk 1: accidental status change from dashboard compact controls.
- Mitigation 1: keep full Agenda as advanced workspace; monitor feedback and consider confirm step
  for destructive status (`Cancellato`) in a follow-up microstep.

## Rollback Plan

- Revert dashboard commit introducing inline selectors.

## Notes

- This is microstep 4 in dashboard interactivity hardening.
