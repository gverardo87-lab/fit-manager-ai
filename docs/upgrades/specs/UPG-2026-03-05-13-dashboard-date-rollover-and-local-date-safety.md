# UPG-2026-03-05-13 - Dashboard Date Rollover and Local Date Safety

## Metadata

- Upgrade ID: UPG-2026-03-05-13
- Date: 2026-03-05
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: codex_02

## Problem

Date helpers in dashboard used a module-level `now` snapshot and UTC slicing (`toISOString().slice(0, 10)`).
This could cause:

- stale day/week labels and queries if the dashboard stayed open across midnight;
- local date mismatch around midnight due to UTC conversion.

## Desired Outcome

Make dashboard day/week calculations local-time safe and automatically refreshed at day rollover.

## Scope

- In scope:
  - replace UTC-based date slicing with local `YYYY-MM-DD` formatter;
  - remove static `now` snapshot and use dynamic date anchor;
  - refresh date anchor automatically at next midnight;
  - propagate dynamic date labels to header/agenda/weekly summary.
- Out of scope:
  - backend/API contract changes;
  - calendar domain logic changes.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `docs/upgrades/specs/UPG-2026-03-05-13-dashboard-date-rollover-and-local-date-safety.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - privacy-safe dashboard remains unchanged;
  - inline status mutation flow remains unchanged.

## Acceptance Criteria

- Functional:
  - daily and weekly dashboard ranges are based on local date;
  - dashboard refreshes date anchor at midnight without reload;
  - date labels in header/agenda/weekly block stay aligned with active day.
- Technical:
  - lint passes on touched dashboard file.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"`
- Manual:
  - keep dashboard open across date boundary and verify day/week labels update;
  - verify morning hours do not shift to previous day because of UTC slicing.

## Risks and Mitigation

- Risk 1: timer refresh logic may stop after first rollover.
- Mitigation 1: effect reschedules itself on each `dateAnchor` update.

## Rollback Plan

- Revert this microstep if date filtering/regression is detected in agenda data loading.
