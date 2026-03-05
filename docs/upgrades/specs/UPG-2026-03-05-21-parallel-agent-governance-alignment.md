# UPG-2026-03-05-21 - Parallel Agent Governance Alignment (Codex + Claude Code)

## Metadata

- Upgrade ID: UPG-2026-03-05-21
- Date: 2026-03-05
- Owner: Codex
- Area: Governance + Documentation
- Priority: medium
- Target release: codex_02

## Problem

Parallel development with Codex and Claude Code is active, but governance instructions were split
across multiple docs with partial overlap and drift:

- `codex.md` rule priority was not aligned with `AGENTS.md`;
- multi-agent protocol lacked a strict workboard contract schema;
- layer-specific `CLAUDE.md` files did not explicitly state lock/handoff expectations.

This increases risk of conflicting edits, unclear ownership, and slower handoffs.

## Desired Outcome

Provide one consistent operating contract for multi-agent collaboration:

- align `codex.md` and root `CLAUDE.md` with `AGENTS.md` precedence;
- harden `docs/ai-sync/MULTI_AGENT_SYNC.md` with start/during/end lifecycle and lock policy;
- standardize `WORKBOARD.md` active-task schema;
- add parallel-collaboration reminders in `api/CLAUDE.md`, `frontend/CLAUDE.md`, `core/CLAUDE.md`.

## Scope

- In scope:
  - `codex.md`
  - `CLAUDE.md`
  - `api/CLAUDE.md`
  - `frontend/CLAUDE.md`
  - `core/CLAUDE.md`
  - `docs/ai-sync/MULTI_AGENT_SYNC.md`
  - `docs/ai-sync/WORKBOARD.md`
  - upgrade tracking docs (`UPGRADE_LOG`, `README`, `WORKBOARD`)
- Out of scope:
  - runtime frontend/backend behavior changes;
  - CI workflow changes;
  - branch strategy automation.

## Acceptance Criteria

- `codex.md` source-of-truth hierarchy matches `AGENTS.md`.
- Root + layer `CLAUDE.md` files include explicit parallel lock/handoff rules.
- `MULTI_AGENT_SYNC.md` includes:
  - priority order;
  - workboard field contract;
  - lifecycle (start/during/end);
  - blocked/conflict handling.
- `WORKBOARD.md` has explicit `Active` table schema with lock and handoff columns.
- Upgrade tracking docs are synchronized.

## Test Plan

- Manual doc review:
  - verify consistency of terms: `Work ID`, `Locked files`, `blocked`, `handoff`;
  - verify no contradiction between `AGENTS.md`, `CLAUDE.md`, `codex.md`, `MULTI_AGENT_SYNC.md`.
- Validation checks:
  - `rg -n "Coordinamento parallelo layer|Locked files|Work ID" CLAUDE.md codex.md api/CLAUDE.md frontend/CLAUDE.md core/CLAUDE.md docs/ai-sync/MULTI_AGENT_SYNC.md docs/ai-sync/WORKBOARD.md`

## Risks and Mitigation

- Risk: higher process overhead for small patches.
- Mitigation: keep protocol lightweight (single-row claim + concise handoff packet).

- Risk: drift between governance docs over time.
- Mitigation: treat governance updates as tracked upgrades with explicit UPG entry.

## Rollback Plan

- Revert this governance-only patch and restore previous docs if the new process creates blockers.
- Keep `AGENTS.md` as stable reference for minimum non-negotiable constraints.
