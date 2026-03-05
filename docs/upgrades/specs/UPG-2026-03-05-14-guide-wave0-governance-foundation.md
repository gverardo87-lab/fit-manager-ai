# UPG-2026-03-05-14 - Guide Wave 0 Governance Foundation

## Metadata

- Upgrade ID: UPG-2026-03-05-14
- Date: 2026-03-05
- Owner: Codex
- Area: Guide + Governance
- Priority: medium
- Target release: codex_02

## Problem

FitManager has strong product flows and a deterministic assistant base, but there is no unified
guide program that starts from simple chaptered help and evolves toward illustrated and interactive
support with assistant linking.

Without a dedicated governance foundation, guide implementation risks fragmentation, stale content,
and weak alignment between documentation, UI help, and assistant behavior.

## Desired Outcome

Complete Wave 0 foundation that enables guided delivery for the next waves:

- establish project skills dedicated to guide architecture, illustrated guidance, and assistant-guide linking;
- update agent routing rules in `AGENTS.md`;
- define roadmap specs for Wave 1/2/3;
- synchronize upgrade tracking and workboard artifacts.

## Scope

- In scope:
  - create 3 new guide-focused skills in `.codex/skills`;
  - update `AGENTS.md` routing and quality gates for guide/help tasks;
  - create roadmap specs:
    - `UPG-2026-03-05-15` (chapters/sections),
    - `UPG-2026-03-05-16` (illustrated layer),
    - `UPG-2026-03-05-17` (interactive + assistant linking);
  - sync `UPGRADE_LOG`, `docs/upgrades/README`, and `WORKBOARD`.
- Out of scope:
  - frontend runtime implementation of guide UI;
  - backend assistant feature expansion;
  - screenshot production and interactive tour mechanics.

## Impact Map

- Files/modules touched:
  - `AGENTS.md`
  - `.codex/skills/fitmanager-guide-content-architecture/*`
  - `.codex/skills/fitmanager-guide-illustrated-playbook/*`
  - `.codex/skills/fitmanager-assistant-guide-linking/*`
  - `docs/upgrades/specs/UPG-2026-03-05-14-guide-wave0-governance-foundation.md`
  - `docs/upgrades/specs/UPG-2026-03-05-15-guide-chapters-and-sections-foundation.md`
  - `docs/upgrades/specs/UPG-2026-03-05-16-guide-illustrated-layer.md`
  - `docs/upgrades/specs/UPG-2026-03-05-17-guide-interactive-and-assistant-linking.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: governance/process docs + skill metadata
- Invariants:
  - no runtime behavior change in API/frontend;
  - privacy-first and deterministic constraints preserved;
  - microstep and doc-sync process remains mandatory.

## Acceptance Criteria

- Functional:
  - 3 guide skills exist with complete `SKILL.md` + `agents/openai.yaml`;
  - `AGENTS.md` includes explicit routing for guide and assistant-guide tasks;
  - roadmap specs for Wave 1/2/3 are present.
- Process:
  - upgrade ledger and workboard are synchronized;
  - next waves are clearly staged as planned units.
- Technical:
  - no TODO placeholders in added skill files;
  - path references in docs are valid.

## Test Plan

- Manual checks:
  - verify new skill folder structure and metadata files;
  - verify AGENTS routing lines and quality gate additions;
  - verify UPG IDs are unique and chronological.
- Validation checks:
  - no TODO placeholder in new skill files;
  - cross-reference check between specs and upgrade log.

## Risks and Mitigation

- Risk 1: guide roadmap remains broad and hard to execute.
- Mitigation 1: lock Wave 1/2/3 as separate microstep deliverables with explicit acceptance criteria.

- Risk 2: assistant and guide evolutions diverge.
- Mitigation 2: enforce dedicated assistant-guide-linking skill and read-only help contract.

## Rollback Plan

- Revert Wave 0 governance patch if routing or skill activation quality regresses.
- Keep previous AGENTS rules and existing skill pack untouched by isolating this change set.

## Notes

- This wave is governance-first by design; runtime guide implementation starts in `UPG-2026-03-05-15`.

