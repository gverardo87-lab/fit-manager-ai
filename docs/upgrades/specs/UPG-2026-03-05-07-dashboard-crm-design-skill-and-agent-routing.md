# UPG-2026-03-05-07 - Dashboard CRM Design Skill and Agent Routing

## Metadata

- Upgrade ID: UPG-2026-03-05-07
- Date: 2026-03-05
- Owner: Codex
- Area: Governance + Dashboard UX
- Priority: medium
- Target release: codex_02

## Problem

Dashboard UX microsteps are accelerating, but reusable visual rules were not encoded in a dedicated
skill. This increases drift risk across future dashboard edits.

## Desired Outcome

Create a dedicated project skill for dashboard CRM visual design and route agents to it from
`AGENTS.md` before the next dashboard microsteps.

## Scope

- In scope:
  - new skill folder `.codex/skills/fitmanager-dashboard-crm-design/`;
  - skill instructions focused on hierarchy, readability, responsive card/table patterns,
    and privacy-safe dashboard constraints;
  - `agents/openai.yaml` metadata for deterministic invocation;
  - `AGENTS.md` update to route dashboard visual redesigns to this skill.
- Out of scope:
  - dashboard code changes;
  - backend/API changes.

## Impact Map

- Files/modules touched:
  - `.codex/skills/fitmanager-dashboard-crm-design/SKILL.md`
  - `.codex/skills/fitmanager-dashboard-crm-design/agents/openai.yaml`
  - `AGENTS.md`
  - `docs/upgrades/specs/UPG-2026-03-05-07-dashboard-crm-design-skill-and-agent-routing.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer: governance/process docs
- Invariants:
  - microstep-first workflow preserved;
  - dashboard remains privacy-safe by default.

## Acceptance Criteria

- Functional:
  - skill exists with complete frontmatter and actionable body;
  - `openai.yaml` has valid interface metadata and a default prompt mentioning skill name;
  - `AGENTS.md` explicitly routes dashboard visual redesigns to the new skill.
- Technical:
  - no TODO placeholders in the new skill;
  - validation attempted and blockers documented if local dependency missing.

## Test Plan

- Validation:
  - attempted: `python .../quick_validate.py .codex/skills/fitmanager-dashboard-crm-design`
  - fallback checks:
    - no TODO in skill files
    - frontmatter and metadata manually inspected

## Risks and Mitigation

- Risk 1: skill validator dependency (`pyyaml`) missing locally may hide structural issues.
- Mitigation 1: perform manual frontmatter/metadata checks now; run full validator when dependency
  is available.

## Rollback Plan

- Revert governance commit if skill routing causes undesired invocation behavior.

## Notes

- This upgrade prepares a reusable design standard for upcoming dashboard UX microsteps.
