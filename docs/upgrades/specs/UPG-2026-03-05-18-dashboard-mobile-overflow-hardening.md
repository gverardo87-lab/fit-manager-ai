# UPG-2026-03-05-18 - Dashboard Mobile Overflow Hardening

## Metadata

- Upgrade ID: UPG-2026-03-05-18
- Date: 2026-03-05
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: codex_02

## Problem

Dashboard mobile usage still showed clipping and horizontal overflow in operational rows:

- agenda rows could exceed viewport width on narrow screens;
- todo/impegni rows could feel cramped and partially clipped;
- KPI/alert blocks were vulnerable to header badge wrapping issues.

## Desired Outcome

Stabilize dashboard mobile/tablet rendering so cards and rows remain fully visible, scrollable, and touch-usable without changing business logic.

## Scope

- In scope:
  - mobile-safe width constraints (`min-w-0`) on dashboard board containers;
  - wrapping/truncation hardening for KPI/alert/live/agenda row content;
  - todo card density + row overflow hardening for mobile;
  - touch-visible delete affordance on todo rows.
- Out of scope:
  - backend/API behavior changes;
  - metric logic or alert generation logic changes.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `frontend/src/components/dashboard/TodoCard.tsx`
  - `docs/upgrades/specs/UPG-2026-03-05-18-dashboard-mobile-overflow-hardening.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - privacy-safe dashboard data policy unchanged;
  - inline agenda status update flow unchanged;
  - no API contract changes.

## Acceptance Criteria

- Functional:
  - no horizontal overflow in dashboard at 390px width;
  - agenda and todo rows stay inside viewport bounds;
  - KPI/alert headers do not clip on narrow widths.
- Technical:
  - lint passes for touched dashboard/todo files.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx" "src/components/dashboard/TodoCard.tsx"`
- Manual:
  - verify 390px, 768px, 1024px widths;
  - verify agenda rows with long client/title values do not overflow;
  - verify todo rows keep title/date/delete controls visible and touch-usable.

## Risks and Mitigation

- Risk 1: additional truncation may hide useful text context.
- Mitigation 1: apply truncation only on narrow, secondary lines while preserving primary labels.

## Rollback Plan

- Revert this microstep if mobile readability regresses or critical context is hidden.
