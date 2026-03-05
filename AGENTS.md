# AGENTS.md - FitManager AI Studio

This file defines how coding agents must work in this repository.
Goal: maximize delivery speed without sacrificing reliability, privacy, and product quality.

## 1) Mission

Build a production-grade CRM for small and medium businesses and professionals.
Every change must improve at least one of these pillars:

- operational speed
- data reliability
- user trust and privacy
- maintainability and testability

## 2) Rule Priority

When instructions conflict, follow this order:

1. System/developer/runtime constraints
2. This file (`AGENTS.md`)
3. `CLAUDE.md` (root + layer-specific files)
4. `codex.md`
5. `docs/ai-sync/MULTI_AGENT_SYNC.md`
6. Other documentation

Always choose the stricter safety/quality rule.

## 3) Execution Model (Microstep-First)

Use this loop on every task:

1. Clarify scope and constraints in one short impact map.
2. Implement one microstep at a time.
3. Run targeted verification immediately after each microstep.
4. Report:
   - what changed
   - what was verified
   - bugs/technical gaps/architectural risks found

Do not hide risks. Surface them early and explicitly.

## 4) Non-Negotiable Product Principles

- Privacy-first on client-visible views.
- Financial data is sensitive: keep it in dedicated finance contexts.
- Multi-tenant safety: never bypass ownership checks.
- Auditability for critical operations.
- Deterministic behavior over "magic" behavior in business-critical flows.

## 5) Engineering Guardrails

### Backend

- Preserve Bouncer Pattern and Deep Relational IDOR checks.
- Prevent mass assignment.
- Keep multi-entity operations atomic.
- Keep audit logs coherent for critical state transitions.

### Frontend

- Keep API type sync with `frontend/src/types/api.ts`.
- Keep query invalidation symmetric across opposite operations.
- Handle loading/error/empty states explicitly.
- Avoid exposing sensitive data in default overview screens.
- For dashboard visual redesigns, apply `.codex/skills/fitmanager-dashboard-crm-design` guidance.

### Cross-layer

- No hardcoded absolute paths.
- Persist business data in `data/`.
- Keep core CRM usable without mandatory AI dependency.

## 6) Mandatory Technical Review per Change

For every implemented microstep, quickly scan for:

- regressions
- hidden coupling
- stale query state risks
- data consistency gaps
- security/privacy leaks
- architectural debt that can break scale

If found, document them and propose the next smallest corrective step.

## 7) Quality Gates

Baseline:

- run relevant lint/tests for touched scope

When relevant:

- DB/schema changes: migration + backend tests
- accounting/cash logic: targeted ledger integrity checks
- safety engine logic: dedicated clinical QA scripts
- installer/backup changes: backup -> mutate -> restore validation flow

Do not claim done without verification evidence.

## 8) Documentation Sync Policy

When behavior changes, update in the same branch:

- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md` (if latest alignment changes)
- spec in `docs/upgrades/specs/` for medium/high-impact changes
- `docs/ai-sync/WORKBOARD.md` when applicable

Docs are part of the deliverable, not optional cleanup.

## 9) MCP and External Knowledge

If MCP servers are configured:

- prefer primary/official sources
- use MCP for fast verification of evolving external APIs
- avoid relying on stale memory for time-sensitive facts

If MCP is unavailable, use local docs and state uncertainty clearly.

## 10) Commit Standard

Commit only cohesive, verified units.
Commit message format should be domain-first and explicit, for example:

- `dashboard: ...`
- `api: ...`
- `docs: ...`
- `installer: ...`

Each commit should leave the branch in a releasable state for its scope.
