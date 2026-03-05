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

- Files/modules touched:
  - `docs/guides/README.md`
  - `docs/guides/chapters/01-inizio-rapido.md`
  - `docs/guides/chapters/02-dashboard-operativa.md`
  - `docs/guides/chapters/03-agenda-e-appuntamenti.md`
  - `docs/guides/chapters/04-clienti-e-profilo.md`
  - `docs/guides/chapters/05-contratti-e-pagamenti.md`
  - `docs/guides/chapters/06-cassa-e-controllo-economico.md`
  - `docs/guides/chapters/07-esercizi-e-archivio-tecnico.md`
  - `docs/guides/chapters/08-schede-allenamento.md`
  - `docs/guides/chapters/09-monitoraggio-allenamenti.md`
  - `docs/guides/chapters/10-impostazioni-backup-e-sicurezza.md`
  - `docs/guides/chapters/11-command-palette-e-assistente.md`
  - `docs/guides/chapters/12-faq-e-troubleshooting.md`
  - `docs/upgrades/specs/UPG-2026-03-05-15-guide-chapters-and-sections-foundation.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: docs-first with optional lightweight frontend links
- Invariants:
  - privacy-safe examples;
  - no forced AI dependency;
  - deterministic instructions tied to existing UI labels.

## Acceptance Criteria

- each core route has at least one guide chapter section;
- each section includes purpose, steps, mistakes, and recovery;
- chapter links are valid and discoverable from the guide index;
- docs sync is complete for the wave.

## Test Plan

- Manual:
  - coverage audit against core route list;
  - link validation pass;
  - UX readability check on desktop/tablet/mobile.

## Verification Evidence

- `docs/guides/` created with 12 chapter files + index.
- Route coverage validated against Wave 1 matrix:
  - `/setup`, `/login`, `/`, `/agenda`, `/clienti`, `/clienti/[id]`,
    `/contratti`, `/contratti/[id]`, `/cassa`, `/esercizi`, `/esercizi/[id]`,
    `/schede`, `/schede/[id]`, `/allenamenti`, `/impostazioni`, global `Ctrl+K`.
- Chapter structure validated for all files:
  - section for purpose
  - steps
  - common mistakes
  - troubleshooting
  - quick actions

## Risks and Mitigation

- Risk: guide text becomes generic and not actionable.
- Mitigation: enforce strict chapter template with route and CTA references.

## Rollback Plan

- Revert wave files and keep only Wave 0 governance artifacts if content quality is insufficient.

## Notes

- Wave 1 intentionally ships as docs-first foundation.
- Illustrated assets and interactive guide behaviors are deferred to `UPG-2026-03-05-16` and `UPG-2026-03-05-17`.
