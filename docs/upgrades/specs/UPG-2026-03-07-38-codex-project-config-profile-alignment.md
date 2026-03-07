# UPG-2026-03-07-38 - Codex Project Config Profile Alignment

## Metadata

- Upgrade ID: UPG-2026-03-07-38
- Date: 2026-03-07
- Owner: Codex
- Area: Governance + AI Workflow
- Priority: medium
- Target release: codex_02

## Problem

The repository-level `.codex/config.toml` was still pinned to `gpt-5.2-codex` and only defined
minimal execution settings. This created drift versus the updated user setup in `~/.codex/config.toml`
and forced FitManager sessions to run with an older project baseline than intended.

## Desired Outcome

Align the project-level Codex baseline with the current setup so FitManager sessions default to the
same model quality and execution posture, while keeping machine-specific preferences out of versioned
project config.

## Scope

- In scope:
  - update `.codex/config.toml` with explicit model/reasoning/verbosity defaults;
  - add CLI profiles `quick`, `deep`, and `safe`;
  - keep OpenAI docs MCP entry and project doc fallback rules;
  - sync upgrade/governance docs.
- Out of scope:
  - editing the user-global `~/.codex/config.toml`;
  - adding machine-local settings such as keyring/file opener/history policy to repo config.

## Impact Map

- Files/modules touched:
  - `.codex/config.toml`
  - `docs/upgrades/specs/UPG-2026-03-07-38-codex-project-config-profile-alignment.md`
  - `docs/upgrades/UPGRADE_LOG.md`
  - `docs/upgrades/README.md`
  - `docs/ai-sync/WORKBOARD.md`
- Layer coinvolti: `tools`
- Invarianti da preservare:
  - repo config must stay portable across collaborators and machines;
  - IDE/editor integrations must remain usable without relying on profiles;
  - no runtime CRM behavior must change.

## Acceptance Criteria

- Funzionale:
  - FitManager project sessions default to `gpt-5.4` with explicit reasoning/verbosity settings.
  - CLI users can opt into `quick`, `deep`, and `safe` profiles from repo config.
- UX:
  - top-level project config remains concise and understandable for collaborators.
- Tecnico:
  - `.codex/config.toml` parses successfully with default config and all three profiles.
  - no machine-specific secrets or local-environment preferences are committed.

## Test Plan

- Manual checks:
  - run `codex --help` from repo root to validate base config parsing;
  - run `codex -p quick --help`;
  - run `codex -p deep --help`;
  - run `codex -p safe --help`.
- Build/Lint gates:
  - not applicable; patch is governance/config only.

## Risks and Mitigation

- Risk 1: profiles are ignored by some IDE integrations.
- Mitigation 1: keep the top-level config fully usable without any profile selection.

- Risk 2: future global setup changes may diverge again from project defaults.
- Mitigation 2: keep repo config limited to project-relevant defaults, so future re-alignment is small and explicit.

## Rollback Plan

- Revert this patch to restore the previous minimal `.codex/config.toml`.
- If profile behavior becomes confusing, keep only the updated top-level model and remove profile blocks.

## Notes

- This patch intentionally keeps personal settings in `~/.codex/config.toml` and project-safe defaults in `.codex/config.toml`.
