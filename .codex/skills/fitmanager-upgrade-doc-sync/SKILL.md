---
name: fitmanager-upgrade-doc-sync
description: Use after FitManager changes to keep specs, upgrade log, and AI workboard aligned. Ensures governance docs stay accurate and release-ready.
---

# FitManager Upgrade Doc Sync

## When To Use

Use this skill when a patch changes behavior, architecture, process, or delivery workflow.

## Required Updates

1. `docs/upgrades/specs/<UPG-ID>.md`
2. `docs/upgrades/UPGRADE_LOG.md`
3. `docs/upgrades/README.md` (latest alignment section when relevant)
4. `docs/ai-sync/WORKBOARD.md` for active/completed tracking when relevant

## Workflow

1. Determine whether patch is:
   - small: log only
   - medium/high: spec + log (+ workboard if collaborative scope)
2. Add or update UPG row with:
   - area/type/impact/risk
   - branch + commit(s)
   - status (`planned`, `in_progress`, `done`)
3. Ensure spec and log refer to each other consistently.
4. Before handoff, verify file paths and commit ids are accurate.

## Done Criteria

- no stale `_pending_` markers after final commit
- UPG ID is unique and chronologically coherent
- workboard entries contain scope and checks actually performed
