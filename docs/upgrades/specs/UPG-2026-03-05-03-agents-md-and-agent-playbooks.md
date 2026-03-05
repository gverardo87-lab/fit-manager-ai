# UPG-2026-03-05-03 - AGENTS.md Baseline and Agent Playbooks

## Metadata

- Upgrade ID: UPG-2026-03-05-03
- Date: 2026-03-05
- Owner: Codex
- Area: Process + Governance
- Priority: medium
- Target release: codex_02 kickoff

## Problem

The repository had strong guidance in `CLAUDE.md` and `codex.md`, but no native `AGENTS.md`
entrypoint for Codex. This limited standardization of microstep execution and reduced
discoverability for agent-first workflows.

## Desired Outcome

Enable a first-class agent operating model with:

- root `AGENTS.md` as default operating contract;
- a dedicated `agents/` workspace for focused playbooks;
- explicit alignment with existing quality and documentation gates.

## Scope

- In scope:
  - create root `AGENTS.md`;
  - create `agents/README.md`;
  - create layer overrides:
    - `frontend/AGENTS.override.md`
    - `api/AGENTS.override.md`
  - create project Codex config baseline (`.codex/config.toml`) with MCP-ready setup;
  - update upgrade tracking docs.
- Out of scope:
  - provisioning secrets/tokens for third-party MCP providers;
  - replacing existing `CLAUDE.md`/`codex.md` governance.

## Impact Map

- Files/modules touched:
  - `AGENTS.md`
  - `agents/README.md`
  - `frontend/AGENTS.override.md`
  - `api/AGENTS.override.md`
  - `.codex/config.toml`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
- Layer: process/documentation
- Invariants:
  - no conflict with existing `CLAUDE.md` hierarchy;
  - no behavior change in runtime product code.

## Acceptance Criteria

- Functional:
  - repository contains a root `AGENTS.md` with execution rules.
  - repository contains an `agents/` bootstrap note.
  - repository contains layer-specific override rules for `frontend` and `api`.
  - repository contains Codex project config baseline under `.codex/config.toml`.
- Technical:
  - guidance includes microstep loop, quality gates, and doc sync policy.
  - guidance references privacy/security/accounting criticality.

## Test Plan

- Manual:
  - verify `AGENTS.md` exists in repository root.
  - verify `agents/README.md` exists.
  - verify `frontend/AGENTS.override.md` and `api/AGENTS.override.md` exist.
  - verify `.codex/config.toml` exists and includes MCP server entry.
  - verify docs upgrade log includes the new entry.

## Risks and Mitigation

- Risk 1: duplicated/conflicting process rules across docs.
- Mitigation 1: explicit priority section in `AGENTS.md`.

## Rollback Plan

- Revert the governance commit if it creates confusion.
- Keep previous process files (`CLAUDE.md`, `codex.md`) as fallback truth.

## Notes

- This upgrade prepares the foundation for next microstep:
  layer-specific overrides and MCP-ready workflows.
