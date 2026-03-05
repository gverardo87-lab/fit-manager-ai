# UPG-2026-03-05-04 - FitManager Skill Pack Foundation

## Metadata

- Upgrade ID: UPG-2026-03-05-04
- Date: 2026-03-05
- Owner: Codex
- Area: Governance + Agent Workflow
- Priority: medium
- Target release: codex_02

## Problem

The repository had AGENTS-level governance but no concrete reusable project skills.
This limited automatic specialization and made repeated workflows less consistent.

## Desired Outcome

Add a shared skill pack under `.codex/skills` so Codex can automatically pick focused
workflow instructions for frontend safety, API integrity, cash-critical changes, doc sync,
and microstep delivery.

## Scope

- In scope:
  - create 5 project skills with complete `SKILL.md`;
  - provide `agents/openai.yaml` metadata per skill.
- Out of scope:
  - third-party skill installation in `~/.codex/skills`;
  - MCP provider provisioning with secrets.

## Impact Map

- Files/modules touched:
  - `.codex/skills/fitmanager-microstep-delivery/*`
  - `.codex/skills/fitmanager-frontend-safety/*`
  - `.codex/skills/fitmanager-api-integrity/*`
  - `.codex/skills/fitmanager-cash-integrity/*`
  - `.codex/skills/fitmanager-upgrade-doc-sync/*`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: process/documentation
- Invariants:
  - no runtime business behavior changes;
  - no conflict with AGENTS/CLAUDE hierarchy.

## Acceptance Criteria

- Functional:
  - 5 project skills exist with non-template content.
  - each skill has valid frontmatter (`name`, `description`).
  - each skill has `agents/openai.yaml`.
- Technical:
  - no placeholder TODO blocks remain in created skills.
  - upgrade docs/workboard are aligned.

## Test Plan

- Manual:
  - verify skill folder structure and key files.
  - verify no TODO placeholders in `.codex/skills`.
  - verify upgrade log and README references.

## Risks and Mitigation

- Risk 1: overlapping or ambiguous skill triggers.
- Mitigation 1: keep descriptions explicit and domain-scoped.

## Rollback Plan

- Revert the skill-pack commits if trigger quality degrades and iterate with narrower scopes.

## Notes

- This upgrade establishes the first loop of a continuous skill-evolution process.
