# UPG-2026-03-05-12 - Dashboard Tablet/Mobile Responsive Optimization

## Metadata

- Upgrade ID: UPG-2026-03-05-12
- Date: 2026-03-05
- Owner: Codex
- Area: Dashboard + Governance
- Priority: medium
- Target release: codex_02

## Problem

Dashboard visual hierarchy was improved, but tablet/mobile density still had two issues:

- agenda/live blocks could consume excessive vertical space with many appointments;
- responsive behavior was not yet standardized as reusable guidance beyond dashboard.

## Desired Outcome

Improve dashboard responsiveness across mobile and tablet while preserving desktop density, and add a reusable project skill for future responsive work.

## Scope

- In scope:
  - responsive layout and spacing refinement in dashboard cards/panels;
  - fixed-height + internal-scroll behavior for agenda/live blocks across mobile/tablet;
  - reusable skill `.codex/skills/fitmanager-responsive-adaptive-ui`;
  - routing update in `AGENTS.md` for responsive tasks.
- Out of scope:
  - backend/API behavior changes;
  - business logic changes for dashboard metrics.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `.codex/skills/fitmanager-responsive-adaptive-ui/SKILL.md`
  - `.codex/skills/fitmanager-responsive-adaptive-ui/agents/openai.yaml`
  - `.codex/skills/fitmanager-responsive-adaptive-ui/references/responsive-density-matrix.md`
  - `AGENTS.md`
  - `docs/upgrades/specs/UPG-2026-03-05-12-dashboard-tablet-mobile-responsive-optimization.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + governance docs
- Invariants:
  - privacy-safe dashboard (no financial overview data);
  - dashboard inline status updates remain active;
  - no API contract changes.

## Acceptance Criteria

- Functional:
  - dashboard keeps balanced spacing and typography on mobile/tablet;
  - agenda and live panel maintain fixed compact height with internal scrolling behavior;
  - no layout regressions on desktop.
- Process:
  - new responsive skill has no TODO placeholders;
  - `AGENTS.md` explicitly routes responsive tasks to the new skill.
- Technical:
  - lint passes on modified dashboard page.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"`
- Manual:
  - verify 390px, 768px, 1024px widths;
  - verify agenda with 8+ appointments does not stretch page height;
  - verify key numbers/status labels remain readable.

## Risks and Mitigation

- Risk 1: over-compaction could hurt readability.
- Mitigation 1: keep numeric hierarchy prominent, reduce spacing first.
- Risk 2: fixed heights could clip content.
- Mitigation 2: preserve internal scroll and keep critical controls in visible area.

## Rollback Plan

- Revert this microstep if responsive behavior introduces clipping or interaction regressions.

## Notes

- This upgrade creates a reusable responsive standard to apply beyond dashboard.
