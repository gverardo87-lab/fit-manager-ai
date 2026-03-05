# UPG-2026-03-05-05 - Dashboard Operational KPI Boost

## Metadata

- Upgrade ID: UPG-2026-03-05-05
- Date: 2026-03-05
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: codex_02

## Problem

After privacy hardening, dashboard no longer exposed financial data but became too weak as an
operator cockpit for kinesiology daily work.

## Desired Outcome

Increase operational usefulness with action-oriented, non-financial KPIs using existing data
without backend contract changes.

## Scope

- In scope:
  - extend hero KPIs from 2 to 4 operational cards:
    - active clients
    - appointments today
    - upcoming sessions (from now)
    - actionable alerts count
  - keep financial data hidden.
- Out of scope:
  - backend changes
  - new API endpoints
  - major layout redesign.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - privacy-first dashboard policy;
  - no financial KPI reintroduction;
  - existing alert/todo/agenda sections preserved.

## Acceptance Criteria

- Functional:
  - dashboard shows 4 non-financial operational KPIs.
  - "Alert Operativi" KPI anchors to alert panel.
  - "Sessioni Imminenti" reflects today scheduled sessions from current time.
- Technical:
  - no TypeScript/lint issues in modified file.
  - no API contract changes required.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"`
- Manual:
  - verify KPI values with/without alerts;
  - verify alert anchor navigation;
  - verify layout on mobile and desktop.

## Risks and Mitigation

- Risk 1: KPI values can feel stale if dashboard stays open across midnight.
- Mitigation 1: keep current behavior and plan a dedicated time-refresh hardening step.

## Rollback Plan

- Revert dashboard KPI expansion commit if usability regressions appear.

## Notes

- This is microstep 1 of broader dashboard effectiveness uplift.
