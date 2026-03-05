# UPG-2026-03-05-10 - Dashboard Visual Hierarchy and Chromatic Refinement

## Metadata

- Upgrade ID: UPG-2026-03-05-10
- Date: 2026-03-05
- Owner: Codex
- Area: Dashboard
- Priority: medium
- Target release: codex_02

## Problem

After numeric readability improvements, weekly appointment cards still had weak category labels and
limited visual differentiation. Overall color language was coherent but not yet distinctive enough for
fast operator scan.

## Desired Outcome

Improve visual hierarchy and color semantics while preserving clarity and privacy-safe defaults:

- bigger/more legible weekly labels;
- category-specific card identity;
- state-aware chromatic cues in live panel.

## Scope

- In scope:
  - weekly cards:
    - larger category chips;
    - per-category gradient/border/text themes;
    - stronger sub-counter readability;
  - live panel:
    - countdown/status blocks with colors tied to current mode (`in_progress`, `next_up`, `free`);
    - softer gradient composition for more polished dashboard tone.
- Out of scope:
  - backend or API changes;
  - interaction/flow changes.

## Impact Map

- Files/modules touched:
  - `frontend/src/app/(dashboard)/page.tsx`
  - `docs/upgrades/specs/UPG-2026-03-05-10-dashboard-visual-hierarchy-and-chromatic-refinement.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: frontend + docs
- Invariants:
  - dashboard remains non-financial and privacy-safe;
  - no data contracts changed.

## Acceptance Criteria

- Functional:
  - weekly category label chips are clearly readable at a glance;
  - each weekly category card has distinct but consistent visual identity;
  - live panel color blocks reflect operational state.
- Technical:
  - lint passes on `page.tsx`.

## Test Plan

- Lint:
  - `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"`
- Manual:
  - verify label readability on desktop/mobile;
  - verify color/state consistency for `in_progress`, `next_up`, `free`;
  - verify contrast remains adequate in dark mode.

## Risks and Mitigation

- Risk 1: stronger colors could feel noisy on dense dashboards.
- Mitigation 1: keep background tints subtle and apply color mostly to chips/numeric focal points.

## Rollback Plan

- Revert commit introducing visual theme mapping.

## Notes

- This is microstep 5 in dashboard UX refinement.
