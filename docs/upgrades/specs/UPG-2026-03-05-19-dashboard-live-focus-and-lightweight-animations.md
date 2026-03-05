# UPG-2026-03-05-19 - Dashboard Live Focus and Lightweight Animations

## Metadata

- Upgrade ID: UPG-2026-03-05-19
- Date: 2026-03-05
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: codex_02

## Problem

After mobile overflow hardening, dashboard readability improved but the page still felt static.
The goal was to add liveliness and guidance without adding dependencies or degrading performance.

## Desired Outcome

Add lightweight, meaningful UI motion and a smart operational prompt that improves decision speed on dashboard.

## Scope

- In scope:
  - smart "Focus operativo" bar based on existing summary/events/alerts data;
  - staggered entrance reveal for KPI cards, agenda rows, quick actions, and main board section;
  - local feature flag for fast rollback;
  - reduced-motion safe behavior (`motion-reduce` classes).
- Out of scope:
  - backend/API changes;
  - persistence of animation preferences;
  - business logic changes in alert generation.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `docs/upgrades/specs/UPG-2026-03-05-19-dashboard-live-focus-and-lightweight-animations.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - dashboard remains privacy-safe;
  - existing agenda inline status update flow unchanged;
  - no new frontend dependencies introduced.

## Acceptance Criteria

- Functional:
  - dashboard shows one contextual "Focus operativo" message with relevant CTA;
  - entry reveal is visible but lightweight on KPI, agenda rows, and quick actions;
  - behavior remains readable with reduced-motion preferences.
- Technical:
  - no new packages;
  - lint passes on touched frontend files.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx" "src/components/dashboard/TodoCard.tsx"`
- Manual:
  - verify focus bar priority logic (critical alert > next session > free day > monitor alerts > stable state);
  - verify entry reveal on 390px, 768px, 1024px;
  - verify no clipping regressions from previous microstep.

## Risks and Mitigation

- Risk 1: motion may feel distracting on some devices.
- Mitigation 1: keep transform/opacity-only transitions and support reduced-motion.
- Risk 2: fallback/rollback may be slow if spread across components.
- Mitigation 2: single local toggle `DASHBOARD_MICROSTEP2_ENABLED`.

## Rollback Plan

- Set `DASHBOARD_MICROSTEP2_ENABLED` to `false` in dashboard page to disable this microstep quickly.
