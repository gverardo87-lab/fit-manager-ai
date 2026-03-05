# UPG-2026-03-05-16 - Guide Illustrated Layer

## Metadata

- Upgrade ID: UPG-2026-03-05-16
- Date: 2026-03-05
- Owner: Codex
- Area: Guide UX
- Priority: medium
- Target release: codex_02

## Problem

Text-only guidance can be clear but still slow for first-time users in dense CRM pages.
The project lacks a standardized illustrated layer with annotated visuals and responsive variants.

## Desired Outcome

Add an illustrated guide layer with callout-based screenshots that accelerates comprehension without
compromising privacy or usability on mobile/tablet.

## Scope

- In scope:
  - produce annotated visuals for highest-frequency chapters;
  - enforce callout standards and responsive visual variants;
  - embed visuals into guide content with one-step/one-image consistency.
- Out of scope:
  - interactive tooltip engine;
  - assistant routing changes;
  - backend/API modifications.

## Impact Map

- Planned files/modules:
  - `docs/guides/assets/*` (screenshots and annotation exports)
  - `docs/guides/*` (chapter updates with visual blocks)
  - optional frontend rendering components if in-app docs are enabled
- Layer: docs UX (with optional frontend integration)
- Invariants:
  - no sensitive real data in visuals;
  - mobile readability preserved;
  - visual labels consistent with live UI wording.

## Acceptance Criteria

- top-priority chapters have illustrated steps;
- callout density and style are consistent;
- desktop/tablet/mobile visual sets are available for critical flows;
- docs sync and upgrade tracking are complete.

## Test Plan

- Manual:
  - review annotations for clarity and overlap;
  - verify responsive readability at 390px, 768px, 1024px;
  - verify chapter text and visual steps are aligned.

## Risks and Mitigation

- Risk: over-annotated images reduce comprehension.
- Mitigation: cap callouts per frame and split long flows into multiple frames.

## Rollback Plan

- Revert illustrated assets and retain text-only guide foundation from Wave 1.

