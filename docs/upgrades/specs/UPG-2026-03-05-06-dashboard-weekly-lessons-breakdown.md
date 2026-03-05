# UPG-2026-03-05-06 - Dashboard Weekly Lessons Breakdown

## Metadata

- Upgrade ID: UPG-2026-03-05-06
- Date: 2026-03-05
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: codex_02

## Problem

Dashboard was privacy-safe and had stronger KPI cards, but still missed a weekly operational view useful
for kinesiology scheduling decisions.

## Desired Outcome

Expose a compact "Lezioni della settimana" section that groups agenda events by category and status to
help the operator understand weekly workload and execution pace.

## Scope

- In scope:
  - weekly event query for current week range (Mon-Sun, no backend change);
  - breakdown cards by category (`PT`, `PERSONALE`, `COLLOQUIO`, `SALA`, `CORSO`);
  - per-category counters: total, in agenda, completate, cancellate;
  - direct CTA to open full agenda.
- Out of scope:
  - countdown and reminder logic;
  - backend endpoints or schema changes;
  - financial data exposure.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `docs/upgrades/specs/UPG-2026-03-05-06-dashboard-weekly-lessons-breakdown.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - privacy-first dashboard policy preserved;
  - no economic cards or amounts reintroduced;
  - existing alert/todo/agenda blocks kept intact.

## Acceptance Criteria

- Functional:
  - dashboard shows a "Lezioni della settimana" section with category cards.
  - each card displays total, scheduled, completed, cancelled counters.
  - section includes week label and link to `/agenda`.
- Technical:
  - no API contract changes;
  - lint passes on modified dashboard file.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"`
- Manual:
  - verify cards with empty week and populated week;
  - verify all expected categories render;
  - verify responsiveness on desktop/mobile breakpoints.

## Risks and Mitigation

- Risk 1: week range is computed client-side and may feel stale if dashboard stays open for long sessions.
- Mitigation 1: schedule follow-up microstep for periodic refresh + date normalization hardening.

## Rollback Plan

- Revert commit introducing weekly section if regressions are reported.

## Notes

- This is microstep 2 of the dashboard usability uplift for kinesiology daily operations.
