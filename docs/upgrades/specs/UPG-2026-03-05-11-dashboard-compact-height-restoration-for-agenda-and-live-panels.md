# UPG-2026-03-05-11 - Dashboard Compact Height Restoration for Agenda and Live Panels

## Metadata

- Upgrade ID: UPG-2026-03-05-11
- Date: 2026-03-05
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: codex_02

## Problem

After recent visual enhancements, agenda and live panels grew too tall. With many daily appointments
the dashboard vertical footprint became excessive.

## Desired Outcome

Restore compact desktop height for the two top-left panels while keeping appointments scrollable
inside the agenda card.

## Scope

- In scope:
  - fixed desktop height for `TodayAgenda` and `AgendaLivePanel`;
  - agenda internal scrolling always active (list no longer expands page height);
  - compact spacing adjustments in live panel to fit original density.
- Out of scope:
  - logic changes for appointments/statuses;
  - backend/API changes.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `docs/upgrades/specs/UPG-2026-03-05-11-dashboard-compact-height-restoration-for-agenda-and-live-panels.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - dashboard interactivity preserved;
  - no data contract changes.

## Acceptance Criteria

- Functional:
  - on desktop, agenda and live panel keep compact fixed height;
  - agenda appointments remain scrollable for long daily lists (8/20+ rows);
  - page height no longer expands proportionally to appointment count.
- Technical:
  - lint passes on modified file.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"`
- Manual:
  - seed day with 8+ appointments and verify internal scroll;
  - verify compact panel height consistency between agenda and live panel;
  - verify mobile remains usable.

## Risks and Mitigation

- Risk 1: too-compact content could reduce readability.
- Mitigation 1: keep typography hierarchy unchanged; reduce only spacing and panel height.

## Rollback Plan

- Revert compact-height commit if overflow/readability regressions are observed.

## Notes

- This is a corrective microstep after visual refinement, focused on practical operator density.
