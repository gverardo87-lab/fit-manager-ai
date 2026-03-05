# UPG-2026-03-05-17 - Guide Interactive Layer and Assistant Linking

## Metadata

- Upgrade ID: UPG-2026-03-05-17
- Date: 2026-03-05
- Owner: Codex
- Area: Guide + Assistant
- Priority: high
- Target release: codex_02

## Problem

Users still need contextual, real-time support while working.
Current assistant capabilities are deterministic but limited in intent coverage and not linked to
a full guide retrieval layer.

## Desired Outcome

Introduce interactive in-app guidance and safe assistant-guide integration:

- contextual step-by-step tours;
- read-only guide answers for help intents;
- controlled parse/commit for command intents.

## Scope

- In scope:
  - interactive guide entry points and progress tracking;
  - assistant request routing (`guide` vs `command`);
  - fallback from low-confidence parse to relevant guide chapter;
  - telemetry for guide usage and fallback quality.
- Out of scope:
  - free-form autonomous write actions without explicit confirmation;
  - broad non-deterministic LLM actions in critical CRM flows.

## Impact Map

- Planned files/modules:
  - `frontend/src/components/layout/CommandPalette.tsx`
  - `frontend/src/hooks/useAssistant.ts`
  - new guide state/hooks under `frontend/src/hooks/` and `frontend/src/lib/`
  - `api/routers/assistant.py`
  - `api/schemas/assistant.py`
  - `api/services/assistant_parser/*` (routing and fallback extensions)
  - tests for assistant-guide routing and safety
- Layer: frontend + api + tests
- Invariants:
  - no side effects in guide/help mode;
  - ownership and IDOR protections preserved;
  - explicit confirmation remains mandatory for writes.

## Acceptance Criteria

- help intents return concise answer + guide reference + next action link;
- command intents preserve existing parse/preview/commit contract;
- ambiguity and low confidence paths remain read-only;
- tests cover routing split and negative paths.

## Test Plan

- Backend:
  - pytest subset for assistant parse/commit and security guards.
- Frontend:
  - lint touched files;
  - manual command palette keyboard flow validation;
  - responsive pass for guide overlays/help panels.

## Risks and Mitigation

- Risk: accidental command execution from help prompts.
- Mitigation: strict intent split with explicit read-only default when uncertain.

- Risk: command palette complexity growth.
- Mitigation: modularize assistant/help logic into dedicated utilities/hooks.

## Rollback Plan

- feature-flag assistant-guide routing;
- revert guide-interactive integration files while preserving chaptered docs.

