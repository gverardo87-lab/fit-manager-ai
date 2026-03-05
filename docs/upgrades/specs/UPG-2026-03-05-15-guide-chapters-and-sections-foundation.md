# UPG-2026-03-05-15 - Guide Chapters and Sections Foundation

## Metadata

- Upgrade ID: UPG-2026-03-05-15
- Date: 2026-03-05
- Owner: Codex
- Area: Guide
- Priority: medium
- Target release: codex_02

## Problem

There is no unified chaptered user guide that maps all core CRM workflows with consistent
structure, troubleshooting, and next actions.

## Desired Outcome

Deliver a complete chapter/section guide foundation that helps users discover all major features
and solve common operational doubts with clear, welcoming instructions.

## Scope

- In scope:
  - define canonical guide taxonomy and chapter order;
  - produce route-mapped chapters for all core CRM surfaces;
  - include FAQ and troubleshooting blocks per chapter;
  - connect chapter content to command palette discovery examples.
- Out of scope:
  - screenshot/callout production;
  - interactive tours;
  - assistant mode behavior changes.

## Impact Map

- Planned files/modules:
  - `docs/guides/` (new guide content tree)
  - `frontend/src/lib/help/*` (optional guide metadata index)
  - `frontend/src/components/layout/*` (entry links only if needed)
  - docs sync files under `docs/upgrades/` and `docs/ai-sync/`
- Layer: docs-first with optional lightweight frontend links
- Invariants:
  - privacy-safe examples;
  - no forced AI dependency;
  - deterministic instructions tied to existing UI labels.

## Acceptance Criteria

- each core route has at least one guide chapter section;
- each section includes purpose, steps, mistakes, and recovery;
- chapter links are valid and discoverable from at least one UI entry point;
- docs sync is complete for the wave.

## Test Plan

- Manual:
  - coverage audit against core route list;
  - link validation pass;
  - UX readability check on desktop/tablet/mobile.

## Risks and Mitigation

- Risk: guide text becomes generic and not actionable.
- Mitigation: enforce strict chapter template with route and CTA references.

## Rollback Plan

- Revert wave files and keep only Wave 0 governance artifacts if content quality is insufficient.

