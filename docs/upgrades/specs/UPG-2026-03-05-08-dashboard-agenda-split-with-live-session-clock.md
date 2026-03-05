# UPG-2026-03-05-08 - Dashboard Agenda Split with Live Session Clock

## Metadata

- Upgrade ID: UPG-2026-03-05-08
- Date: 2026-03-05
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: codex_02

## Problem

Agenda rows consumed too much horizontal space with low information density. Operators needed a second
high-value panel instead of empty area.

## Desired Outcome

Split the agenda area into two panels:

- left: current agenda list (existing behavior);
- right: real-time operational widget with studio clock and next-session countdown, plus live status
  ("occupato/in progress/libero").

## Scope

- In scope:
  - dashboard layout update: agenda area rendered in 2 tiles on large screens;
  - new live panel with:
    - real-time clock (seconds)
    - countdown to next appointment
    - "in progress" state when lesson is active
    - event detail snippet (title/time/client) when available;
  - loading state for live panel.
- Out of scope:
  - backend endpoints or data model changes;
  - cross-day countdown logic beyond current day events.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `docs/upgrades/specs/UPG-2026-03-05-08-dashboard-agenda-split-with-live-session-clock.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - privacy-safe dashboard preserved (no financial values);
  - no API contract changes.

## Acceptance Criteria

- Functional:
  - agenda zone shows two panels on large screens;
  - live panel shows current clock and dynamic countdown;
  - if an event is currently active, status switches to "in progress/occupato";
  - if no active/upcoming events, panel shows "libero".
- Technical:
  - lint passes on modified dashboard file.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"`
- Manual:
  - validate panel states:
    - active lesson
    - upcoming lesson
    - no events
  - validate responsive behavior on mobile/desktop.

## Risks and Mitigation

- Risk 1: 1-second timer can create minor rendering overhead.
- Mitigation 1: timer isolated in dedicated live panel component, limited scope.

## Rollback Plan

- Revert dashboard commit introducing agenda split and live panel.

## Notes

- This is microstep 3 in dashboard UX effectiveness hardening.
