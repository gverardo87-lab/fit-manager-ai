---
name: fitmanager-microstep-delivery
description: Use when implementing non-trivial changes in FitManager. Enforces impact map, microstep execution, targeted verification, and explicit bug/risk surfacing before handoff.
---

# FitManager Microstep Delivery

## When To Use

Use this skill when the task is more than a one-line fix and may cause regressions.
Typical triggers:

- page/process hardening requests
- bugfix + refactor combinations
- changes touching API and frontend together
- any request asking for "microstep" execution

## Workflow

1. Build an impact map:
   - objective
   - touched files/layers
   - invariants to preserve
2. Implement one smallest useful step.
3. Run targeted verification for touched scope.
4. Run a bug/risk scan:
   - regressions
   - stale state/cache
   - privacy/security leak
   - architectural coupling risk
5. Report outcome and move to next microstep.

## Verification Matrix

- Frontend change:
  - lint touched files
  - verify loading/error/empty states
- API change:
  - run relevant tests subset
  - verify ownership and transaction invariants
- Docs/process change:
  - verify upgrade log + spec + workboard consistency

## Handoff Contract

Each microstep handoff must include:

- what changed
- verification executed
- residual risks
- next smallest step
