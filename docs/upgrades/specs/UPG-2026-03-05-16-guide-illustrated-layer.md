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

- Files/modules touched:
  - `docs/guides/illustrated/README.md`
  - `docs/guides/illustrated/flow-01-setup-login-primi-passi.md`
  - `docs/guides/illustrated/flow-02-dashboard-scan.md`
  - `docs/guides/illustrated/flow-03-agenda-operativa.md`
  - `docs/guides/illustrated/flow-04-clienti-profilo.md`
  - `docs/guides/illustrated/flow-05-contratti-rate.md`
  - `docs/guides/illustrated/flow-06-cassa-movimenti.md`
  - `docs/guides/illustrated/flow-07-impostazioni-backup.md`
  - `docs/guides/illustrated/flow-08-command-palette-assistente.md`
  - `docs/guides/assets/illustrated/README.md`
  - `docs/guides/assets/illustrated/manifest-wave2.md`
  - `docs/guides/README.md`
  - `docs/guides/chapters/01-inizio-rapido.md`
  - `docs/guides/chapters/02-dashboard-operativa.md`
  - `docs/guides/chapters/03-agenda-e-appuntamenti.md`
  - `docs/guides/chapters/04-clienti-e-profilo.md`
  - `docs/guides/chapters/05-contratti-e-pagamenti.md`
  - `docs/guides/chapters/06-cassa-e-controllo-economico.md`
  - `docs/guides/chapters/10-impostazioni-backup-e-sicurezza.md`
  - `docs/guides/chapters/11-command-palette-e-assistente.md`
  - `docs/upgrades/specs/UPG-2026-03-05-16-guide-illustrated-layer.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
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

## Verification Evidence

- 8 critical flow files created with callout-based step frames.
- Responsive set declared for each flow (`desktop/tablet/mobile`).
- Callout standards enforced in flow files and manifest:
  - max 4 callouts per frame
  - short labels
  - ordered markers.
- Wave 1 chapters linked to relevant illustrated flows.

## Risks and Mitigation

- Risk: over-annotated images reduce comprehension.
- Mitigation: cap callouts per frame and split long flows into multiple frames.

## Rollback Plan

- Revert illustrated assets and retain text-only guide foundation from Wave 1.

## Notes

- Wave 2 in this phase ships as annotation-ready illustrated specifications and asset manifest.
- Screenshot capture/export execution remains operationally straightforward using the provided naming and checklist.
